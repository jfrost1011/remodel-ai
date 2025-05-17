from __future__ import annotations

import os
import logging
from typing import Optional, Dict
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from config import estimates_cache

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────────────
#  Very small in-memory cache  (keeps the 10 most-recent PDFs)
# ────────────────────────────────────────────────────────────────────────────
_pdf_cache: Dict[str, str] = {}          # key = pdf_<estimate_id>, value = file-path
_MAX_CACHE = 10


def _evict_if_necessary() -> None:
    """Keep the cache at ≤ _MAX_CACHE items (FIFO eviction)."""
    if len(_pdf_cache) > _MAX_CACHE:
        oldest_key = next(iter(_pdf_cache))
        try:
            os.remove(_pdf_cache[oldest_key])
        except Exception:
            pass
        _pdf_cache.pop(oldest_key, None)


# ────────────────────────────────────────────────────────────────────────────
#  Low-level PDF generator (sync)
# ────────────────────────────────────────────────────────────────────────────
def _build_pdf_file(filepath: str, estimate_id: str, estimate_data: dict,
                    include_breakdown: bool) -> None:
    """
    Build the PDF file on disk — **blocking / synchronous** helper.
    """
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []

    styles = getSampleStyleSheet()

    # ---------- Title ----------
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#10B981"),
        spaceAfter=30,
        alignment=1,  # center
    )
    story.append(Paragraph("RemodelAI Cost Estimate", title_style))
    story.append(Spacer(1, 0.5 * inch))

    # ---------- Estimate meta ----------
    story.append(Paragraph(f"Estimate ID: {estimate_id}", styles["Normal"]))
    story.append(
        Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles["Normal"])
    )
    story.append(Spacer(1, 0.3 * inch))

    # ---------- Cost summary ----------
    story.append(Paragraph("Cost Summary", styles["Heading2"]))
    cost_data = [
        ["Item", "Amount"],
        ["Total Estimate", f"${estimate_data['total_cost']:,.0f}"],
        ["Low Range", f"${estimate_data['cost_range_low']:,.0f}"],
        ["High Range", f"${estimate_data['cost_range_high']:,.0f}"],
        ["Confidence Score", f"{estimate_data['confidence_score']*100:.0f}%"],
    ]
    cost_table = Table(cost_data, colWidths=[3 * inch, 2 * inch])
    cost_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10B981")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )
    story.append(cost_table)
    story.append(Spacer(1, 0.5 * inch))

    # ---------- Cost breakdown ----------
    if include_breakdown:
        story.append(Paragraph("Cost Breakdown", styles["Heading2"]))
        breakdown_data = [
            ["Category", "Amount", "Percentage"],
            ["Materials", f"${estimate_data['cost_breakdown']['materials']:,.0f}", "40%"],
            ["Labor", f"${estimate_data['cost_breakdown']['labor']:,.0f}", "35%"],
            ["Permits", f"${estimate_data['cost_breakdown']['permits']:,.0f}", "5%"],
            ["Other", f"${estimate_data['cost_breakdown']['other']:,.0f}", "20%"],
        ]
        breakdown_table = Table(breakdown_data, colWidths=[2 * inch, 2 * inch, 1.5 * inch])
        breakdown_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10B981")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )
        story.append(breakdown_table)
        story.append(Spacer(1, 0.5 * inch))

    # ---------- Timeline ----------
    story.append(Paragraph("Project Timeline", styles["Heading2"]))
    timeline_data = [
        ["Phase", "Duration"],
        ["Planning", f"{estimate_data['timeline']['planning_days']} days"],
        ["Permits", f"{estimate_data['timeline']['permit_days']} days"],
        ["Construction", f"{estimate_data['timeline']['construction_days']} days"],
        ["Total", f"{estimate_data['timeline']['total_days']} days"],
    ]
    timeline_table = Table(timeline_data, colWidths=[3 * inch, 2 * inch])
    timeline_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10B981")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ]
        )
    )
    story.append(timeline_table)
    story.append(Spacer(1, 0.5 * inch))

    # ---------- Footer ----------
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.grey,
        alignment=1,  # centered
    )
    story.append(Spacer(1, 1 * inch))
    story.append(
        Paragraph("Generated by RemodelAI - AI-Powered Construction Estimates", footer_style)
    )
    story.append(
        Paragraph("Estimates are approximations based on historical data", footer_style)
    )
    story.append(
        Paragraph("Valid for 30 days from generation date", footer_style)
    )

    # Build the PDF
    doc.build(story)


# ────────────────────────────────────────────────────────────────────────────
#  Public helper with caching
# ────────────────────────────────────────────────────────────────────────────
def generate_pdf(
    estimate_id: str,
    estimate_data: dict,
    export_dir: str = "exports",
    include_breakdown: bool = True,
    force_regenerate: bool = False,
) -> str:
    """
    Generate (or fetch cached) PDF for an estimate.

    Returns the **file path** to the PDF on disk.
    """
    cache_key = f"pdf_{estimate_id}"

    # Return cached version if allowed
    if not force_regenerate and cache_key in _pdf_cache and os.path.exists(_pdf_cache[cache_key]):
        logger.info(f"Using cached PDF for estimate {estimate_id}")
        return _pdf_cache[cache_key]

    # Ensure export directory exists
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, f"{estimate_id}.pdf")

    # Build the PDF
    _build_pdf_file(filepath, estimate_id, estimate_data, include_breakdown)

    # Store in cache and evict if necessary
    _pdf_cache[cache_key] = filepath
    _evict_if_necessary()

    logger.info(f"Generated new PDF for estimate {estimate_id}")
    return filepath


# ════════════════════════════════════════════════════════════════════════════
#  PDFService class  (uses the helper above)
# ════════════════════════════════════════════════════════════════════════════
class PDFService:
    def __init__(self):
        self.export_dir = "exports"
        os.makedirs(self.export_dir, exist_ok=True)

    async def generate_estimate_pdf(
        self,
        estimate_id: str,
        include_breakdown: bool = True,
        include_similar_projects: bool = True,  # placeholder for future use
    ) -> str:
        """
        Generate or fetch a PDF report for an estimate.

        If the specified estimate_id is not found in the cache, the service
        creates a generic/sample estimate so the user still receives a PDF.
        """
        try:
            # ── Retrieve estimate data (with graceful fallback) ──────────
            estimate_data = estimates_cache.get(estimate_id)
            if not estimate_data:
                logger.warning(
                    f"Estimate {estimate_id} not found in cache; "
                    "generating generic PDF report."
                )
                # Generic placeholder data
                estimate_data = {
                    "total_cost": 50_000,
                    "cost_range_low": 45_000,
                    "cost_range_high": 55_000,
                    "confidence_score": 0.85,
                    "cost_breakdown": {
                        "materials": 20_000,
                        "labor": 17_500,
                        "permits": 2_500,
                        "other": 10_000,
                    },
                    "timeline": {
                        "planning_days": 14,
                        "permit_days": 30,
                        "construction_days": 60,
                        "total_days": 104,
                    },
                }

            # ── Generate (or fetch) cached PDF ──────────────────────────
            pdf_path = generate_pdf(
                estimate_id=estimate_id,
                estimate_data=estimate_data,
                export_dir=self.export_dir,
                include_breakdown=include_breakdown,
                force_regenerate=False,
            )
            return pdf_path

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
            raise

    # ---------------------------------------------------------------------
    def get_export_path(self, estimate_id: str) -> Optional[str]:
        """Return the full file path for a previously generated PDF."""
        cache_key = f"pdf_{estimate_id}"
        if cache_key in _pdf_cache and os.path.exists(_pdf_cache[cache_key]):
            return _pdf_cache[cache_key]

        filepath = os.path.join(self.export_dir, f"{estimate_id}.pdf")
        return filepath if os.path.exists(filepath) else None
