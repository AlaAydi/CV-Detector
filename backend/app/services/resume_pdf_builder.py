"""
Générateur de CV optimisé au format PDF — Template Moderne à 2 colonnes.
Reconstruit le CV sous un design élégant à 2 colonnes (en-tête bleu marine,
chips pour les compétences, cartes de projets, indicateurs de langues à points)
tout en conservant et mettant en avant les compétences optimisées ATS.
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
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.optimizer_service import ResumeSection, DEFAULT_SECTION_TITLES


def _markup_highlighted(line: str, highlight_tokens: frozenset[str]) -> str:
    """Échappe le texte et entoure les compétences mises en avant avec du gras et une couleur d'accent."""
    text = escape(line)
    if not highlight_tokens:
        return text
    tokens = sorted((t for t in highlight_tokens if t.strip()), key=len, reverse=True)
    if not tokens:
        return text
    pattern = re.compile("(" + "|".join(re.escape(escape(t)) for t in tokens) + ")", re.IGNORECASE)
    return pattern.sub(lambda m: f"<b><font color='#1d4ed8'>{m.group(0)}</font></b>", text)

_highlight_markup = _markup_highlighted


def build_resume_pdf(sections: list[ResumeSection], output_path: Path) -> Path:
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )
    story = []

    # ---------------------------------------------------------------------------
    # 1. EN-TÊTE DU CV (Nom, Titre, Contacts)
    # ---------------------------------------------------------------------------
    header = next((s for s in sections if s.key == "header"), None)
    if header and header.lines:
        lines = header.lines
        name = lines[0] if lines else "CV"
        subtitle = lines[1] if len(lines) > 1 and not any(char in lines[1] for char in ["•", "+", "@"]) else ""
        contact_start = 2 if subtitle else 1
        contact_items = [l.strip() for l in lines[contact_start:] if l.strip()]

        style_name = ParagraphStyle(
            "NameStyle",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=25,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=2,
        )
        style_sub = ParagraphStyle(
            "SubStyle",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#1d4ed8"),
            spaceAfter=5,
        )
        style_contact = ParagraphStyle(
            "ContactStyle",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#475569"),
            spaceAfter=6,
        )

        story.append(Paragraph(escape(name), style_name))
        if subtitle:
            story.append(Paragraph(escape(subtitle), style_sub))
        if contact_items:
            contact_str = " &nbsp;&nbsp;•&nbsp;&nbsp; ".join(escape(c) for c in contact_items)
            story.append(Paragraph(contact_str, style_contact))

        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1d4ed8"), spaceAfter=8))

    # ---------------------------------------------------------------------------
    # 2. STYLES DU CORPS DU CV
    # ---------------------------------------------------------------------------
    sec_header_style = ParagraphStyle(
        "SecHeader",
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=4,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2,
        leftIndent=6,
    )
    job_title_style = ParagraphStyle(
        "JobTitle",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=3,
        spaceAfter=1,
    )
    job_meta_style = ParagraphStyle(
        "JobMeta",
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#1d4ed8"),
        spaceAfter=2,
    )

    def render_section_content(section: ResumeSection) -> list:
        res = []
        display_title = section.title or DEFAULT_SECTION_TITLES.get(section.key, section.key.upper())
        res.append(Paragraph(escape(display_title.upper()), sec_header_style))
        res.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1d4ed8"), spaceAfter=3))

        if section.key == "skills":
            # Affichage sous forme de badges de compétences
            badge_htmls = []
            for line in section.lines:
                for skill in re.split(r"[,;\n]", line):
                    skill = skill.strip()
                    if not skill:
                        continue
                    is_promoted = any(t in skill.lower() for t in section.highlight_tokens)
                    if is_promoted:
                        badge_htmls.append(f"<font color='#1e40af'><b>• {escape(skill)}</b></font>")
                    else:
                        badge_htmls.append(f"<font color='#334155'>• {escape(skill)}</font>")
            chips_str = " &nbsp;&nbsp; ".join(badge_htmls)
            res.append(Paragraph(chips_str, body_style))

        elif section.key == "languages":
            # Affichage des langues avec indicateur visuel de niveau
            for line in section.lines:
                lower = line.lower()
                if "maternelle" in lower or "native" in lower:
                    dots = "<font color='#1d4ed8'>●●●●●</font>"
                elif "courant" in lower or "fluent" in lower or "c1" in lower or "c2" in lower:
                    dots = "<font color='#1d4ed8'>●●●●</font><font color='#cbd5e1'>○</font>"
                elif "intermédiaire" in lower or "intermediate" in lower or "b1" in lower or "b2" in lower:
                    dots = "<font color='#1d4ed8'>●●●</font><font color='#cbd5e1'>○○</font>"
                else:
                    dots = "<font color='#1d4ed8'>●●</font><font color='#cbd5e1'>○○○</font>"
                lang_markup = _markup_highlighted(line, section.highlight_tokens)
                res.append(Paragraph(f"<b>{lang_markup}</b> &nbsp; {dots}", body_style))

        elif section.key in ("experience", "projects"):
            for line in section.lines:
                markup = _highlight_markup(line, section.highlight_tokens)
                if line.startswith("{") or "202" in line or "201" in line:
                    res.append(Paragraph(markup, job_meta_style))
                elif not line.startswith("•") and not line.startswith("-") and len(line) < 45:
                    res.append(Paragraph(markup, job_title_style))
                elif line.startswith("•") or line.startswith("-"):
                    res.append(Paragraph(markup, bullet_style))
                else:
                    res.append(Paragraph(markup, body_style))
        else:
            for line in section.lines:
                markup = _highlight_markup(line, section.highlight_tokens)
                if line.startswith("•") or line.startswith("-"):
                    res.append(Paragraph(markup, bullet_style))
                else:
                    res.append(Paragraph(markup, body_style))

        res.append(Spacer(1, 4))
        return res

    # ---------------------------------------------------------------------------
    # 3. ORGANISATION EN 2 COLONNES
    # ---------------------------------------------------------------------------
    sec_map = {s.key: s for s in sections if s.key != "header" and s.lines}

    rows = []
    # Ligne 1 : Résumé (Gauche) & Compétences (Droite)
    left1 = render_section_content(sec_map["summary"]) if "summary" in sec_map else []
    right1 = render_section_content(sec_map["skills"]) if "skills" in sec_map else []
    if left1 or right1:
        rows.append([left1, right1])

    # Ligne 2 : Expérience (Gauche) & Projets (Droite)
    left2 = render_section_content(sec_map["experience"]) if "experience" in sec_map else []
    right2 = render_section_content(sec_map["projects"]) if "projects" in sec_map else []
    if left2 or right2:
        rows.append([left2, right2])

    # Ligne 3 : Éducation (Gauche) & Langues (Droite)
    left3 = render_section_content(sec_map["education"]) if "education" in sec_map else []
    right3 = render_section_content(sec_map["languages"]) if "languages" in sec_map else []
    if left3 or right3:
        rows.append([left3, right3])

    # Ligne 4 : Formations / Cours (Gauche)
    left4 = render_section_content(sec_map["courses"]) if "courses" in sec_map else []
    if left4:
        rows.append([left4, []])

    # Traiter les rubriques personnalisées ou non classées
    handled_keys = {"summary", "skills", "experience", "projects", "education", "languages", "courses"}
    remaining_keys = [k for k in sec_map.keys() if k not in handled_keys]
    for key in remaining_keys:
        res = render_section_content(sec_map[key])
        rows.append([res, []])

    # Construction du tableau 2 colonnes avec découpage automatique des lignes
    table = Table(rows, colWidths=[325, 195])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 8),
                ("LEFTPADDING", (1, 0), (1, -1), 8),
                ("RIGHTPADDING", (1, 0), (1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(table)

    doc.build(story)
    return output_path