# app/utils/receipt_generator.py

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

def generate_fee_receipt(student_name: str, amount: float, date_paid: str, receipt_number: str) -> BytesIO:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Title
    pdf.setTitle("TuitorIN - Fee Receipt")

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 60, "TuitorIN Tuition Center")

    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 80, "Official Fee Payment Receipt")

    # Line
    pdf.setStrokeColor(colors.black)
    pdf.line(50, height - 90, width - 50, height - 90)

    # Details Section
    y = height - 130
    line_height = 20

    def draw_label_value(label, value):
        nonlocal y
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(60, y, f"{label}:")
        pdf.setFont("Helvetica", 11)
        pdf.drawString(180, y, str(value))
        y -= line_height

    draw_label_value("Receipt Number", receipt_number)
    draw_label_value("Student Name", student_name)
    draw_label_value("Amount Paid (INR)", f"₹ {amount:.2f}")
    draw_label_value("Date of Payment", date_paid)
    draw_label_value("Generated On", datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Footer
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(60, 80, "Thank you for your payment. This is a system-generated receipt.")

    # Signature line
    pdf.line(width - 200, 100, width - 60, 100)
    pdf.drawString(width - 165, 85, "Authorized Signature")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return buffer
