import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import face_recognition
import json
import asyncio
import platform
import numpy as np
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class RecognizeFaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Recognize Face")
        self.root.geometry("800x600")

        # Load and set background image
        try:
            bg_image = Image.open("background.jpg")
            bg_image = bg_image.resize((800, 600), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_image)
            background_label = tk.Label(root, image=self.bg_photo)
            background_label.place(relwidth=1, relheight=1)
        except Exception:
            print("Background image not found, using default background")

        # GUI elements
        upload_button = tk.Button(root, text="Upload Image for Recognition", command=self.recognize_image, font=("Arial", 12), bg="lightgreen")
        upload_button.place(relx=0.35, rely=0.4, relwidth=0.3, relheight=0.1)

        self.result_label = tk.Label(root, text="", font=("Arial", 12), bg="white")
        self.result_label.place(relx=0.2, rely=0.55, relwidth=0.6, relheight=0.1)

        # JSON file path
        self.json_file = "employees.json"

    def recognize_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if not file_path:
            return

        try:
            # Load employees
            employees = self.load_employees()
            if not employees:
                self.result_label.config(text="No employees registered")
                return

            # Load and process image
            unknown_image = face_recognition.load_image_file(file_path)
            unknown_encodings = face_recognition.face_encodings(unknown_image)
            if len(unknown_encodings) == 0:
                self.result_label.config(text="No faces detected")
                return

            # Recognize faces
            recognized_ids = set()
            for unknown_encoding in unknown_encodings:
                for employee in employees:
                    known_encodings = [np.array(enc) for enc in employee["encodings"]]
                    matches = face_recognition.compare_faces(known_encodings, unknown_encoding)
                    if True in matches:
                        recognized_ids.add(employee["id"])
                        self.result_label.config(text=f"Recognized: {employee['name']} (ID: {employee['id']})")

            # Generate attendance report as PDF
            self.generate_attendance_report(employees, recognized_ids)

        except Exception as e:
            self.result_label.config(text=f"Error: {str(e)}")

    def load_employees(self):
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, "r") as f:
                    return json.load(f)
            return []
        except Exception:
            return []

    def generate_attendance_report(self, employees, recognized_ids):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        pdf_file = f"attendance_{timestamp}.pdf"

        try:
            # Create PDF
            doc = SimpleDocTemplate(pdf_file, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_style = ParagraphStyle(
                name='Title',
                fontSize=16,
                alignment=1,
                spaceAfter=20
            )
            elements.append(Paragraph(f"Attendance Report - {timestamp.replace('_', ' ')}", title_style))

            # Present employees table
            elements.append(Paragraph("Present Employees", styles['Heading2']))
            present_data = [["ID", "Name"]]
            present_count = 0
            for employee in employees:
                if employee["id"] in recognized_ids:
                    present_data.append([employee["id"], employee["name"]])
                    present_count += 1

            if present_count == 0:
                elements.append(Paragraph("No employees present", styles['Normal']))
            else:
                present_table = Table(present_data)
                present_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(present_table)

            elements.append(Spacer(1, 20))

            # Absent employees table
            elements.append(Paragraph("Absent Employees", styles['Heading2']))
            absent_data = [["ID", "Name"]]
            absent_count = 0
            for employee in employees:
                if employee["id"] not in recognized_ids:
                    absent_data.append([employee["id"], employee["name"]])
                    absent_count += 1

            if absent_count == 0:
                elements.append(Paragraph("No employees absent", styles['Normal']))
            else:
                absent_table = Table(absent_data)
                absent_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(absent_table)

            # Build PDF
            doc.build(elements)
            self.result_label.config(text=f"Attendance report saved as {pdf_file}")

        except Exception as e:
            self.result_label.config(text=f"Error generating PDF: {str(e)}")

async def main():
    root = tk.Tk()
    app = RecognizeFaceApp(root)
    root.mainloop()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())