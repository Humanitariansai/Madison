"""
PDF report generation
"""
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
from PIL import Image as PILImage
from typing import List, Optional, Dict
import pandas as pd

class ReportSection:
    def __init__(self, title: str, image_bytes: bytes):
        self.title = title
        self.image_bytes = image_bytes

def build_pdf_report(
    output_path: Path,
    title: str,
    subtitle: str,
    exec_summary_md: str,
    priority_df: Optional[pd.DataFrame],
    sections: List[ReportSection],
    appendix_json: Optional[Dict] = None
) -> Path:
    """
    Build PDF report
    """
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph(title, styles['Title']))
    story.append(Paragraph(subtitle, styles['Heading2']))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive summary
    story.append(Paragraph("Executive Summary", styles['Heading1']))
    story.append(Paragraph(exec_summary_md, styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Sections
    for section in sections:
        story.append(PageBreak())
        story.append(Paragraph(section.title, styles['Heading1']))
        if section.image_bytes:
            img = Image(io.BytesIO(section.image_bytes), width=6*inch, height=4*inch)
            story.append(img)
        story.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(story)
    return output_path

