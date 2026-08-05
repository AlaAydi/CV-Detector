import re
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from app.services.optimizer_service import ResumeSection, optimize_sections

SECTION_TITLE_DISPLAY = {
    "summary": "Résumé",
    "skills": "Compétences",
    "experience": "Expérience Professionnelle",
    "education": "Formation",
    "projects": "Projets Académiques",
    "languages": "Langues",
}


def _display_title(section: ResumeSection) -> str:
    return section.title or SECTION_TITLE_DISPLAY.get(section.key, section.key.title())


def _highlight_markup(line: str, highlight_tokens: frozenset[str]) -> str:
    """Escape for markup safety, then wrap matched keywords in <b>."""
    text = escape(line)
    if not highlight_tokens:
        return text
    for token in sorted(highlight_tokens, key=len, reverse=True):
        if not token.strip():
            continue
        pattern = re.compile(re.escape(escape(token)), re.IGNORECASE)
        text = pattern.sub(lambda m: f"<b>{m.group(0)}</b>", text)
    return text


def _is_bulleted(line: str) -> bool:
    return line.lstrip().startswith(("-", "•", "·", "*", "▪", "–", "—"))


# ---------------------------------------------------------------------------
# PDF generation — always rebuilt as a flowing document (reportlab Platypus),
# so content that grows or shrinks simply reflows the page instead of
# overlapping fixed coordinates.
# ---------------------------------------------------------------------------

def _pdf_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "NameStyle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=20, leading=24, spaceAfter=2, alignment=TA_LEFT,
            textColor=colors.HexColor("#1a1a1a"),
        ),
        "contact": ParagraphStyle(
            "ContactStyle", parent=base["Normal"], fontSize=9.5, leading=13,
            spaceAfter=12, textColor=colors.HexColor("#555555"),
        ),
        "section_title": ParagraphStyle(
            "SectionTitle", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12, leading=15, spaceBefore=14, spaceAfter=4,
            textColor=colors.HexColor("#16325c"),
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"], fontSize=10, leading=14,
            spaceAfter=3, textColor=colors.HexColor("#222222"),
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["Normal"], fontSize=10, leading=14,
            spaceAfter=3, leftIndent=12, textColor=colors.HexColor("#222222"),
        ),
    }


from app.services.resume_pdf_builder import build_resume_pdf

def generate_optimized_pdf(resume_text: str, job_text: str, output_path: Path) -> Path:
    sections = optimize_sections(resume_text, job_text)
    return build_resume_pdf(sections, output_path)


def generate_pdf(sections, output_path: Path) -> Path:
    """
    Génère un PDF 2 colonnes élégant depuis les sections optimisées.
    Accepte directement List[ResumeSection].
    """
    return build_resume_pdf(sections, output_path)


# ---------------------------------------------------------------------------
# DOCX generation — structured with real heading styles.
# ---------------------------------------------------------------------------

def build_docx_from_sections(sections: list[ResumeSection], output_path: Path) -> Path:
    document = Document()

    for section in sections:
        if section.key == "header":
            if section.lines:
                title = document.add_paragraph()
                run = title.add_run(section.lines[0])
                run.bold = True
                run.font.size = Pt(20)
                title.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if len(section.lines) > 1:
                    contact = document.add_paragraph(" | ".join(section.lines[1:]))
                    for run in contact.runs:
                        run.font.size = Pt(9.5)
                        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
            continue

        if not section.lines:
            continue

        heading = document.add_paragraph()
        run = heading.add_run(_display_title(section).upper())
        run.bold = True
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(0x16, 0x32, 0x5C)

        for line in section.lines:
            display = line if _is_bulleted(line) else f"• {line}" if section.key in {"experience", "projects"} else line
            para = document.add_paragraph(style="List Bullet" if _is_bulleted(display) else None)
            lower = display.lower()
            parts = [display]
            if section.highlight_tokens:
                # simple split-and-bold on highlighted tokens
                pattern = re.compile("(" + "|".join(re.escape(t) for t in section.highlight_tokens) + ")", re.IGNORECASE)
                parts = pattern.split(display) if section.highlight_tokens else [display]
            for part in parts:
                run = para.add_run(part)
                if part.lower() in {t.lower() for t in section.highlight_tokens}:
                    run.bold = True

    document.save(output_path)
    return output_path


def generate_optimized_docx(resume_text: str, job_text: str, output_path: Path) -> Path:
    sections = optimize_sections(resume_text, job_text)
    return build_docx_from_sections(sections, output_path)


def generate_docx(text: str, output_path: Path) -> Path:
    document = Document()
    for paragraph in text.split("\n"):
        document.add_paragraph(paragraph)
    document.save(output_path)
    return output_path