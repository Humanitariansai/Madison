"""
Report generation module
Creates PDF reports from analysis results
"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import json
import logging

logger = logging.getLogger(__name__)

def generate_pdf_report(
    output_path: Path,
    file_name: str,
    sentiment_data: Optional[Dict] = None,
    themes_data: Optional[Dict] = None,
    summaries_data: Optional[Dict] = None,
    trends_data: Optional[Dict] = None,
    priorities_data: Optional[Dict] = None,
    date_range_start: Optional[datetime] = None,
    date_range_end: Optional[datetime] = None,
    metadata: Optional[Dict] = None
) -> Path:
    """
    Generate a comprehensive PDF report from analysis results
    
    Args:
        output_path: Path where PDF will be saved
        file_name: Original file name
        sentiment_data: Sentiment analysis results
        themes_data: Theme extraction results
        summaries_data: Summary data
        trends_data: Trend analysis results
        priorities_data: Theme priorities
        date_range_start: Start date of analysis
        date_range_end: End date of analysis
        metadata: Additional metadata (rows_count, etc.)
    
    Returns:
        Path to generated PDF
    """
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=12
        )
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=8
        )
        normal_style = styles['Normal']
        
        # Title
        elements.append(Paragraph("Survey Analysis Report", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Metadata section
        if metadata:
            metadata_text = f"""
            <b>File:</b> {file_name}<br/>
            <b>Total Responses:</b> {metadata.get('rows_count', 'N/A')}<br/>
            """
            if date_range_start or date_range_end:
                date_str = ""
                if date_range_start:
                    date_str += f"<b>From:</b> {date_range_start.strftime('%Y-%m-%d')} "
                if date_range_end:
                    date_str += f"<b>To:</b> {date_range_end.strftime('%Y-%m-%d')}"
                metadata_text += date_str + "<br/>"
            metadata_text += f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            elements.append(Paragraph(metadata_text, normal_style))
            elements.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        if summaries_data and summaries_data.get('executive_summary'):
            elements.append(Paragraph("Executive Summary", heading_style))
            exec_summary = summaries_data.get('executive_summary', 'No summary available.')
            elements.append(Paragraph(exec_summary, normal_style))
            elements.append(Spacer(1, 0.2*inch))
            elements.append(PageBreak())
        
        # Sentiment Analysis
        if sentiment_data:
            elements.append(Paragraph("Sentiment Analysis", heading_style))
            
            # Sentiment Distribution
            if sentiment_data.get('sentiment_distribution'):
                dist = sentiment_data['sentiment_distribution']
                dist_data = [
                    ['Sentiment', 'Count', 'Percentage'],
                    ['Positive', str(dist.get('positive', 0)), f"{dist.get('positive_pct', 0):.1f}%"],
                    ['Negative', str(dist.get('negative', 0)), f"{dist.get('negative_pct', 0):.1f}%"],
                    ['Neutral', str(dist.get('neutral', 0)), f"{dist.get('neutral_pct', 0):.1f}%"],
                    ['Total', str(dist.get('total', 0)), '100.0%']
                ]
                dist_table = Table(dist_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
                dist_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(dist_table)
                elements.append(Spacer(1, 0.2*inch))
            
            elements.append(Spacer(1, 0.2*inch))
        
        # Theme Analysis
        if themes_data:
            elements.append(Paragraph("Theme Analysis", heading_style))
            
            if themes_data.get('themes') and len(themes_data['themes']) > 0:
                themes = themes_data['themes']
                if isinstance(themes, list) and len(themes) > 0:
                    # Top Themes Table
                    theme_data = [['Rank', 'Theme', 'Weight']]
                    for idx, theme in enumerate(themes[:20], 1):  # Top 20 themes
                        if isinstance(theme, dict):
                            keyphrase = theme.get('keyphrase', theme.get('theme', 'N/A'))
                            weight = theme.get('weight', theme.get('score', 0))
                            theme_data.append([str(idx), keyphrase, f"{float(weight):.3f}"])
                        else:
                            theme_data.append([str(idx), str(theme), 'N/A'])
                    
                    theme_table = Table(theme_data, colWidths=[0.8*inch, 4*inch, 1.2*inch])
                    theme_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    elements.append(theme_table)
                    elements.append(Spacer(1, 0.2*inch))
            
            elements.append(Spacer(1, 0.2*inch))
        
        # Theme Priorities
        if priorities_data and priorities_data.get('priorities'):
            elements.append(Paragraph("Theme Priorities", heading_style))
            
            priorities = priorities_data['priorities']
            if isinstance(priorities, list) and len(priorities) > 0:
                priority_data = [['Theme', 'Count', 'Neg Share', 'Priority Score']]
                for p in priorities[:15]:  # Top 15 priorities
                    if isinstance(p, dict):
                        priority_data.append([
                            p.get('keyphrase', 'N/A'),
                            str(p.get('count', 0)),
                            f"{p.get('neg_share', 0):.2f}",
                            f"{p.get('priority', 0):.2f}"
                        ])
                
                priority_table = Table(priority_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
                priority_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(priority_table)
                elements.append(Spacer(1, 0.2*inch))
        
        # Summaries
        if summaries_data:
            elements.append(PageBreak())
            elements.append(Paragraph("Detailed Summaries", heading_style))
            
            if summaries_data.get('overall_summary'):
                elements.append(Paragraph("Overall Summary", subheading_style))
                elements.append(Paragraph(summaries_data['overall_summary'], normal_style))
                elements.append(Spacer(1, 0.2*inch))
            
            if summaries_data.get('by_theme') and len(summaries_data['by_theme']) > 0:
                elements.append(Paragraph("Summaries by Theme", subheading_style))
                for theme_summary in summaries_data['by_theme'][:10]:  # Top 10 theme summaries
                    if isinstance(theme_summary, dict):
                        theme_name = theme_summary.get('theme', 'Unknown Theme')
                        summary_text = theme_summary.get('summary', 'No summary available.')
                        elements.append(Paragraph(f"<b>{theme_name}</b>", normal_style))
                        elements.append(Paragraph(summary_text, normal_style))
                        elements.append(Spacer(1, 0.1*inch))
        
        # Build PDF
        doc.build(elements)
        logger.info(f"✅ PDF report generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF report: {e}")
        raise

def generate_json_report(
    output_path: Path,
    sentiment_data: Optional[Dict] = None,
    themes_data: Optional[Dict] = None,
    summaries_data: Optional[Dict] = None,
    trends_data: Optional[Dict] = None,
    priorities_data: Optional[Dict] = None,
    metadata: Optional[Dict] = None
) -> Path:
    """
    Generate a JSON report from analysis results
    """
    try:
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "sentiment": sentiment_data,
            "themes": themes_data,
            "summaries": summaries_data,
            "trends": trends_data,
            "priorities": priorities_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"✅ JSON report generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error generating JSON report: {e}")
        raise

