import re
from dataclasses import dataclass, field

from app.services.nlp_service import detect_education_terms, detect_languages, detect_skills


SECTION_HEADERS = {
    "summary": ["summary", "profil", "profile", "à propos", "about", "resume"],
    "skills": ["skills", "compétences", "competences", "technical skills", "technologies"],
    "experience": ["experience", "expérience", "work experience", "employment", "professional experience"],
    "education": ["education", "formation", "studies", "diplômes", "diplomes"],
    "projects": ["projects", "projets", "portfolio"],
    "languages": ["languages", "langues", "language"],
}

# Which detector extracts "keywords" for each section, and how additions are
# inserted once a keyword is confirmed to be already true (present elsewhere
# in the CV) and required by the job, but missing from that section.
#   - "list": list/enumeration-style sections (skills, languages, education) ->
#     the missing item is inserted as its own line/entry.
#   - "append_line": narrative/bullet sections (experience, projects) -> the
#     missing keyword is appended to the end of the last existing bullet,
#     i.e. a real rewrite of that line, instead of inventing a new bullet.
SECTION_KEYWORD_CONFIG: dict[str, tuple] = {
    "skills": (detect_skills, "list"),
    "languages": (detect_languages, "list"),
    "education": (detect_education_terms, "list"),
    "experience": (detect_skills, "append_line"),
    "projects": (detect_skills, "append_line"),
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


def _ordered_keywords(resume_text: str, job_text: str, detector) -> list[str]:
    resume_keywords = detector(resume_text)
    job_keywords = detector(job_text)
    prioritized = [keyword for keyword in job_keywords if keyword in resume_keywords]
    remaining = [keyword for keyword in resume_keywords if keyword not in prioritized]
    return prioritized + remaining


def get_ordered_skills(resume_text: str, job_text: str) -> list[str]:
    return _ordered_keywords(resume_text, job_text, detect_skills)


def _keywords_in_section_lines(lines: list[str], detector) -> set[str]:
    if not lines:
        return set()
    section_text = " ".join(lines)
    return set(detector(section_text))


def _promoted_keywords(resume_text: str, job_text: str, section_lines: list[str], detector) -> set[str]:
    """Keywords already true (present elsewhere in the CV) and required by the job,
    but absent from this specific section. Never introduces anything that isn't
    already demonstrably in the CV, so no information is invented."""
    section_keywords = _keywords_in_section_lines(section_lines, detector)
    resume_keywords = set(detector(resume_text))
    job_keywords = set(detector(job_text))
    return {keyword for keyword in resume_keywords & job_keywords if keyword not in section_keywords}


def _line_keyword_priority(line: str, ordered_keywords: list[str]) -> int:
    line_lower = line.lower()
    for index, keyword in enumerate(ordered_keywords):
        if keyword in line_lower:
            return index
    return len(ordered_keywords) + 1


def _token_display_name(skill: str, resume_text: str) -> str:
    """Return the exact spelling found in the CV, without inventing new wording."""
    pattern = re.compile(re.escape(skill), re.IGNORECASE)
    match = pattern.search(resume_text)
    if match:
        return match.group(0)
    return skill


def _reorder_inline_keywords(line: str, ordered_keywords: list[str], promoted: set[str], resume_text: str) -> str:
    separator = ", " if "," in line else "; "
    parts = [part.strip() for part in re.split(r"[,;]", line) if part.strip()]

    existing_lower = {part.lower() for part in parts}
    for keyword in ordered_keywords:
        if keyword in promoted:
            display = _token_display_name(keyword, resume_text)
            if display.lower() not in existing_lower:
                parts.insert(0, display)
                existing_lower.add(display.lower())

    if len(parts) <= 1:
        return parts[0] if parts else line

    sorted_parts = sorted(parts, key=lambda part: _line_keyword_priority(part, ordered_keywords))
    return separator.join(sorted_parts)


def _optimize_list_lines(
    lines: list[str],
    ordered_keywords: list[str],
    promoted: set[str],
    resume_text: str,
) -> list[str]:
    """Reorder/insert for enumeration-style sections (skills, languages, education)."""
    if not lines:
        if promoted:
            display = [_token_display_name(keyword, resume_text) for keyword in ordered_keywords if keyword in promoted]
            return [", ".join(display)] if display else lines
        return lines

    if len(lines) == 1 and ("," in lines[0] or ";" in lines[0]):
        return [_reorder_inline_keywords(lines[0], ordered_keywords, promoted, resume_text)]

    result = sorted(lines, key=lambda line: _line_keyword_priority(line, ordered_keywords))
    existing_lower = {line.lower() for line in result}
    for keyword in ordered_keywords:
        if keyword not in promoted:
            continue
        display = _token_display_name(keyword, resume_text)
        if display.lower() not in existing_lower:
            result.insert(0, display)
            existing_lower.add(display.lower())
    return result


def _extend_last_line_with_missing(
    lines: list[str],
    ordered_keywords: list[str],
    promoted: set[str],
    resume_text: str,
) -> list[str]:
    """Rewrite the last bullet of a narrative section (experience, projects) to
    fold in already-true keywords it doesn't mention yet, instead of inventing
    a disconnected new bullet."""
    if not lines or not promoted:
        return lines

    display = [_token_display_name(keyword, resume_text) for keyword in ordered_keywords if keyword in promoted]
    if not display:
        return lines

    result = lines[:]
    last = result[-1].rstrip()
    if last and last[-1] not in ".!?":
        connector = ", " if ("," in last or ":" in last) else " – "
    else:
        connector = " – "
        last = last.rstrip(".!? ")
    result[-1] = f"{last}{connector}{', '.join(display)}"
    return result


def optimize_sections(resume_text: str, job_text: str) -> list[ResumeSection]:
    sections = parse_sections_ordered(resume_text)

    optimized: list[ResumeSection] = []
    for section in sections:
        config = SECTION_KEYWORD_CONFIG.get(section.key)
        if config and section.lines:
            detector, strategy = config
            ordered_keywords = _ordered_keywords(resume_text, job_text, detector)
            promoted = _promoted_keywords(resume_text, job_text, section.lines, detector)

            if strategy == "append_line":
                new_lines = _extend_last_line_with_missing(section.lines, ordered_keywords, promoted, resume_text)
            else:
                new_lines = _optimize_list_lines(section.lines, ordered_keywords, promoted, resume_text)

            highlight = frozenset(
                _token_display_name(keyword, resume_text).lower() for keyword in promoted
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
                if section.highlight_tokens:
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
    return any(section.highlight_tokens for section in sections)