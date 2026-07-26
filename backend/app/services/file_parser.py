import re
from pathlib import Path

import fitz
from docx import Document


def extract_text_from_pdf(filepath: Path) -> str:
    text_parts: list[str] = []
    with fitz.open(filepath) as doc:
        for page in doc:
            page_lines: list[str] = []
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    line_text = "".join(span["text"] for span in line["spans"]).strip()
                    if line_text:
                        page_lines.append(line_text)
            if page_lines:
                text_parts.append("\n".join(page_lines))
    return "\n\n".join(text_parts).strip()


def extract_text_from_docx(filepath: Path) -> str:
    document = Document(filepath)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text(filepath: Path) -> str:
    suffix = filepath.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(filepath)
    if suffix == ".docx":
        return extract_text_from_docx(filepath)
    raise ValueError(f"Unsupported file type: {suffix}")


def clean_text(text: str) -> str:
    """Normalize whitespace per line while keeping paragraph structure."""
    text = text.replace("\x00", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def flatten_text(text: str) -> str:
    """Single-line version for keyword matching."""
    return re.sub(r"\s+", " ", text).strip()
