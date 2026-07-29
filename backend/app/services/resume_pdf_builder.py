
"""
Générateur de CV optimisé en PDF — reconstruction complète (pas d'édition
pixel par pixel du fichier original).

Remplace l'approche fragile de `_apply_sections_to_pdf` dans
template_modifier_service.py, qui écrivait le nouveau texte à la position
exacte de l'ancien texte et provoquait des chevauchements dès que le
contenu changeait de longueur.

Ici, reportlab.platypus (un moteur de mise en page "à flux", comme du
HTML/CSS) place lui-même chaque ligne, gère le retour à la ligne et la
pagination automatique. Il ne peut donc plus y avoir de texte superposé.
"""

import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from app.services.optimizer_service import ResumeSection

# ---------------------------------------------------------------------------
# Styles — un seul endroit à modifier si tu veux changer la charte visuelle.
# ---------------------------------------------------------------------------

NAME_STYLE = ParagraphStyle(
    "Name",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    alignment=1,  # centré
    spaceAfter=4,
)

CONTACT_STYLE = ParagraphStyle(
    "Contact",
    fontName="Helvetica",
    fontSize=9.5,
    leading=13,
    alignment=1,
    textColor=colors.HexColor("#444444"),
    spaceAfter=10,
)

SECTION_TITLE_STYLE = ParagraphStyle(
    "SectionTitle",
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=15,
    spaceBefore=10,
    spaceAfter=3,
    textColor=colors.HexColor("#1a1a1a"),
)

BODY_STYLE = ParagraphStyle(
    "Body",
    fontName="Helvetica",
    fontSize=9.5,
    leading=12,
    alignment=0,
    spaceAfter=4,
)
BULLET_STYLE = ParagraphStyle(
    "Bullet",
    parent=BODY_STYLE,
    leftIndent=0,
)

# Titre par défaut si une section optimisée n'a pas gardé son titre d'origine.
DEFAULT_SECTION_TITLES = {
    "summary": "Résumé",
    "skills": "Compétences",
    "experience": "Expérience Professionnelle",
    "education": "Formation",
    "projects": "Projets",
    "languages": "Langues",
}


def _markup_highlighted(line: str, highlight_tokens: frozenset[str]) -> str:
    """Échappe le texte pour reportlab et met en gras les tokens mis en avant
    (compétences requises par l'offre déjà présentes dans le CV)."""
    escaped = escape(line)
    if not highlight_tokens:
        return escaped

    tokens = sorted((t for t in highlight_tokens if t), key=len, reverse=True)
    if not tokens:
        return escaped

    pattern = re.compile("(" + "|".join(re.escape(t) for t in tokens) + ")", re.IGNORECASE)
    return pattern.sub(lambda m: f"<b>{m.group(0)}</b>", escaped)


def _is_list_section(key: str) -> bool:
    return key in {"skills", "languages", "education"}

def _is_project_section(key):
    return key in {
        "projects",
        "experience"
    }

def build_resume_pdf(sections: list[ResumeSection], output_path: Path) -> Path:
    """Construit un PDF propre, une colonne, ATS-friendly à partir des
    sections optimisées."""

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title="CV optimisé",
    )

    story = []

    header = next((s for s in sections if s.key == "header"), None)

    if header and header.lines:
        name, *contact_lines = header.lines

        story.append(
            Paragraph(
                escape(name),
                NAME_STYLE
            )
        )

        if contact_lines:
            story.append(
                Paragraph(
                    " &nbsp;|&nbsp; ".join(
                        escape(c) for c in contact_lines
                    ),
                    CONTACT_STYLE
                )
            )

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.75,
                color=colors.HexColor("#999999"),
                spaceAfter=8
            )
        )

    for section in sections:

        if section.key == "header" or not section.lines:
            continue

        title = (
            section.title
            or DEFAULT_SECTION_TITLES.get(
                section.key,
                section.key.title()
            )
        )

        story.append(
            Paragraph(
                escape(title.strip()),
                SECTION_TITLE_STYLE
            )
        )

        story.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.HexColor("#cccccc"),
                spaceAfter=4
            )
        )

        # Sections sous forme de liste
        if _is_list_section(section.key) and len(section.lines) > 1:

            items = [
                ListItem(
                    Paragraph(
                        _markup_highlighted(
                            line,
                            section.highlight_tokens
                        ),
                        BULLET_STYLE
                    ),
                    leftIndent=10
                )
                for line in section.lines
            ]

            story.append(
                ListFlowable(
                    items,
                    bulletType="bullet",
                    start="•",
                    leftIndent=12,
                    spaceBefore=2
                )
            )

        # Sections normales
        else:

            for line in section.lines:

                markup = _markup_highlighted(
                    line,
                    section.highlight_tokens
                )

                story.append(
                    Paragraph(
                        markup,
                        BODY_STYLE
                    )
                )

        story.append(
            Spacer(1, 6)
        )

    doc.build(story)

    return output_path