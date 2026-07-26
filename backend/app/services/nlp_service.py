import json
import re
from functools import lru_cache
from pathlib import Path

from app.services.text_similarity import cosine_similarity_text


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "skills_synonyms.json"

EXPERIENCE_PATTERNS = [
    r"\b(\d+)\+?\s*(?:years?|ans?|yr)\b",
    r"\b(?:senior|junior|mid[- ]level|lead|principal)\b",
    r"\b(?:internship|stage|stagiaire)\b",
]

EDUCATION_PATTERNS = [
    r"\b(?:bachelor|master|phd|doctorate|licence|master(?:\s+)?(?:\s+)?(?:\s+)?|mba|bts|dut|engineering degree)\b",
    r"\b(?:university|universit[eé]|ecole|school|institut)\b",
    r"\b(?:certification|certified|certificate|dipl[oô]me)\b",
]

# Fixed vocabulary (no external file needed) so spoken languages can be
# matched the same way as technical skills: canonical -> known aliases.
LANGUAGE_SYNONYMS: dict[str, list[str]] = {
    "français": ["français", "francais", "french"],
    "anglais": ["anglais", "english"],
    "espagnol": ["espagnol", "spanish", "español"],
    "allemand": ["allemand", "german", "deutsch"],
    "italien": ["italien", "italian", "italiano"],
    "arabe": ["arabe", "arabic"],
    "chinois": ["chinois", "chinese", "mandarin"],
    "portugais": ["portugais", "portuguese"],
    "russe": ["russe", "russian"],
    "néerlandais": ["néerlandais", "neerlandais", "dutch"],
}


@lru_cache
def load_synonyms() -> dict[str, list[str]]:
    with open(DATA_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    normalized: dict[str, list[str]] = {}
    for skill, aliases in raw.items():
        key = skill.lower().strip()
        normalized[key] = [key] + [a.lower().strip() for a in aliases]
    return normalized


def normalize_skill(skill: str) -> str:
    skill = skill.lower().strip()
    synonyms = load_synonyms()
    for canonical, aliases in synonyms.items():
        if skill in aliases:
            return canonical
    return skill


def _build_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical, aliases in load_synonyms().items():
        for alias in aliases:
            index[alias] = canonical
    return index


def detect_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found: set[str] = set()
    alias_index = _build_alias_index()

    for alias, canonical in sorted(alias_index.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, text_lower):
            found.add(canonical)

    return sorted(found)


def detect_languages(text: str) -> list[str]:
    text_lower = text.lower()
    found: set[str] = set()
    for canonical, aliases in LANGUAGE_SYNONYMS.items():
        for alias in aliases:
            if re.search(r"\b" + re.escape(alias) + r"\b", text_lower):
                found.add(canonical)
                break
    return sorted(found)


def detect_education_terms(text: str) -> list[str]:
    """Extract education/degree/certification terms literally present in the text.

    Unlike detect_skills (fixed canonical vocabulary), education wording varies too
    much to normalize safely, so we return the matched substrings themselves.
    """
    text_lower = text.lower()
    found: set[str] = set()
    for pattern in EDUCATION_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            term = re.sub(r"\s+", " ", match.group(0)).strip()
            if term:
                found.add(term)
    return sorted(found)


def keyword_similarity(resume_text: str, job_text: str) -> float:
    return cosine_similarity_text(resume_text, job_text)


def pattern_score(text: str, patterns: list[str]) -> float:
    text_lower = text.lower()
    matches = sum(1 for pattern in patterns if re.search(pattern, text_lower, re.IGNORECASE))
    return min(1.0, matches / max(len(patterns), 1))


def experience_score(resume_text: str, job_text: str) -> float:
    resume_hits = pattern_score(resume_text, EXPERIENCE_PATTERNS)
    job_hits = pattern_score(job_text, EXPERIENCE_PATTERNS)
    if job_hits == 0:
        return resume_hits
    return min(1.0, resume_hits / job_hits) if resume_hits else 0.0


def education_score(resume_text: str, job_text: str) -> float:
    resume_hits = pattern_score(resume_text, EDUCATION_PATTERNS)
    job_hits = pattern_score(job_text, EDUCATION_PATTERNS)
    if job_hits == 0:
        return resume_hits if resume_hits else 0.5
    return min(1.0, resume_hits / job_hits) if resume_hits else 0.0