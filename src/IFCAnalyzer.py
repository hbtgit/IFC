import ifcopenshell
import numpy as np
import os
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

class IFCAnalyzer:
    def __init__(self, ifc_path):
        self.ifc_path = ifc_path
        self.ifc_file = None

    def load_ifc_file(self):
        try:
            self.ifc_file = ifcopenshell.open(self.ifc_path)
            print(f"Successfully loaded IFC file: {self.ifc_path}")
        except Exception as e:
            print(f"Error loading IFC file: {e}")
            raise

    def extract_element_counts(self):
        """Extract counts of specific elements from the IFC file."""
        if not self.ifc_file:
            raise ValueError("IFC file is not loaded.")
        
        element_counts = {
            'IfcBeam': len(self.ifc_file.by_type('IfcBeam')),
            'IfcColumn': len(self.ifc_file.by_type('IfcColumn'))
        }
        return element_counts

    def calculate_total_weight(self):
        """Calculate total weight from the IFC file."""
        if not self.ifc_file:
            raise ValueError("IFC file is not loaded.")
        
        total_weight = sum(quantity.WeightValue for quantity in self.ifc_file.by_type('IfcQuantityWeight') if quantity)
        return round(total_weight, 2)

class Application(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("IFC Analyzer")
        self.geometry("400x300")
        self.create_widgets()
        self.register_drop_target()

    def create_widgets(self):
        self.result_label = ctk.CTkLabel(self, text="Drag and drop an IFC file here")
        self.result_label.pack(pady=20)

        self.analyze_button = ctk.CTkButton(self, text="Analyze", command=self.analyze_ifc)
        self.analyze_button.pack(pady=10)

        self.file_path = ""

    def register_drop_target(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        dropped_file = event.data.replace("{","").replace("}", "")
        dropped_file = os.path.normpath(dropped_file)
        print(f"Dropped file data: {dropped_file}")  # Debugging line
        
        # Debugging: print the full event data
        print(f"Full event data: {event.data}")
        
        if dropped_file.lower().endswith('.ifc'):
            self.file_path = dropped_file
            self.result_label.configure(text=f"Dropped file: {self.file_path}")
        else:
            messagebox.showerror("Error", "Please drop a valid IFC file.")

    # def open_file_dialog(self):
    #     file_path = filedialog.askopenfilename(filetypes=[("IFC files", "*.ifc")])
    #     if file_path:
    #         self.file_path = file_path
    #         self.result_label.configure(text=f"Selected file: {self.file_path}")

    def analyze_ifc(self):
        if not self.file_path:
            messagebox.showerror("Error", "Please drag and drop a valid IFC file.")
            return
        
        analyzer = IFCAnalyzer(self.file_path)
        try:
            analyzer.load_ifc_file()
            counts = analyzer.extract_element_counts()
            total_weight = analyzer.calculate_total_weight()
            result_text = f"Counts: {counts}\nTotal Weight: {total_weight} kg"
            self.result_label.configure(text=result_text)
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
