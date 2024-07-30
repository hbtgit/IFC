'''
**LICENSE**

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
#from main import *
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

#from gui import *
from calculate import *
from read_methods import *
#from report import *
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

def live_load_widget(floor_count):
    live_loads = []

    # Create the main window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Loop through each floor and get user input for live loads
    for floor in range(1, floor_count + 1):
        load_info = {}
        load_info['floor'] = floor
        
        # Prompt for percentage load type
        load_info['percentage_load'] = simpledialog.askfloat(
            f"Floor {floor}",
            f"Enter the live load as a percentage for floor {floor}:"
        )

        # Prompt for area load type
        load_info['area_load'] = simpledialog.askfloat(
            f"Floor {floor}",
            f"Enter the live load as an area (in square feet) for floor {floor}:"
        )

        live_loads.append(load_info)

    # Destroy the main window after getting inputs
    root.destroy()

    return live_loads
