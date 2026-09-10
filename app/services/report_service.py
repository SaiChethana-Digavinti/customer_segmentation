# ============================================================
# REPORT GENERATION SERVICE
# Multi-Format Report Generator (CSV, Excel, PDF, DOCX, JSON)
# ============================================================

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("report_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# ------------------------------------------------------------
# 3rd Party Libraries
# ------------------------------------------------------------
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from docx import Document
from docx.enum.section import WD_ORIENTATION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# HELPER: FILE NAME BUILDER
# ============================================================

def build_report_filename(prefix: str, extension: str, filter_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Construct a descriptive filename incorporating segment or priority filter tags.
    """
    segment = filter_info.get("segment") if filter_info else None
    if segment and str(segment).strip():
        safe_tag = str(segment).strip().lower().replace(" ", "_")
    else:
        safe_tag = "all"

    ext = extension.lstrip(".")
    return f"{prefix}_{safe_tag}.{ext}"


def _get_summary_stats(customers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics across the given customer cohort.
    """
    total = len(customers)
    total_rev = sum(float(c.get("monetary", 0.0) or 0.0) for c in customers)
    avg_spend = (total_rev / total) if total > 0 else 0.0
    avg_rec = (sum(float(c.get("recency", 0.0) or 0.0) for c in customers) / total) if total > 0 else 0.0
    avg_freq = (sum(float(c.get("frequency", 0.0) or 0.0) for c in customers) / total) if total > 0 else 0.0

    segment_counts: Dict[str, int] = {}
    segment_rev: Dict[str, float] = {}
    for c in customers:
        seg = str(c.get("segment", "Unknown"))
        segment_counts[seg] = segment_counts.get(seg, 0) + 1
        segment_rev[seg] = segment_rev.get(seg, 0.0) + float(c.get("monetary", 0.0) or 0.0)

    top_seg = max(segment_counts.items(), key=lambda x: x[1])[0] if segment_counts else "None"

    return {
        "total_customers": total,
        "total_revenue": total_rev,
        "average_spend": avg_spend,
        "average_recency": avg_rec,
        "average_frequency": avg_freq,
        "segment_counts": segment_counts,
        "segment_revenue": segment_rev,
        "top_segment": top_seg,
    }


# ============================================================
# 1. CSV REPORT GENERATOR
# ============================================================

def generate_csv_report(
    customers: List[Dict[str, Any]],
    filter_info: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Generate CSV string and filename for customer segmentation.
    """
    output = io.StringIO()
    fieldnames = [
        "CustomerID",
        "Segment",
        "Recency",
        "Frequency",
        "Monetary",
        "RFM_Score",
        "RFM_Total",
        "Priority",
        "Campaign",
        "Marketing_Strategy",
        "Recommended_Action",
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for c in customers:
        writer.writerow({
            "CustomerID": c.get("customer_id", ""),
            "Segment": c.get("segment", ""),
            "Recency": c.get("recency", ""),
            "Frequency": c.get("frequency", ""),
            "Monetary": f"{float(c.get('monetary', 0.0) or 0.0):.2f}",
            "RFM_Score": c.get("rfm_score", ""),
            "RFM_Total": c.get("rfm_total", ""),
            "Priority": c.get("priority", ""),
            "Campaign": c.get("campaign", ""),
            "Marketing_Strategy": c.get("marketing_strategy", ""),
            "Recommended_Action": c.get("recommended_action", ""),
        })

    csv_content = output.getvalue()
    output.close()

    filename = build_report_filename("customer_segmentation_report", "csv", filter_info)
    return csv_content, filename


# ============================================================
# 2. EXCEL (.xlsx) REPORT GENERATOR
# ============================================================

def generate_excel_report(
    customers: List[Dict[str, Any]],
    filter_info: Optional[Dict[str, Any]] = None,
) -> Tuple[bytes, str]:
    """
    Generate formatted Excel workbook (.xlsx) with customer details and summary sheets.
    """
    wb = openpyxl.Workbook()

    # Sheet 1: Customer Details
    ws_customers = wb.active
    ws_customers.title = "Customer Segmentation"
    ws_customers.views.sheetView[0].showGridLines = True

    # Color Palette & Styles
    navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    soft_blue_fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=16, bold=True, color="1E3A8A")
    meta_font = Font(name="Calibri", size=9, italic=True, color="64748B")
    bold_font = Font(name="Calibri", size=11, bold=True, color="0F172A")
    regular_font = Font(name="Calibri", size=10, color="1E293B")

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )
    total_top_border = Side(style="thin", color="1E3A8A")
    total_bottom_border = Side(style="double", color="1E3A8A")
    total_border = Border(top=total_top_border, bottom=total_bottom_border)

    # Title & Subtitle Banner
    ws_customers.append(["Customer Segmentation & Marketing Analytics Report"])
    ws_customers.cell(row=1, column=1).font = title_font

    active_seg = filter_info.get("segment") if filter_info else "All"
    active_pri = filter_info.get("priority") if filter_info else "All"
    gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_text = f"Generated: {gen_time}  |  Segment Filter: {active_seg or 'All'}  |  Priority Filter: {active_pri or 'All'}  |  Records: {len(customers)}"
    ws_customers.append([meta_text])
    ws_customers.cell(row=2, column=1).font = meta_font
    ws_customers.append([])  # Empty line

    # Headers
    headers = [
        "Customer ID",
        "Segment",
        "Recency (Days)",
        "Frequency (Orders)",
        "Monetary (Spend ₹)",
        "RFM Score",
        "RFM Total",
        "Priority",
        "Assigned Campaign",
        "Marketing Strategy",
        "Recommended Action",
    ]
    ws_customers.append(headers)
    header_row_idx = 4

    for col_idx in range(1, len(headers) + 1):
        cell = ws_customers.cell(row=header_row_idx, column=col_idx)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws_customers.row_dimensions[header_row_idx].height = 26

    # Data Rows
    for row_num, c in enumerate(customers, start=header_row_idx + 1):
        monetary_val = float(c.get("monetary", 0.0) or 0.0)
        row_values = [
            c.get("customer_id", ""),
            c.get("segment", ""),
            int(c.get("recency", 0) or 0),
            int(c.get("frequency", 0) or 0),
            monetary_val,
            str(c.get("rfm_score", "")),
            int(c.get("rfm_total", 0) or 0),
            str(c.get("priority", "")),
            str(c.get("campaign", "")),
            str(c.get("marketing_strategy", "")),
            str(c.get("recommended_action", "")),
        ]
        ws_customers.append(row_values)

        # Formatting
        row_cell_bg = soft_blue_fill if row_num % 2 == 0 else PatternFill(fill_type=None)
        for col_idx in range(1, len(headers) + 1):
            cell = ws_customers.cell(row=row_num, column=col_idx)
            cell.font = regular_font
            cell.border = thin_border
            if row_num % 2 == 0:
                cell.fill = row_cell_bg

            # Column specific alignments
            if col_idx in (1, 6, 7, 8):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (3, 4):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            elif col_idx == 5:
                cell.alignment = Alignment(horizontal="right", vertical="center")
                cell.number_format = '"₹"#,##0.00'
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

        ws_customers.row_dimensions[row_num].height = 20

    # Summary Row
    summary_row_idx = header_row_idx + len(customers) + 1
    total_spend = sum(float(c.get("monetary", 0.0) or 0.0) for c in customers)
    ws_customers.cell(row=summary_row_idx, column=1, value="Total Portfolio").font = bold_font
    ws_customers.cell(row=summary_row_idx, column=2, value=f"{len(customers)} Customers").font = bold_font
    sum_cell = ws_customers.cell(row=summary_row_idx, column=5, value=total_spend)
    sum_cell.font = bold_font
    sum_cell.number_format = '"₹"#,##0.00'

    for col_idx in range(1, len(headers) + 1):
        ws_customers.cell(row=summary_row_idx, column=col_idx).border = total_border

    # Auto-adjust column widths
    for col in ws_customers.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if cell.row < 3:
                continue  # skip title
            max_len = max(max_len, len(val_str))
        ws_customers.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Sheet 2: Segment Breakdown Summary
    ws_summary = wb.create_sheet(title="Segment Summary")
    ws_summary.views.sheetView[0].showGridLines = True

    ws_summary.append(["Customer Segments Summary & Financial Metrics"])
    ws_summary.cell(row=1, column=1).font = title_font
    ws_summary.append([])

    sum_headers = [
        "Segment",
        "Customer Count",
        "Customer Share (%)",
        "Total Revenue (₹)",
        "Revenue Share (%)",
        "Average Spend (₹)",
    ]
    ws_summary.append(sum_headers)
    for col_idx in range(1, len(sum_headers) + 1):
        cell = ws_summary.cell(row=3, column=col_idx)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws_summary.row_dimensions[3].height = 24

    stats = _get_summary_stats(customers)
    total_cust = stats["total_customers"]
    total_revenue = stats["total_revenue"]

    s_row = 4
    for seg, count in stats["segment_counts"].items():
        rev = stats["segment_revenue"].get(seg, 0.0)
        cust_pct = (count / total_cust * 100) if total_cust > 0 else 0.0
        rev_pct = (rev / total_revenue * 100) if total_revenue > 0 else 0.0
        avg_spend = (rev / count) if count > 0 else 0.0

        ws_summary.append([
            seg,
            count,
            f"{cust_pct:.1f}%",
            rev,
            f"{rev_pct:.1f}%",
            avg_spend,
        ])
        ws_summary.cell(row=s_row, column=1).alignment = Alignment(horizontal="left", vertical="center")
        ws_summary.cell(row=s_row, column=2).alignment = Alignment(horizontal="right", vertical="center")
        ws_summary.cell(row=s_row, column=3).alignment = Alignment(horizontal="right", vertical="center")
        c4 = ws_summary.cell(row=s_row, column=4)
        c4.alignment = Alignment(horizontal="right", vertical="center")
        c4.number_format = '"₹"#,##0.00'
        ws_summary.cell(row=s_row, column=5).alignment = Alignment(horizontal="right", vertical="center")
        c6 = ws_summary.cell(row=s_row, column=6)
        c6.alignment = Alignment(horizontal="right", vertical="center")
        c6.number_format = '"₹"#,##0.00'

        for col_idx in range(1, len(sum_headers) + 1):
            ws_summary.cell(row=s_row, column=col_idx).border = thin_border
        s_row += 1

    # Auto-adjust column widths for Sheet 2
    for col in ws_summary.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = max(len(str(cell.value or "")) for cell in col if cell.row > 2) if col else 12
        ws_summary.column_dimensions[col_letter].width = max(max_len + 4, 16)

    # Save to buffer
    output = io.BytesIO()
    wb.save(output)
    xlsx_bytes = output.getvalue()
    output.close()

    filename = build_report_filename("customer_segmentation_report", "xlsx", filter_info)
    return xlsx_bytes, filename


# ============================================================
# 3. PDF REPORT GENERATOR (ReportLab)
# ============================================================

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute total pages and render a professional footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        page_w, page_h = self._pagesize

        # Running footer
        self.drawString(36, 22, "Customer AI Analytics Platform  |  Confidential")
        self.drawRightString(page_w - 36, 22, f"Page {self._pageNumber} of {page_count}")

        # Footer divider line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 32, page_w - 36, 32)

        self.restoreState()


def generate_pdf_report(
    customers: List[Dict[str, Any]],
    filter_info: Optional[Dict[str, Any]] = None,
) -> Tuple[bytes, str]:
    """
    Generate professional landscape PDF report with ReportLab Platypus.
    """
    output = io.BytesIO()

    # 11 x 8.5 inches landscape (792 x 612 pt)
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=14,
    )

    kpi_val_style = ParagraphStyle(
        "KPIVal",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,  # Center
    )

    kpi_lbl_style = ParagraphStyle(
        "KPILbl",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0,
    )

    table_header_center_style = ParagraphStyle(
        "TableHeaderCenter",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
    )

    table_cell_center = ParagraphStyle(
        "TableCellCenter",
        parent=table_cell_style,
        alignment=1,
    )

    table_cell_right = ParagraphStyle(
        "TableCellRight",
        parent=table_cell_style,
        alignment=2,
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Customer Segmentation & AI Marketing Report", title_style))

    active_seg = filter_info.get("segment") if filter_info else "All"
    active_pri = filter_info.get("priority") if filter_info else "All"
    gen_time = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    sub_text = (
        f"<b>Generated:</b> {gen_time} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Segment Filter:</b> {active_seg or 'All'} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Priority Filter:</b> {active_pri or 'All'} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"<b>Total Customers:</b> {len(customers)}"
    )
    story.append(Paragraph(sub_text, subtitle_style))

    # KPI Cards Row
    stats = _get_summary_stats(customers)
    kpi_data = [
        [
            Paragraph(f"{stats['total_customers']}", kpi_val_style),
            Paragraph(f"₹{stats['total_revenue']:,.2f}", kpi_val_style),
            Paragraph(f"₹{stats['average_spend']:,.2f}", kpi_val_style),
            Paragraph(f"{stats['average_recency']:.1f} days", kpi_val_style),
            Paragraph(f"{stats['top_segment']}", kpi_val_style),
        ],
        [
            Paragraph("TOTAL CUSTOMERS", kpi_lbl_style),
            Paragraph("TOTAL PORTFOLIO REVENUE", kpi_lbl_style),
            Paragraph("AVERAGE CUSTOMER VALUE", kpi_lbl_style),
            Paragraph("AVERAGE RECENCY", kpi_lbl_style),
            Paragraph("LARGEST COHORT", kpi_lbl_style),
        ],
    ]

    # Available printable width = 792 - 72 = 720 pt
    kpi_table = Table(kpi_data, colWidths=[144, 144, 144, 144, 144])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # Main Customer Records Table
    # Widths summing to 720: 50 + 80 + 45 + 40 + 65 + 45 + 35 + 45 + 135 + 180 = 720 pt
    col_widths = [50, 80, 45, 40, 65, 45, 35, 45, 135, 180]

    headers = [
        Paragraph("Cust ID", table_header_center_style),
        Paragraph("Segment", table_header_style),
        Paragraph("Recency", table_header_center_style),
        Paragraph("Freq", table_header_center_style),
        Paragraph("Spend", table_header_center_style),
        Paragraph("RFM", table_header_center_style),
        Paragraph("Score", table_header_center_style),
        Paragraph("Priority", table_header_center_style),
        Paragraph("Assigned Campaign", table_header_style),
        Paragraph("Strategy & Recommended Action", table_header_style),
    ]

    table_data = [headers]

    for c in customers:
        spend_str = f"₹{float(c.get('monetary', 0.0) or 0.0):,.2f}"
        rec_str = f"{c.get('recency', 0)}d"
        strategy = c.get("marketing_strategy", "")
        action = c.get("recommended_action", "")
        combined_action = f"<b>{strategy}</b>: {action}" if strategy else action

        row = [
            Paragraph(str(c.get("customer_id", "")), table_cell_center),
            Paragraph(str(c.get("segment", "")), table_cell_style),
            Paragraph(rec_str, table_cell_center),
            Paragraph(str(c.get("frequency", 0)), table_cell_center),
            Paragraph(spend_str, table_cell_right),
            Paragraph(str(c.get("rfm_score", "")), table_cell_center),
            Paragraph(str(c.get("rfm_total", "")), table_cell_center),
            Paragraph(str(c.get("priority", "")), table_cell_center),
            Paragraph(str(c.get("campaign", "")), table_cell_style),
            Paragraph(combined_action, table_cell_style),
        ]
        table_data.append(row)

    cust_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    cust_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))

    story.append(cust_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = output.getvalue()
    output.close()

    filename = build_report_filename("customer_segmentation_report", "pdf", filter_info)
    return pdf_bytes, filename


# ============================================================
# 4. WORD DOCUMENT (.docx) REPORT GENERATOR
# ============================================================

def _set_cell_background(cell, fill_hex: str):
    """
    Set background color of a Word table cell using XML.
    """
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """
    Set inner cell margins in twips (1 pt = 20 twips).
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def generate_docx_report(
    customers: List[Dict[str, Any]],
    filter_info: Optional[Dict[str, Any]] = None,
) -> Tuple[bytes, str]:
    """
    Generate professional Microsoft Word document (.docx) with tables and formatting.
    """
    doc = Document()

    # Landscape Orientation for Wide Data Table
    section = doc.sections[0]
    section.orientation = WD_ORIENTATION.LANDSCAPE
    section.page_width = Inches(11.0)
    section.page_height = Inches(8.5)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)

    # Document Header Title
    title_p = doc.add_paragraph()
    title_run = title_p.add_run("Customer Segmentation & Marketing Analytics Report")
    title_run.font.name = "Calibri"
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(30, 58, 138)  # Navy #1E3A8A
    title_p.paragraph_format.space_after = Pt(2)

    # Subtitle / Metadata
    active_seg = filter_info.get("segment") if filter_info else "All"
    active_pri = filter_info.get("priority") if filter_info else "All"
    gen_time = datetime.now().strftime("%B %d, %Y at %H:%M:%S")

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run(
        f"Generated: {gen_time}  |  Segment Filter: {active_seg or 'All'}  |  "
        f"Priority Filter: {active_pri or 'All'}  |  Total Records: {len(customers)}"
    )
    sub_run.font.name = "Calibri"
    sub_run.font.size = Pt(9.5)
    sub_run.font.color.rgb = RGBColor(100, 116, 139)
    sub_p.paragraph_format.space_after = Pt(14)

    # Section 1: Executive KPI Summary
    stats = _get_summary_stats(customers)
    doc.add_heading("Executive Summary & Portfolio Overview", level=2)

    summary_table = doc.add_table(rows=2, cols=4)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    kpi_headers = ["Total Customers", "Total Revenue", "Average Customer Value", "Dominant Segment"]
    kpi_values = [
        f"{stats['total_customers']}",
        f"₹{stats['total_revenue']:,.2f}",
        f"₹{stats['average_spend']:,.2f}",
        f"{stats['top_segment']}",
    ]

    for i, (hdr, val) in enumerate(zip(kpi_headers, kpi_values)):
        cell_hdr = summary_table.cell(0, i)
        cell_hdr.text = hdr
        _set_cell_background(cell_hdr, "1E3A8A")
        _set_cell_margins(cell_hdr, top=120, bottom=120, left=150, right=150)
        p = cell_hdr.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(9)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

        cell_val = summary_table.cell(1, i)
        cell_val.text = val
        _set_cell_background(cell_val, "F1F5F9")
        _set_cell_margins(cell_val, top=120, bottom=120, left=150, right=150)
        p_val = cell_val.paragraphs[0]
        p_val.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p_val.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(13)
            r.font.bold = True
            r.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Section 2: Detailed Customer Data Table
    doc.add_heading("Detailed Customer RFM & Campaign Breakdown", level=2)

    col_names = [
        "Cust ID",
        "Segment",
        "Recency",
        "Freq",
        "Monetary (₹)",
        "RFM",
        "Total",
        "Priority",
        "Campaign",
        "Marketing Strategy & Recommended Action",
    ]

    # Available width = 11.0 - 1.2 = 9.8 inches
    col_widths_in = [
        Inches(0.7),
        Inches(1.1),
        Inches(0.65),
        Inches(0.55),
        Inches(1.0),
        Inches(0.6),
        Inches(0.5),
        Inches(0.7),
        Inches(1.7),
        Inches(2.3),
    ]

    data_table = doc.add_table(rows=len(customers) + 1, cols=len(col_names))
    data_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Style Header Row
    for col_idx, text in enumerate(col_names):
        cell = data_table.cell(0, col_idx)
        cell.width = col_widths_in[col_idx]
        cell.text = text
        _set_cell_background(cell, "1E3A8A")
        _set_cell_margins(cell, top=100, bottom=100, left=100, right=100)
        p = cell.paragraphs[0]
        if col_idx in (0, 2, 3, 5, 6, 7):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif col_idx == 4:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p.runs:
            r.font.name = "Calibri"
            r.font.size = Pt(8.5)
            r.font.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)

    # Style Data Rows
    for row_idx, c in enumerate(customers, start=1):
        strategy = c.get("marketing_strategy", "")
        action = c.get("recommended_action", "")
        combined_action = f"{strategy} — {action}" if strategy else action

        row_vals = [
            str(c.get("customer_id", "")),
            str(c.get("segment", "")),
            f"{c.get('recency', 0)}d",
            str(c.get("frequency", 0)),
            f"₹{float(c.get('monetary', 0.0) or 0.0):,.2f}",
            str(c.get("rfm_score", "")),
            str(c.get("rfm_total", "")),
            str(c.get("priority", "")),
            str(c.get("campaign", "")),
            combined_action,
        ]

        bg_color = "F8FAFC" if row_idx % 2 == 0 else "FFFFFF"

        for col_idx, val in enumerate(row_vals):
            cell = data_table.cell(row_idx, col_idx)
            cell.width = col_widths_in[col_idx]
            cell.text = val
            _set_cell_background(cell, bg_color)
            _set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            if col_idx in (0, 2, 3, 5, 6, 7):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif col_idx == 4:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                r.font.name = "Calibri"
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Section 3: AI Playbook Highlights
    doc.add_heading("Strategic Recommendations by Cohort", level=2)
    playbook_points = [
        ("Champions (VIPs)", "Deliver exclusive VIP early access, concierge onboarding, and bespoke loyalty rewards to safeguard 80%+ revenue share."),
        ("Loyal Customers", "Incentivize higher average basket sizes through personalized cross-sell recommendations and tiered threshold discounts."),
        ("At Risk Customers", "Trigger automated win-back workflows featuring time-limited 20% discount vouchers and re-engagement surveys."),
        ("Lost Customers", "Deploy low-cost batch reactivation broadcasts showcasing new arrivals and catalog updates; suppress costly ad retargeting."),
    ]
    for seg_name, strategy_text in playbook_points:
        p = doc.add_paragraph(style="List Bullet")
        bold_r = p.add_run(f"{seg_name}: ")
        bold_r.font.bold = True
        bold_r.font.name = "Calibri"
        bold_r.font.size = Pt(9.5)
        text_r = p.add_run(strategy_text)
        text_r.font.name = "Calibri"
        text_r.font.size = Pt(9.5)

    # Save to buffer
    output = io.BytesIO()
    doc.save(output)
    docx_bytes = output.getvalue()
    output.close()

    filename = build_report_filename("customer_segmentation_report", "docx", filter_info)
    return docx_bytes, filename


# ============================================================
# 5. JSON REPORT GENERATOR
# ============================================================

def generate_json_report(
    customers: List[Dict[str, Any]],
    filter_info: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Generate structured, pretty-printed JSON export.
    """
    stats = _get_summary_stats(customers)

    report_payload = {
        "report_title": "Customer Segmentation & AI Marketing Analytics Report",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "filter_criteria": {
            "segment": filter_info.get("segment") if filter_info else None,
            "priority": filter_info.get("priority") if filter_info else None,
            "search": filter_info.get("search") if filter_info else None,
        },
        "summary": {
            "total_customers": stats["total_customers"],
            "total_portfolio_revenue": round(stats["total_revenue"], 2),
            "average_customer_spend": round(stats["average_spend"], 2),
            "average_recency_days": round(stats["average_recency"], 1),
            "average_frequency_orders": round(stats["average_frequency"], 1),
            "top_segment": stats["top_segment"],
            "segment_breakdown": {
                seg: {
                    "count": count,
                    "revenue": round(stats["segment_revenue"].get(seg, 0.0), 2),
                    "percentage_of_customers": round((count / stats["total_customers"] * 100), 1) if stats["total_customers"] > 0 else 0.0,
                }
                for seg, count in stats["segment_counts"].items()
            },
        },
        "customers": [
            {
                "customer_id": c.get("customer_id"),
                "segment": c.get("segment"),
                "recency_days": c.get("recency"),
                "frequency_orders": c.get("frequency"),
                "monetary_spend": float(c.get("monetary", 0.0) or 0.0),
                "rfm_score": str(c.get("rfm_score", "")),
                "rfm_total": c.get("rfm_total"),
                "priority": c.get("priority"),
                "assigned_campaign": c.get("campaign"),
                "marketing_strategy": c.get("marketing_strategy"),
                "recommended_action": c.get("recommended_action"),
            }
            for c in customers
        ],
    }

    json_str = json.dumps(report_payload, indent=2, ensure_ascii=False)
    filename = build_report_filename("customer_segmentation_report", "json", filter_info)
    return json_str, filename
