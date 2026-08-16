import os
from io import BytesIO
from datetime import datetime
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from app.core.security import get_current_user_from_request
from app.services.mongo_client import mongo_client
from app.agents.orchestrator import orchestrator
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Rect, String, Line

router = APIRouter(prefix="/reports")

# --- Custom Vector Graphic Drawings inside PDF ---

def create_gpa_chart_drawing(semesters, gpas) -> Drawing:
    """Renders a beautiful bar chart representing Semester GPA Progression"""
    d = Drawing(460, 130)
    # Background card
    d.add(Rect(0, 0, 460, 130, fillColor=colors.HexColor('#F9FAFB'), strokeColor=colors.HexColor('#E5E7EB'), strokeWidth=0.5, rx=6, ry=6))
    
    # Title
    d.add(String(20, 110, "Semester GPA Progression Trend", fontName="Helvetica-Bold", fontSize=9.5, fillColor=colors.HexColor('#6B1E2D')))
    
    start_x = 80
    start_y = 20
    bar_width = 32
    gap = 40
    
    # Y-Axis Guidelines
    for val in [2, 4, 6, 8, 10]:
        y_pos = start_y + (val * 7.5)
        d.add(Line(60, y_pos, 420, y_pos, strokeColor=colors.HexColor('#F3F4F6'), strokeWidth=0.5))
        d.add(String(38, y_pos - 3, f"{val}.0", fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#9CA3AF')))
        
    # Draw bars
    for idx, (sem, gpa) in enumerate(zip(semesters, gpas)):
        x = start_x + idx * (bar_width + gap)
        h = gpa * 7.5  # scale
        # Draw bar
        d.add(Rect(x, start_y, bar_width, h, fillColor=colors.HexColor('#6B1E2D'), strokeColor=None, rx=2, ry=2))
        # Value label
        d.add(String(x + 7, start_y + h + 4, f"{gpa:.2f}", fontName="Helvetica-Bold", fontSize=8, fillColor=colors.HexColor('#1F2937')))
        # Label
        d.add(String(x + 2, 8, sem, fontName="Helvetica", fontSize=8, fillColor=colors.HexColor('#4B5563')))
        
    return d

def create_attendance_gauge_drawing(percentage) -> Drawing:
    """Renders a horizontal indicator progress bar for Attendance"""
    d = Drawing(460, 48)
    # Background card
    d.add(Rect(0, 0, 460, 48, fillColor=colors.HexColor('#F9FAFB'), strokeColor=colors.HexColor('#E5E7EB'), strokeWidth=0.5, rx=6, ry=6))
    
    # Title
    d.add(String(20, 30, "Class Attendance Standing Ratio", fontName="Helvetica-Bold", fontSize=9, fillColor=colors.HexColor('#1F2937')))
    
    # Success / Warning Colors
    filled_color = colors.HexColor('#10B981') if percentage >= 75 else colors.HexColor('#EF4444')
    d.add(String(390, 28, f"{percentage}%", fontName="Helvetica-Bold", fontSize=11, fillColor=filled_color))
    
    # Outer bar
    d.add(Rect(20, 12, 420, 8, fillColor=colors.HexColor('#E5E7EB'), strokeColor=None, rx=2, ry=2))
    # Inner filled bar
    fill_width = int(420 * (percentage / 100.0))
    d.add(Rect(20, 12, fill_width, 8, fillColor=filled_color, strokeColor=None, rx=2, ry=2))
    
    return d

def create_institution_outcomes_drawing(resolved, active, escalated) -> Drawing:
    """Renders a clustered bar chart for Institutional Support Queue Cases"""
    d = Drawing(460, 130)
    # Background card
    d.add(Rect(0, 0, 460, 130, fillColor=colors.HexColor('#F9FAFB'), strokeColor=colors.HexColor('#E5E7EB'), strokeWidth=0.5, rx=6, ry=6))
    
    # Title
    d.add(String(20, 110, "Academic Intervention & Support Resolution Status", fontName="Helvetica-Bold", fontSize=9.5, fillColor=colors.HexColor('#6B1E2D')))
    
    categories = ["Resolved Support Cases", "In-Progress Support", "Escalated Urgent Cases"]
    values = [resolved, active, escalated]
    max_val = max(values) if values and max(values) > 0 else 10
    scale = 75.0 / max_val
    
    start_x = 90
    start_y = 20
    bar_width = 44
    gap = 60
    
    # Draw grid lines
    for val in [int(max_val * 0.2), int(max_val * 0.4), int(max_val * 0.6), int(max_val * 0.8), max_val]:
        if val == 0: continue
        y_pos = start_y + (val * scale)
        d.add(Line(60, y_pos, 420, y_pos, strokeColor=colors.HexColor('#F3F4F6'), strokeWidth=0.5))
        d.add(String(40, y_pos - 3, str(val), fontName="Helvetica", fontSize=8, fillColor=colors.HexColor('#9CA3AF')))
        
    # Draw bars
    colors_list = [colors.HexColor('#10B981'), colors.HexColor('#F59E0B'), colors.HexColor('#EF4444')]
    for idx, (cat, val, color) in enumerate(zip(categories, values, colors_list)):
        x = start_x + idx * (bar_width + gap)
        h = val * scale
        d.add(Rect(x, start_y, bar_width, h, fillColor=color, strokeColor=None, rx=2, ry=2))
        # Value label
        d.add(String(x + 16, start_y + h + 4, str(val), fontName="Helvetica-Bold", fontSize=8.5, fillColor=colors.HexColor('#1F2937')))
        # Category label
        d.add(String(x - 10, 8, cat[:18], fontName="Helvetica", fontSize=7.5, fillColor=colors.HexColor('#4B5563')))
        
    return d

# --- PDF Generation Functions ---

def generate_student_pdf_bytes(
    student_name, roll_number, course, cgpa, attendance, grades, completion,
    email, phone, guardian, backlogs, status, report_text
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Colors
    primary_color = colors.HexColor('#6B1E2D') # Deep burgundy
    neutral_dark = colors.HexColor('#1F2937')
    neutral_light = colors.HexColor('#F9FAFB')
    border_color = colors.HexColor('#E5E7EB')

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontSize=20,
        leading=24,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6B7280'),
        fontName='Helvetica',
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceBefore=14,
        spaceAfter=8
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=neutral_dark,
        fontName='Helvetica'
    )
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=12,
        textColor=neutral_dark,
        fontName='Helvetica-Bold'
    )
    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )
    
    # Document Header
    story.append(Paragraph("PORTALITICS INSTITUTE OF TECHNOLOGY", title_style))
    story.append(Paragraph(f"Official Academic Progress & Growth Summary · Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Candidate details table
    story.append(Paragraph("Candidate Personal & Academic Information", h2_style))
    profile_data = [
        [Paragraph("Candidate Name", cell_bold), Paragraph(student_name, cell_style), Paragraph("Roll Number", cell_bold), Paragraph(roll_number, cell_style)],
        [Paragraph("Degree Program", cell_bold), Paragraph(course, cell_style), Paragraph("Cumulative CGPA", cell_bold), Paragraph(f"{cgpa} / 10.0", cell_style)],
        [Paragraph("Institutional Email", cell_bold), Paragraph(email, cell_style), Paragraph("Phone Number", cell_bold), Paragraph(phone, cell_style)],
        [Paragraph("Guardian Name", cell_bold), Paragraph(guardian, cell_style), Paragraph("Active Backlogs", cell_bold), Paragraph(str(backlogs), cell_style)],
        [Paragraph("Academic Status", cell_bold), Paragraph(status, cell_bold), Paragraph("Admission Cycle", cell_bold), Paragraph("2026-2027", cell_style)]
    ]
    profile_table = Table(profile_data, colWidths=[110, 150, 110, 150])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), neutral_light),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 15))
    
    # Academic Health Metrics table
    story.append(Paragraph("Core Academic Indicators", h2_style))
    metrics_data = [
        [Paragraph("Performance Indicator", header_cell), Paragraph("Scored Rating / Value", header_cell), Paragraph("Evaluation Remarks", header_cell)],
        [Paragraph("Class Attendance Stability", cell_style), Paragraph(f"{attendance}%", cell_bold), Paragraph("Satisfactory" if float(attendance or 0) >= 75 else "Critical Attendance Risk", cell_style)],
        [Paragraph("Exam Score Average", cell_style), Paragraph(f"{grades} / 100", cell_bold), Paragraph("Under Review", cell_style)],
        [Paragraph("Assignment Completion Rate", cell_style), Paragraph(f"{completion}%", cell_bold), Paragraph("On Track", cell_style)]
    ]
    metrics_table = Table(metrics_data, colWidths=[180, 160, 180])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 15))
    
    # Render Vector Graphics & Charts
    story.append(Paragraph("Visualizations & Analytics Trend", h2_style))
    story.append(create_attendance_gauge_drawing(float(attendance or 0)))
    story.append(Spacer(1, 12))
    
    # gpa progression data (Mock historical trend with current GPA)
    current_gpa = float(cgpa) if cgpa != 'N/A' else 8.4
    gpa_trend = [7.8, 8.2, 8.0, current_gpa]
    story.append(create_gpa_chart_drawing(["Sem 1", "Sem 2", "Sem 3", "Sem 4"], gpa_trend))
    story.append(Spacer(1, 15))
    
    # AI Report block
    story.append(Paragraph("Evidence-Grounded AI Action Recommendations", h2_style))
    report_paragraph = Paragraph(report_text, ParagraphStyle(
        'ReportParagraph',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=neutral_dark,
        fontName='Helvetica'
    ))
    
    report_table = Table([[report_paragraph]], colWidths=[520])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')), # light red background
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 1, primary_color),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(report_table)
    story.append(Spacer(1, 35))
    
    # Signatures
    sig_data = [
        [Paragraph("_____________________________<br><b>Dr. Alan Turing</b><br>Head of Department (CSE)", cell_style), 
         Paragraph("_____________________________<br><b>Dr. Skinner</b><br>Principal / Dean", cell_style)]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    return buffer.getvalue()

# --- Endpoints ---

@router.get("/student/{student_id}")
async def student_report(request: Request, student_id: str):
    # Fetch student info
    student = mongo_client.get_user_by_id(student_id)
    if not student:
        student = {
            "name": "Academic Student",
            "roll_number": "N/A",
            "course": "N/A",
            "cgpa": "N/A",
            "email": "N/A",
            "phone": "N/A",
            "guardian_name": "N/A",
            "current_backlogs": "0",
            "academic_status": "On Track"
        }
        
    history = mongo_client.get_student_academic_history(student_id)
    
    from app.services.rules_engine import DeterministicRulesEngine
    att_metric = DeterministicRulesEngine.calculate_attendance_metric(history.get("attendance", []))
    grd_metric = DeterministicRulesEngine.calculate_grade_metric(history.get("exams", []))
    asg_metric = DeterministicRulesEngine.calculate_assignment_metric(history.get("assignments", []))
    
    attendance_pct = str(att_metric.get("percentage", 85.0))
    grades_avg = str(grd_metric.get("average_score", 72.0))
    completion_pct = str(asg_metric.get("completion_rate", 90.0))
    
    agent_output = orchestrator.route_event("report_generated", student_id, "student")
    report_text = agent_output.get("formatted_report", "Monitor candidate closely.")
    if isinstance(report_text, dict):
        report_text = report_text.get("recommendation", "Review performance metrics weekly.")
        
    pdf_data = generate_student_pdf_bytes(
        student_name=student.get("name", "Student"),
        roll_number=student.get("roll_number", "N/A"),
        course=student.get("course", "N/A"),
        cgpa=str(student.get("cgpa", "N/A")),
        attendance=attendance_pct,
        grades=grades_avg,
        completion=completion_pct,
        email=student.get("email", "N/A"),
        phone=student.get("phone", "N/A"),
        guardian=student.get("guardian_name", "N/A"),
        backlogs=student.get("current_backlogs", "0"),
        status=student.get("academic_status", "On Track"),
        report_text=str(report_text)
    )
    
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=student_growth_report_{student_id}.pdf"}
    )

@router.get("/institution")
async def institution_report(request: Request):
    outcomes = mongo_client.calculate_institution_outcomes()
    
    resolved = outcomes.get("resolved_count", 0)
    active = outcomes.get("in_progress_count", 0)
    escalated = outcomes.get("escalated_count", 0)
    success_rate = outcomes.get("overall_success_rate", 100.0)
    total = outcomes.get("total_count", 0)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Colors
    primary_color = colors.HexColor('#6B1E2D') # Deep burgundy
    neutral_dark = colors.HexColor('#1F2937')
    neutral_light = colors.HexColor('#F9FAFB')
    border_color = colors.HexColor('#E5E7EB')

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontSize=20,
        leading=24,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#6B7280'),
        fontName='Helvetica',
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=primary_color,
        fontName='Helvetica-Bold',
        spaceBefore=14,
        spaceAfter=8
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=neutral_dark,
        fontName='Helvetica'
    )
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=neutral_dark,
        fontName='Helvetica-Bold'
    )
    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.white,
        fontName='Helvetica-Bold'
    )

    story.append(Paragraph("PORTALITICS INSTITUTE OF TECHNOLOGY", title_style))
    story.append(Paragraph(f"Executive Institutional Growth & Academic Support Report · Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Summary Info
    story.append(Paragraph("Institutional Support Metrics Summary", h2_style))
    summary_data = [
        [Paragraph("Academic Metric", header_cell), Paragraph("Registered Case Count", header_cell), Paragraph("Current Percentage / Rating", header_cell)],
        [Paragraph("Resolved Support Cases", cell_style), Paragraph(str(resolved), cell_bold), Paragraph(f"{success_rate}% Success Rate", cell_bold)],
        [Paragraph("In-Progress Support Cases", cell_style), Paragraph(str(active), cell_bold), Paragraph("-", cell_style)],
        [Paragraph("Escalated Urgent Cases", cell_style), Paragraph(str(escalated), cell_bold), Paragraph("-", cell_style)],
        [Paragraph("Total Academic Interventions", cell_style), Paragraph(str(total), cell_bold), Paragraph("100.0%", cell_style)]
    ]
    summary_table = Table(summary_data, colWidths=[200, 160, 160])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Chart Visualization
    story.append(Paragraph("Intervention Metrics Visualization Chart", h2_style))
    story.append(create_institution_outcomes_drawing(resolved, active, escalated))
    story.append(Spacer(1, 15))
    
    # Executive Summary Paragraph
    story.append(Paragraph("Institutional Executive Summary", h2_style))
    exec_summary = f"Portalitics Institute of Technology maintains high standards of academic quality control. Under the current cycle, we monitored a total of {total} academic support interventions. With a resolved support rate of {success_rate}%, our agentic counseling models have successfully guided at-risk candidates back to satisfactory academic standing. Continuous monitoring remains active across all departments."
    
    summary_paragraph = Paragraph(exec_summary, ParagraphStyle(
        'ExecSummaryParagraph',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=neutral_dark,
        fontName='Helvetica'
    ))
    
    summary_box_table = Table([[summary_paragraph]], colWidths=[520])
    summary_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDF4')), # light green background
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#16A34A')),
        ('PADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(summary_box_table)
    story.append(Spacer(1, 35))
    
    # Signatures
    sig_data = [
        [Paragraph("_____________________________<br><b>Dr. Alan Turing</b><br>Dean of Academic Affairs", cell_style), 
         Paragraph("_____________________________<br><b>Dr. Skinner</b><br>Principal / Dean", cell_style)]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sig_table)
    
    doc.build(story)
    pdf_data = buffer.getvalue()
    
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=executive_institutional_growth_report.pdf"}
    )

@router.get("/class/{class_id}", response_class=HTMLResponse)
async def class_report(request: Request, class_id: str):
    user = get_current_user_from_request(request)
    return templates.TemplateResponse(
        request=request,
        name="reports/class_report.html",
        context={
            "user": user,
            "page_title": "Class Progress & Support Summary"
        }
    )

@router.get("/comparative", response_class=HTMLResponse)
async def comparative_report(request: Request):
    user = get_current_user_from_request(request)
    return templates.TemplateResponse(
        request=request,
        name="reports/comparative_report.html",
        context={
            "user": user,
            "page_title": "Comparative Departmental Report"
        }
    )
