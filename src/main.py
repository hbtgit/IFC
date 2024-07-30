'''**LICENSE**

Include a proper license file according to Mythic Systems' guidelines.

**Documentation Files**

Update any existing documentation files to include Mythic Systems' branding.

### 2. Add Branding to Code

Include a header with Mythic Systems branding in each Python file:

```python
# Mythic Systems Structural Analysis Tool
# (c) 2024 Mythic Systems
# All rights reserved.
'''
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend


from calculate import *
from read_methods import *

from widget import *
import ifcopenshell
import re
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Delaunay, ConvexHull
from tkinter import Tk, messagebox, Label, Checkbutton, BooleanVar, Entry
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
from fpdf import FPDF
import tkinter as tk
from tkinter import simpledialog
from Seismicwidget import create_seismic_input_widgets

def main():
    from gui import on_drop

    root = TkinterDnD.Tk()
    create_seismic_input_widgets(master=root)
    root.title("IFC to PDF Converter")
    root.geometry("400x500")

    global ice_load_entry, snow_load_entry, remove_zero_point_var, Imperial_var, roof_uplift_entry, roof_downpressure_entry, wind_force_entry, wall_height_entry

    label = Label(root, text="Drag and drop an IFC file here", width=40, height=10)
    label.grid(row=4, columnspan=2, pady=10)

    # Add a label and entry field for snow load per unit area
    Label(root, text="Snow Load (lbs/sq. ft.):").grid(row=5, column=0, sticky='w')
    snow_load_entry = Entry(root)
    snow_load_entry.grid(row=5, column=1, sticky='w')

    Label(root, text="Ice Load (lbs/sq. ft.):").grid(row=6, column=0, sticky='w')
    ice_load_entry = Entry(root)
    ice_load_entry.grid(row=6, column=1, sticky='w')

    remove_zero_point_var = BooleanVar(value=False)
    checkbox = Checkbutton(root, text="Remove (0,0,0) Point", variable=remove_zero_point_var)
    checkbox.grid(row=7, columnspan=2, sticky='w')

    Label(root, text="Roof Uplift Pressure (psf)").grid(row=8, column=0, sticky='w')
    roof_uplift_entry = Entry(root)
    roof_uplift_entry.grid(row=8, column=1, sticky='w')

    Label(root, text="Roof Downpressure (psf)").grid(row=9, column=0, sticky='w')
    roof_downpressure_entry = Entry(root)
    roof_downpressure_entry.grid(row=9, column=1, sticky='w')

    Label(root, text="Wind Force (lbs)").grid(row=10, column=0, sticky='w')
    wind_force_entry = Entry(root)
    wind_force_entry.grid(row=10, column=1, sticky='w')

    Label(root, text="Wall Height (feet)").grid(row=11, column=0, sticky='w')
    wall_height_entry = Entry(root)
    wall_height_entry.grid(row=11, column=1, sticky='w')

    root.drop_target_register(DND_FILES)
    
    values = {
        "snow_load_entry": snow_load_entry,
        "ice_load_entry": ice_load_entry,
        "roof_uplift_entry": roof_uplift_entry,
        "roof_downpressure_entry": roof_downpressure_entry,
        "wind_force_entry": wind_force_entry,
        "wall_height_entry": wall_height_entry,
        "remove_zero_point_var" : remove_zero_point_var,
        "site_class_entry": root.children['!entry'],
        "importance_factor_entry" : root.children['!entry2'],
        "spectral_response_acceleration_entry": root.children['!entry3'],
    }
    on_drop_md = lambda event: on_drop(event, values)
    root.dnd_bind('<<Drop>>', on_drop_md)

    root.mainloop()



if __name__ == '__main__':
    main()
