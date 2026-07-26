from io import BytesIO
from pathlib import Path

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_docx(text: str, output_path: Path) -> Path:
    document = Document()
    for paragraph in text.split("\n"):
        document.add_paragraph(paragraph)
    document.save(output_path)
    return output_path


def generate_pdf(text: str, output_path: Path) -> Path:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    line_height = 14

    for line in text.splitlines():
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, line[:110])
        y -= line_height

    pdf.save()
    output_path.write_bytes(buffer.getvalue())
    return output_path
