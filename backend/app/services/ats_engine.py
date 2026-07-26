from app.services.nlp_service import (
    detect_skills,
    education_score,
    experience_score,
    keyword_similarity,
)


def compute_skills_match(resume_text: str, job_text: str) -> tuple[list[str], list[str], float]:
    resume_skills = set(detect_skills(resume_text))
    job_skills = set(detect_skills(job_text))

    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    if not job_skills:
        score = 1.0 if resume_skills else 0.5
    else:
        score = len(matched) / len(job_skills)

    return matched, missing, score


def compute_ats_score(resume_text: str, job_text: str) -> dict:
    matched, missing, skills_ratio = compute_skills_match(resume_text, job_text)
    keywords_ratio = keyword_similarity(resume_text, job_text)
    exp_ratio = experience_score(resume_text, job_text)
    edu_ratio = education_score(resume_text, job_text)

    score_skills = round(skills_ratio * 100)
    score_keywords = round(keywords_ratio * 100)
    score_experience = round(exp_ratio * 100)
    score_education = round(edu_ratio * 100)

    global_score = round(
        0.40 * score_skills
        + 0.30 * score_keywords
        + 0.20 * score_experience
        + 0.10 * score_education
    )

    return {
        "score": global_score,
        "score_skills": score_skills,
        "score_keywords": score_keywords,
        "score_experience": score_experience,
        "score_education": score_education,
        "matched_skills": matched,
        "missing_skills": missing,
    }


def compatibility_level(score: int) -> str:
    if score >= 80:
        return "excellent"
    if score >= 65:
        return "good"
    if score >= 45:
        return "moderate"
    return "low"


def build_recommendations(matched: list[str], missing: list[str], scores: dict) -> list[str]:
    recommendations: list[str] = []

    if missing:
        top_missing = missing[:8]
        recommendations.append(
            "Ajoutez ou mettez en avant ces compétences déjà présentes dans votre parcours : "
            + ", ".join(top_missing)
            + "."
        )

    if scores["score_keywords"] < 60:
        recommendations.append(
            "Reformulez votre résumé et vos expériences avec les mots-clés exacts de l'offre, "
            "sans inventer de nouvelles informations."
        )

    if scores["score_experience"] < 50:
        recommendations.append(
            "Détaillez vos années d'expérience et vos responsabilités en lien avec le poste visé."
        )

    if scores["score_education"] < 50:
        recommendations.append(
            "Mettez en avant vos diplômes, certifications ou formations pertinentes pour ce poste."
        )

    if matched:
        recommendations.append(
            "Compétences déjà alignées avec l'offre : " + ", ".join(matched[:10]) + "."
        )

    if not recommendations:
        recommendations.append("Votre CV est déjà bien aligné avec cette offre.")

    return recommendations
