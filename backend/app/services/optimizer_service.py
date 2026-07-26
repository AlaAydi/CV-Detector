import re
from dataclasses import dataclass, field

from app.services.nlp_service import detect_skills


SECTION_HEADERS = {
    "summary": ["summary", "profil", "profile", "à propos", "about", "resume"],
    "skills": ["skills", "compétences", "competences", "technical skills", "technologies"],
    "experience": ["experience", "expérience", "work experience", "employment", "professional experience"],
    "education": ["education", "formation", "studies", "diplômes", "diplomes"],
    "projects": ["projects", "projets", "portfolio"],
}


@dataclass
class ResumeSection:
    key: str
    title: str | None
    lines: list[str]
    highlight_tokens: frozenset[str] = field(default_factory=frozenset)


def _match_section_key(line: str) -> str | None:
    lower = line.lower()
    for section, keywords in SECTION_HEADERS.items():
        if any(re.fullmatch(rf"{kw}.*", lower) or lower == kw for kw in keywords):
            return section
    return None


def parse_sections_ordered(text: str) -> list[ResumeSection]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return [ResumeSection("header", None, [])]

    sections: list[ResumeSection] = []
    current_key = "header"
    current_title: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_title, current_lines
        if current_title is not None or current_lines or (current_key == "header" and sections == []):
            sections.append(ResumeSection(current_key, current_title, current_lines))
        current_lines = []

    for line in lines:
        matched_key = _match_section_key(line)
        if matched_key:
            flush()
            current_key = matched_key
            current_title = line
            current_lines = []
        else:
            current_lines.append(line)

    flush()
    return sections


def get_ordered_skills(resume_text: str, job_text: str) -> list[str]:
    resume_skills = detect_skills(resume_text)
    job_skills = detect_skills(job_text)
    prioritized_skills = [skill for skill in job_skills if skill in resume_skills]
    remaining_skills = [skill for skill in resume_skills if skill not in prioritized_skills]
    return prioritized_skills + remaining_skills


def _skills_in_section_lines(lines: list[str]) -> set[str]:
    if not lines:
        return set()
    section_text = " ".join(lines)
    return set(detect_skills(section_text))


def _promoted_skills(resume_text: str, job_text: str, skills_lines: list[str]) -> set[str]:
    """Skills present elsewhere in the CV and required by the job, but absent from the skills section."""
    section_skills = _skills_in_section_lines(skills_lines)
    resume_skills = set(detect_skills(resume_text))
    job_skills = set(detect_skills(job_text))
    return {skill for skill in resume_skills & job_skills if skill not in section_skills}


def _line_skill_priority(line: str, ordered_skills: list[str]) -> int:
    line_lower = line.lower()
    for index, skill in enumerate(ordered_skills):
        if skill in line_lower:
            return index
    return len(ordered_skills) + 1


def _token_display_name(skill: str, resume_text: str) -> str:
    """Return the exact spelling found in the CV, without inventing new wording."""
    pattern = re.compile(re.escape(skill), re.IGNORECASE)
    match = pattern.search(resume_text)
    if match:
        return match.group(0)
    return skill


def _reorder_inline_skills(line: str, ordered_skills: list[str], promoted: set[str], resume_text: str) -> str:
    separator = ", " if "," in line else "; "
    parts = [part.strip() for part in re.split(r"[,;]", line) if part.strip()]

    existing_lower = {part.lower() for part in parts}
    for skill in ordered_skills:
        if skill in promoted:
            display = _token_display_name(skill, resume_text)
            if display.lower() not in existing_lower:
                parts.insert(0, display)
                existing_lower.add(display.lower())

    if len(parts) <= 1:
        return parts[0] if parts else line

    sorted_parts = sorted(parts, key=lambda part: _line_skill_priority(part, ordered_skills))
    return separator.join(sorted_parts)


def _optimize_skills_lines(
    lines: list[str],
    ordered_skills: list[str],
    promoted: set[str],
    resume_text: str,
) -> list[str]:
    if not lines:
        if promoted:
            display = [_token_display_name(skill, resume_text) for skill in ordered_skills if skill in promoted]
            return [", ".join(display)] if display else lines
        return lines

    if len(lines) == 1 and ("," in lines[0] or ";" in lines[0]):
        return [_reorder_inline_skills(lines[0], ordered_skills, promoted, resume_text)]

    result = sorted(lines, key=lambda line: _line_skill_priority(line, ordered_skills))
    existing_lower = {line.lower() for line in result}
    for skill in ordered_skills:
        if skill not in promoted:
            continue
        display = _token_display_name(skill, resume_text)
        if display.lower() not in existing_lower:
            result.insert(0, display)
            existing_lower.add(display.lower())
    return result


def optimize_sections(resume_text: str, job_text: str) -> list[ResumeSection]:
    sections = parse_sections_ordered(resume_text)
    ordered_skills = get_ordered_skills(resume_text, job_text)

    optimized: list[ResumeSection] = []
    for section in sections:
        if section.key == "skills" and section.lines:
            promoted = _promoted_skills(resume_text, job_text, section.lines)
            new_lines = _optimize_skills_lines(section.lines, ordered_skills, promoted, resume_text)
            highlight = frozenset(
                _token_display_name(skill, resume_text).lower() for skill in promoted
            )
            optimized.append(
                ResumeSection(section.key, section.title, new_lines, highlight),
            )
        else:
            optimized.append(
                ResumeSection(section.key, section.title, section.lines[:]),
            )
    return optimized


def sections_to_text(sections: list[ResumeSection]) -> str:
    parts: list[str] = []
    for section in sections:
        block: list[str] = []
        if section.key == "header":
            block.extend(section.lines)
        else:
            if section.title:
                block.append(section.title)
            for line in section.lines:
                if section.highlight_tokens and section.key == "skills":
                    block.append(_format_line_with_highlights(line, section.highlight_tokens))
                else:
                    block.append(line)
        if block:
            parts.append("\n".join(block))
    return "\n\n".join(parts).strip()


def _format_line_with_highlights(line: str, highlight_tokens: frozenset[str]) -> str:
    if "," in line or ";" in line:
        separator = ", " if "," in line else "; "
        parts = [part.strip() for part in re.split(r"[,;]", line) if part.strip()]
        formatted = []
        for part in parts:
            if any(token in part.lower() for token in highlight_tokens):
                formatted.append(f"**{part}**")
            else:
                formatted.append(part)
        return separator.join(formatted)

    if any(token in line.lower() for token in highlight_tokens):
        return f"**{line}**"
    return line


def optimize_resume(resume_text: str, job_text: str) -> str:
    optimized = sections_to_text(optimize_sections(resume_text, job_text))
    return optimized.strip() or resume_text


def sections_have_changes(sections: list[ResumeSection]) -> bool:
    return any(
        section.key == "skills" and (section.lines or section.highlight_tokens)
        for section in sections
    )
