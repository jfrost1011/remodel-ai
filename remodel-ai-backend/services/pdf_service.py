from typing import Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from config import estimates_cache
import os
import logging
from datetime import datetime
logger = logging.getLogger(__name__)
class PDFService:
    def __init__(self):
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)
    async def generate_estimate_pdf(
        self, 
        estimate_id: str, 
        include_breakdown: bool = True,
        include_similar_projects: bool = True
    ) -> str:
        """Generate a PDF report for an estimate"""
        try:
            # Get estimate data
            estimate_data = estimates_cache.get(estimate_id)
            if not estimate_data:
                raise ValueError(f"Estimate {estimate_id} not found")
            # Create PDF
            filename = f"{estimate_id}.pdf"
            filepath = os.path.join(self.export_dir, filename)
            doc = SimpleDocTemplate(filepath, pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#10B981'),
                spaceAfter=30,
                alignment=1
            )
            story.append(Paragraph("RemodelAI Cost Estimate", title_style))
            story.append(Spacer(1, 0.5*inch))
            # Estimate details
            story.append(Paragraph(f"Estimate ID: {estimate_id}", styles['Normal']))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            # Cost summary
            story.append(Paragraph("Cost Summary", styles['Heading2']))
            cost_data = [
                ['Item', 'Amount'],
                ['Total Estimate', f"${estimate_data['total_cost']:,.0f}"],
                ['Low Range', f"${estimate_data['cost_range_low']:,.0f}"],
                ['High Range', f"${estimate_data['cost_range_high']:,.0f}"],
                ['Confidence Score', f"{estimate_data['confidence_score']*100:.0f}%"]
            ]
            cost_table = Table(cost_data, colWidths=[3*inch, 2*inch])
            cost_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(cost_table)
            story.append(Spacer(1, 0.5*inch))
            # Cost breakdown
            if include_breakdown:
                story.append(Paragraph("Cost Breakdown", styles['Heading2']))
                breakdown_data = [
                    ['Category', 'Amount', 'Percentage'],
                    ['Materials', f"${estimate_data['cost_breakdown']['materials']:,.0f}", "40%"],
                    ['Labor', f"${estimate_data['cost_breakdown']['labor']:,.0f}", "35%"],
                    ['Permits', f"${estimate_data['cost_breakdown']['permits']:,.0f}", "5%"],
                    ['Other', f"${estimate_data['cost_breakdown']['other']:,.0f}", "20%"],
                ]
                breakdown_table = Table(breakdown_data, colWidths=[2*inch, 2*inch, 1.5*inch])
                breakdown_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ]))
                story.append(breakdown_table)
                story.append(Spacer(1, 0.5*inch))
            # Timeline
            story.append(Paragraph("Project Timeline", styles['Heading2']))
            timeline_data = [
                ['Phase', 'Duration'],
                ['Planning', f"{estimate_data['timeline']['planning_days']} days"],
                ['Permits', f"{estimate_data['timeline']['permit_days']} days"],
                ['Construction', f"{estimate_data['timeline']['construction_days']} days"],
                ['Total', f"{estimate_data['timeline']['total_days']} days"],
            ]
            timeline_table = Table(timeline_data, colWidths=[3*inch, 2*inch])
            timeline_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(timeline_table)
            story.append(Spacer(1, 0.5*inch))
            # Footer
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=1
            )
            story.append(Spacer(1, 1*inch))
            story.append(Paragraph("Generated by RemodelAI - AI-Powered Construction Estimates", footer_style))
            story.append(Paragraph("Estimates are approximations based on historical data", footer_style))
            story.append(Paragraph("Valid for 30 days from generation date", footer_style))
            # Build PDF
            doc.build(story)
            return filepath
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    def get_export_path(self, estimate_id: str) -> Optional[str]:
        """Get the file path for an exported estimate"""
        filepath = os.path.join(self.export_dir, f"{estimate_id}.pdf")
        if os.path.exists(filepath):
            return filepath
        return None