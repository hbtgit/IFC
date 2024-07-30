import tkinter as tk
from tkinter import BooleanVar, Label, Entry, Checkbutton
from tkinterdnd2 import TkinterDnD, DND_FILES


import tkinter as tk

def calculate_seismic_load(site_class_entry, importance_factor_entry, spectral_response_acceleration_entry):
    # Retrieve user input
    site_class = float(site_class_entry.get().strip() or "0")  # Get value from Entry widget
    importance_factor = float(importance_factor_entry.get().strip() or "0")
    spectral_response_acceleration = float(spectral_response_acceleration_entry.get().strip() or "0")

    # Calculate seismic load
    seismic_load = compute_seismic_load(site_class, importance_factor, spectral_response_acceleration)
    print(f"Seismic Load: {seismic_load} kN")


def compute_seismic_load(site_class, importance_factor, spectral_response_acceleration):
    # site_class is now a float, so we don't need to call .get()
    # You might need a conversion or validation based on what you expect

    # Assuming amplification_factors is a dictionary of floats
    amplification_factors = {
        # Example data; replace with actual values
        0.0: 1.0,  # This is a placeholder; replace with your actual values
        1.0: 1.5,
        2.0: 2.0,
    }
    
    # Use the float value to get the amplification factor
    amplification_factor = amplification_factors.get(site_class, 1.0)  # Default to 1.0 if not found

    # Perform the computation (assuming you have other code here)
    # For example:
    seismic_load = (importance_factor * spectral_response_acceleration * amplification_factor)

    return seismic_load


def create_seismic_input_widgets(master):
    # Create and place widgets
    site_class_label = tk.Label(master, text="Site Class")
    site_class_label.grid(row=0, column=0)
    site_class_entry = tk.Entry(master)
    site_class_entry.grid(row=0, column=1)

    importance_factor_label = tk.Label(master, text="Importance Factor")
    importance_factor_label.grid(row=1, column=0)
    importance_factor_entry = tk.Entry(master)
    importance_factor_entry.grid(row=1, column=1)

    spectral_response_acceleration_label = tk.Label(master, text="Spectral Response Acceleration")
    spectral_response_acceleration_label.grid(row=2, column=0)
    spectral_response_acceleration_entry = tk.Entry(master)
    spectral_response_acceleration_entry.grid(row=2, column=1)

    calculate_button = tk.Button(master, text="Calculate Seismic Load", 
                                 command=lambda: calculate_seismic_load(site_class_entry, 
                                                                        importance_factor_entry, 
                                                                        spectral_response_acceleration_entry))
    calculate_button.grid(row=3, columnspan=2)

    return master
