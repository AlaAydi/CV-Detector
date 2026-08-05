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

    current_score = scores.get("score", 0)
    recommendations.append(
        f"🎯 Plan d'action ATS > 95% (Score actuel : {current_score}%) : Suivez ces étapes clés pour maximiser la compatibilité de votre CV."
    )

    if missing:
        top_missing = missing[:8]
        recommendations.append(
            f"💡 Compétences prioritaires à ajouter : Intégrez ou mettez en valeur ces compétences requises dans votre section Compétences ainsi que dans le descriptif de vos projets ou expériences : {', '.join(top_missing)}."
        )

    if scores.get("score_keywords", 0) < 95:
        recommendations.append(
            "🔑 Alignement des mots-clés : Harmonisez l'intitulé de votre profil (ex: Développeur Full-Stack Angular / Spring Boot) et le vocabulaire technique avec la description exacte de l'offre."
        )

    recommendations.append(
        "📈 Chiffrage des résultats & verbes d'action : Ajoutez des métriques quantifiables dans vos expériences (ex: 'Optimisation des temps de réponse de 35%', 'Équipe de 4 développeurs', 'Gestion de 10k+ utilisateurs') et commencez vos puces par des verbes d'action forts (Conception, Développement, Optimisation)."
    )

    if matched:
        recommendations.append(
            f"✅ Compétences déjà alignées avec l'offre : {', '.join(matched[:10])}."
        )

    recommendations.append(
        "📄 Structure & lisibilité ATS : Utilisez des intitulés de rubrique standardisés (RÉSUMÉ, EXPÉRIENCE, ÉDUCATION, COMPÉTENCES, PROJETS, LANGUES) et téléchargez le CV optimisé ci-dessous pour conserver un layout 2 colonnes clair sans texte masqué."
    )

    return recommendations
