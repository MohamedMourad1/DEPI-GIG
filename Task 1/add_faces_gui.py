import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import face_recognition
import json
import asyncio
import platform
import numpy as np
import os

class AddEmployeeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Add Employee")
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
        tk.Label(root, text="Employee Name:", font=("Arial", 12), bg="white").place(relx=0.2, rely=0.3, relwidth=0.2, relheight=0.05)
        self.name_entry = tk.Entry(root, font=("Arial", 12))
        self.name_entry.place(relx=0.4, rely=0.3, relwidth=0.4, relheight=0.05)

        tk.Label(root, text="Employee ID:", font=("Arial", 12), bg="white").place(relx=0.2, rely=0.4, relwidth=0.2, relheight=0.05)
        self.id_entry = tk.Entry(root, font=("Arial", 12))
        self.id_entry.place(relx=0.4, rely=0.4, relwidth=0.4, relheight=0.05)

        upload_button = tk.Button(root, text="Upload Images", command=self.upload_images, font=("Arial", 12), bg="lightblue")
        upload_button.place(relx=0.35, rely=0.5, relwidth=0.3, relheight=0.1)

        # JSON file path
        self.json_file = "employees.json"

    def upload_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if not file_paths:
            return

        name = self.name_entry.get().strip()
        employee_id = self.id_entry.get().strip()

        if not name or not employee_id:
            messagebox.showerror("Error", "Please enter both name and employee ID")
            return

        if not employee_id.isdigit():
            messagebox.showerror("Error", "Employee ID must be a number")
            return

        # Load existing employees
        employees = self.load_employees()
        if any(emp["id"] == employee_id for emp in employees):
            messagebox.showerror("Error", "Employee ID already exists")
            return

        encodings = []
        for file_path in file_paths:
            try:
                image = face_recognition.load_image_file(file_path)
                enc = face_recognition.face_encodings(image)
                if len(enc) > 0:
                    encodings.append(enc[0].tolist())  # Convert numpy array to list for JSON
                else:
                    messagebox.showwarning("Warning", f"No face detected in {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process {file_path}: {str(e)}")

        if not encodings:
            messagebox.showerror("Error", "No valid faces detected in any image")
            return

        # Add new employee to JSON
        employees.append({
            "id": employee_id,
            "name": name,
            "encodings": encodings
        })

        self.save_employees(employees)
        messagebox.showinfo("Success", f"Employee {name} (ID: {employee_id}) added with {len(encodings)} images")

    def load_employees(self):
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, "r") as f:
                    return json.load(f)
            return []
        except Exception:
            return []

    def save_employees(self, employees):
        try:
            with open(self.json_file, "w") as f:
                json.dump(employees, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save employees: {str(e)}")

async def main():
    root = tk.Tk()
    app = AddEmployeeApp(root)
    root.mainloop()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())