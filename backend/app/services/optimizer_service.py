import re

from app.services.nlp_service import detect_skills


SECTION_HEADERS = {
    "summary": ["summary", "profil", "profile", "à propos", "about", "resume"],
    "skills": ["skills", "compétences", "competences", "technical skills", "technologies"],
    "experience": ["experience", "expérience", "work experience", "employment", "professional experience"],
    "education": ["education", "formation", "studies", "diplômes", "diplomes"],
    "projects": ["projects", "projets", "portfolio"],
}


def _split_sections(text: str) -> dict[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections: dict[str, list[str]] = {
        "header": [],
        "summary": [],
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "other": [],
    }

    current = "header"
    for line in lines:
        lower = line.lower()
        matched = False
        for section, keywords in SECTION_HEADERS.items():
            if any(re.fullmatch(rf"{kw}.*", lower) or lower == kw for kw in keywords):
                current = section
                matched = True
                break
        if not matched:
            sections[current].append(line)

    return {key: "\n".join(value).strip() for key, value in sections.items() if value}


def optimize_resume(resume_text: str, job_text: str) -> str:
    sections = _split_sections(resume_text)
    resume_skills = detect_skills(resume_text)
    job_skills = detect_skills(job_text)
    prioritized_skills = [skill for skill in job_skills if skill in resume_skills]
    remaining_skills = [skill for skill in resume_skills if skill not in prioritized_skills]
    ordered_skills = prioritized_skills + remaining_skills

    parts: list[str] = []

    header = sections.get("header", "")
    if header:
        parts.append(header)

    summary = sections.get("summary", "")
    if summary:
        parts.append("PROFIL PROFESSIONNEL\n" + summary)

    if ordered_skills:
        skills_block = sections.get("skills", "")
        skill_lines = [f"- {skill.title()}" for skill in ordered_skills]
        if skills_block:
            parts.append("COMPÉTENCES\n" + skills_block + "\n" + "\n".join(skill_lines))
        else:
            parts.append("COMPÉTENCES\n" + "\n".join(skill_lines))

    for section_name, title in [
        ("experience", "EXPÉRIENCE"),
        ("projects", "PROJETS"),
        ("education", "FORMATION"),
    ]:
        content = sections.get(section_name, "")
        if content:
            parts.append(f"{title}\n{content}")

    other = sections.get("other", "")
    if other:
        parts.append(other)

    optimized = "\n\n".join(part for part in parts if part.strip())
    return optimized.strip() or resume_text
