import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import ifcopenshell
import re
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Delaunay, ConvexHull
from tkinter import Tk, messagebox, Label, Checkbutton, BooleanVar, Entry
from tkinterdnd2 import TkinterDnD, DND_FILES, DND_ALL
import os
from fpdf import FPDF
import tkinter as tk
from tkinter import simpledialog
import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES
from Seismicwidget import create_seismic_input_widgets
from PIL import Image
from CTkMessagebox import CTkMessagebox


def explore_ifc_properties(ifc_path):
    import ifcopenshell
    ifc_file = ifcopenshell.open(ifc_path)

    for element in ifc_file.by_type('IfcElement'):
        material_set = element.IsDefinedBy
        if material_set:
            for definition in material_set:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_set = definition.RelatingPropertyDefinition
                    if property_set.is_a('IfcPropertySet'):
                        print(f"Element: {element.GlobalId}")
                        for prop in property_set.HasProperties:
                            if prop.is_a('IfcPropertySingleValue'):
                                print(f"Property Name: {prop.Name}, Value: {prop.NominalValue}")


def extract_element_counts(ifc_path):
    """Extracts the counts of specific elements from an IFC file."""
    ifc_file = ifcopenshell.open(ifc_path)
    element_counts = {
        'IfcBeam': len(ifc_file.by_type('IfcBeam')),
        'IfcColumn': len(ifc_file.by_type('IfcColumn'))
    }
    return element_counts


def extract_ifc_data(ifc_path):
    """Extracts IFC data and calculates the total weight from an IFC file using ifcopenshell."""
    total_weight = 0.0
    ifc_file = ifcopenshell.open(ifc_path)
    for quantity in ifc_file.by_type('IfcQuantityWeight'):
        if quantity:
            total_weight += quantity.WeightValue
    return round(total_weight, 2)

def extract_section_types(ifc_path):
    """Extracts unique section types from an IFC file using ifcopenshell."""
    section_types = set()
    ifc_file = ifcopenshell.open(ifc_path)
    for element in ifc_file.by_type('IfcStructuralProfileProperties'):
        section_types.add(element.ProfileName)
    for element in ifc_file.by_type('IfcCShapeProfileDef'):
        section_types.add(element.ProfileName)
    return section_types

def extract_Aux_data(ifc_path):
    """Extracts auxiliary data (section counts and weights) from an IFC file using ifcopenshell."""
    Aux_data = {}
    ifc_file = ifcopenshell.open(ifc_path)
    for element in ifc_file.by_type('IfcStructuralProfileProperties'):
        section_name = element.ProfileName
        if section_name not in Aux_data:
            Aux_data[section_name] = {'count': 0, 'total_weight': 0.0}
        Aux_data[section_name]['count'] += 1
    for element in ifc_file.by_type('IfcQuantityWeight'):
        section_name = element.Name
        if section_name in Aux_data:
            Aux_data[section_name]['total_weight'] += element.WeightValue
    for key in Aux_data:
        Aux_data[key]['total_weight'] = round(Aux_data[key]['total_weight'], 2)
    total_stud_count = sum(data['count'] for data in Aux_data.values())
    return total_stud_count, Aux_data

def extract_floor_data(ifc_path):
    """Extracts floor data to determine the number of stories in the building using ifcopenshell."""
    ifc_file = ifcopenshell.open(ifc_path)
    floors = len(ifc_file.by_type('IfcBuildingStorey'))
    return floors


def extract_forces_moments(ifc_path):
    """Extracts total forces and moments from an IFC file."""
    forces = {}
    moments = {}

    # Load the IFC file
    ifc_file = ifcopenshell.open(ifc_path)
    
    # Check the schema of the IFC file
    schema = ifc_file.schema

    # Define patterns based on schema
    if schema == "IFC2X3":
        # If the schema is IFC2X3, handle accordingly
        print("Using schema IFC2X3")
        # You may need to use different entity names or extraction methods
        # Currently, there's no direct equivalent for IfcForceVector and IfcMomentVector in IFC2X3
        # Hence, we would need to understand the exact requirement and map them accordingly
        return forces, moments
    elif schema.startswith("IFC4"):
        # If the schema is IFC4 or any of its derivatives
        print("Using schema IFC4")
        force_pattern = re.compile(r'IFCFORCEVECTOR\(([^,]+),([^,]+),([^,]+)\);')
        moment_pattern = re.compile(r'IFCMOMENTVECTOR\(([^,]+),([^,]+),([^,]+)\);')
        floor_pattern = re.compile(r'#\d+=\s*IFCBUILDINGSTOREY\(([^,]+),')

        current_floor = "Foundation"

        for line in open(ifc_path, 'r'):
            floor_match = floor_pattern.search(line)
            if floor_match:
                current_floor = floor_match.group(1).strip("'")
                if current_floor not in forces:
                    forces[current_floor] = np.zeros(3)
                    moments[current_floor] = np.zeros(3)
            force_match = force_pattern.search(line)
            if force_match:
                force_values = list(map(float, force_match.groups()))
                forces[current_floor] += np.array(force_values)
            moment_match = moment_pattern.search(line)
            if moment_match:
                moment_values = list(map(float, moment_match.groups()))
                moments[current_floor] += np.array(moment_values)

        return forces, moments
    else:
        raise ValueError(f"Unsupported IFC schema: {schema}")

def extract_roof_pressures(ifc_path):
    """Extracts roof uplift and downpressure from an IFC file."""
    uplift_pressures = {}
    down_pressures = {}

    # Load the IFC file
    ifc_file = ifcopenshell.open(ifc_path)

    for element in ifc_file.by_type('IfcRoof'):
        material_set = element.IsDefinedBy
        if material_set:
            for definition in material_set:
                if definition.is_a('IfcRelDefinesByProperties'):
                    property_set = definition.RelatingPropertyDefinition
                    if property_set.is_a('IfcPropertySet'):
                        for prop in property_set.HasProperties:
                            if prop.is_a('IfcPropertySingleValue'):
                                if 'UpliftPressure' in prop.Name:
                                    uplift_pressures[element.GlobalId] = prop.NominalValue.wrappedValue
                                if 'DownPressure' in prop.Name:
                                    down_pressures[element.GlobalId] = prop.NominalValue.wrappedValue

    return uplift_pressures, down_pressures

def parse_ifc_file(ifc_path, zero_val=None):
    """Parses the IFC file to extract 3D coordinates using ifcopenshell."""
    remove_zero_point_var = BooleanVar(value=False)
    if zero_val is not None:
        remove_zero_point_var = zero_val
    coordinates = []
    ifc_file = ifcopenshell.open(ifc_path)
    for point in ifc_file.by_type('IfcCartesianPoint'):
        coord_tuple = tuple(point.Coordinates)
        if len(coord_tuple) == 3 and (not remove_zero_point_var.get() or coord_tuple != (0.0, 0.0, 0.0)):
            coordinates.append(tuple(round(x / 12, 2) for x in coord_tuple))
    return coordinates

def calculate_dead_load_with_live_load(ifc_file, live_loads, roof_area, snow_load_per_unit_area, ice_load_per_unit_area):
    model = ifcopenshell.open(ifc_file)

    total_dead_load = 0.0
    total_live_load = 0.0

    for element in model.by_type('IfcElementQuantity'):
        for quantity in element.Quantities:
            if quantity.is_a('IfcQuantityWeight'):
                if 'Dead Load' in quantity.Name or 'DeadLoad' in quantity.Name or 'Gross Weight' in quantity.Name or 'GrossWeight' in quantity.Name:
                    total_dead_load += quantity.WeightValue

    for load in live_loads:
        area_load = load['area_load']
        if area_load:
            total_live_load += area_load * load['percentage_load'] / 100

    # Calculate snow load
    total_snow_load = calculate_snow_load(roof_area, snow_load_per_unit_area)

    # Calculate ice load
    total_ice_load = calculate_ice_load(roof_area, ice_load_per_unit_area)

    return total_dead_load, total_live_load, total_snow_load, total_ice_load

def calculate_beam_column_weight(ifc_path):
    """Calculate the total weight of beams and columns using 'Gross Weight' or 'IFCQUANTITYLENGTH'."""
    total_beam_weight = 0.0
    total_column_weight = 0.0

    ifc_file = ifcopenshell.open(ifc_path)

    # Helper function to get weight value
    def get_weight_value(element, attribute_names):
        for attr_name in attribute_names:
            attr_value = getattr(element, attr_name, None)
            if attr_value:
                return attr_value
        return 0.0

    # Define attribute names to check for weight values
    weight_attributes = ['GrossWeight', 'WeightValue']

    # Iterate over beams
    for beam in ifc_file.by_type('IfcBeam'):
        for quantity in beam.IsDefinedBy:
            if quantity.is_a('IfcRelDefinesByProperties'):
                prop_set = quantity.RelatingPropertyDefinition
                if prop_set.is_a('IfcElementQuantity'):
                    for quantity in prop_set.Quantities:
                        if quantity.is_a('IfcQuantityWeight') or quantity.Name == 'Gross Weight':
                            total_beam_weight += get_weight_value(quantity, weight_attributes)

    # Iterate over columns
    for column in ifc_file.by_type('IfcColumn'):
        for quantity in column.IsDefinedBy:
            if quantity.is_a('IfcRelDefinesByProperties'):
                prop_set = quantity.RelatingPropertyDefinition
                if prop_set.is_a('IfcElementQuantity'):
                    for quantity in prop_set.Quantities:
                        if quantity.is_a('IfcQuantityWeight') or quantity.Name == 'Gross Weight':
                            total_column_weight += get_weight_value(quantity, weight_attributes)
    total_weight = total_beam_weight + total_column_weight
    return round(total_weight, 2)
    # return round(total_beam_weight, 2), round(total_column_weight, 2)

def calculate_area_from_coords(coord_list):
    coords = np.array(coord_list)

    def triangulation_area(points):
        if len(points) < 3:
            return 0.0
        tri = Delaunay(points)
        area = 0.0
        for simplex in tri.simplices:
            pts = points[simplex]
            a = np.linalg.norm(pts[0] - pts[1])
            b = np.linalg.norm(pts[1] - pts[2])
            c = np.linalg.norm(pts[2] - pts[0])
            s = (a + b + c) / 2
            area += np.sqrt(s * (s - a) * (s - b) * (s - c))
        return round(area, 1)

    area_xy = triangulation_area(coords[:, [0, 1]])
    area_yz = triangulation_area(coords[:, [1, 2]])
    area_xz = triangulation_area(coords[:, [0, 2]])

    return area_xy, area_yz, area_xz

def calculate_perimeter(coords):
    if len(coords) < 3:
        return 0.0
    hull = ConvexHull(coords)
    perimeter = 0.0
    for simplex in hull.simplices:
        p1 = np.array(coords[simplex[0]])
        p2 = np.array(coords[simplex[1]])
        perimeter += np.linalg.norm(p1 - p2)
    return round(perimeter / 12, 1)

def calculate_footing_perimeter(coords):
    if len(coords) < 3:
        return []

    hull = ConvexHull(coords)
    perimeter_coords = [coords[vertex] for vertex in hull.vertices]

    return perimeter_coords

def calculate_wind_loads_and_present(wind_force, building_height, roof_perimeter, ifc_path):
    """
    Calculate and present wind loads on the building.
    """
    # Calculate wind pressure (force per unit length)
    wind_pressure = wind_force / roof_perimeter

    # Calculate wall moments due to wind force
    wall_moment = wind_pressure * building_height

    # Prepare the results
    results = {
        'Wind Force': wind_force,
        'Building Height': building_height,
        'Roof Perimeter': roof_perimeter,
        'Wind Pressure': round(wind_pressure, 2),
        'Wall Moment': round(wall_moment, 2)
    }

    # Print the results in a structured format
    print("Wind Load Calculation Results:")
    print(f"Wind Force: {results['Wind Force']} lbs")
    print(f"Building Height: {results['Building Height']} feet")
    print(f"Roof Perimeter: {results['Roof Perimeter']} feet")
    print(f"Wind Pressure: {results['Wind Pressure']} lbs/ft")
    print(f"Wall Moment: {results['Wall Moment']} ft-lbs")

    return results

def calculate_linear_load(perimeter, uplift_pressures, down_pressures):
    net_pressure = down_pressures - uplift_pressures
    linear_load = net_pressure * perimeter
    return round(linear_load, 2)

def calculate_wall_moments(wind_force, height):
    moment = wind_force * height
    return round(moment, 2)

def calculate_roof_perimeter(coordinates):
    """Calculate the perimeter of the roof based on the given coordinates."""
    if not coordinates:
        return 0.0
    
    # Extract the Z-axis values
    z_vals = [coord[2] for coord in coordinates]
    
    # Find the maximum Z-axis value (highest elevation)
    max_z = max(z_vals)
    
    # Extract coordinates that are at the highest elevation
    roof_coords = [coord[:2] for coord in coordinates if coord[2] == max_z]
    
    if len(roof_coords) < 3:
        return 0.0

    perimeter = 0.0
    num_points = len(roof_coords)
    
    for i in range(num_points):
        x1, y1 = roof_coords[i]
        x2, y2 = roof_coords[(i + 1) % num_points]
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        perimeter += distance
    
    return round(perimeter, 2)

def calculate_dead_load(ifc_file):
    # Open the IFC file
    model = ifcopenshell.open(ifc_file)

    total_dead_load = 0.0

    for element in model.by_type('IfcElementQuantity'):
        for quantity in element.Quantities:
            if quantity.is_a('IfcQuantityWeight'):
                if 'Dead Load' in quantity.Name or 'DeadLoad' in quantity.Name or 'Gross Weight' in quantity.Name or 'GrossWeight' in quantity.Name:
                    total_dead_load += quantity.WeightValue

    return total_dead_load


def calculate_wind_loads(ifc_file):
    # Open the IFC file
    model = ifcopenshell.open(ifc_file)

    wind_pressure = 0.0
    wall_moment = 0.0

    # List of possible names for wind pressure and wall moment
    wind_pressure_names = ['Wind Pressure', 'WindPressure', 'Wind Load', 'WindLoad', 'Wind_Pressure', 'Wind_Load']
    wall_moment_names = ['Wall Moment', 'WallMoment', 'Wind Moment', 'WindMoment', 'Wall_Moment', 'Wind_Moment']

    for element in model.by_type('IfcElementQuantity'):
        for quantity in element.Quantities:
            # Check for wind pressure
            if any(name in quantity.Name for name in wind_pressure_names):
                if quantity.is_a('IfcQuantityArea'):
                    wind_pressure = quantity.AreaValue
                elif quantity.is_a('IfcQuantityLength'):
                    wind_pressure = quantity.LengthValue
                elif quantity.is_a('IfcQuantityVolume'):
                    wind_pressure = quantity.VolumeValue
                elif quantity.is_a('IfcQuantityForce'):
                    wind_pressure = quantity.ForceValue
                elif quantity.is_a('IfcQuantityPressure'):
                    wind_pressure = quantity.PressureValue

            # Check for wall moment
            if any(name in quantity.Name for name in wall_moment_names):
                if quantity.is_a('IfcQuantityArea'):
                    wall_moment = quantity.AreaValue
                elif quantity.is_a('IfcQuantityLength'):
                    wall_moment = quantity.LengthValue
                elif quantity.is_a('IfcQuantityVolume'):
                    wall_moment = quantity.VolumeValue
                elif quantity.is_a('IfcQuantityForce'):
                    wall_moment = quantity.ForceValue
                elif quantity.is_a('IfcQuantityMoment'):
                    wall_moment = quantity.MomentValue

    return {'Wind Pressure': wind_pressure, 'Wall Moment': wall_moment}

def calculate_snow_load(roof_area, snow_load_per_unit_area):
    """
    Calculate the total snow load on the roof.
    
    :param roof_area: Area of the roof in square feet.
    :param snow_load_per_unit_area: Snow load per unit area in lbs/sq. ft.
    :return: Total snow load in lbs.
    """
    total_snow_load = roof_area * snow_load_per_unit_area
    return round(total_snow_load, 2)

def calculate_ice_load(roof_area, ice_load_per_unit_area):
    """
    Calculate the total ice load on the roof.

    :param roof_area: Area of the roof in square feet.
    :param ice_load_per_unit_area: Ice load per unit area in lbs/sq. ft.
    :return: Total ice load in lbs.
    """
    total_ice_load = roof_area * ice_load_per_unit_area
    return round(total_ice_load, 2)

def on_drop(event, values):
    try:
        print("Drop event triggered!")
        
        # Print the event data
        print(f"Event data: {event.data}")
        
        ifc_file_path = event.data.strip('{}')  # Remove curly braces if present
        print(f"Processed file path: {ifc_file_path}")

        # Entry widgets
        wind_speed_entry = values["wind_speed_entry"]
        snow_load_entry = values["snow_load_entry"]
        ice_load_entry = values["ice_load_entry"]
        zero_check = values["remove_zero_point_var"]
        site_class_entry = values["site_class_entry"]
        importance_factor_entry = values["importance_factor_entry"]
        spectral_response_acceleration_entry = values["spectral_response_acceleration_entry"]


        coordinates = parse_ifc_file(ifc_file_path, zero_val=zero_check)
        areas = calculate_area_from_coords(coordinates)

        output_path = os.path.splitext(ifc_file_path)[0] + "_coordinate_plots.pdf"
        floor_count = extract_floor_data(ifc_file_path)
        forces, moments = extract_forces_moments(ifc_file_path)
        uplift_pressures, down_pressures = extract_roof_pressures(ifc_file_path)
        perimeter = calculate_perimeter(coordinates)
        roof_perimeter = calculate_roof_perimeter(coordinates)

        # Call the live_load_widget function to get live load inputs
        live_loads = live_load_widget(floor_count)
        ## print("Live Loads: ", live_loads)

        plot_coordinates(coordinates, areas, output_path, ifc_file_path)
        print(f"Output saved to: {output_path}")

        Aux_output_path = os.path.splitext(ifc_file_path)[0] + "_Aux.pdf"

        # Validate and convert inputs safely
        try:
            # roof_uplift = float(roof_uplift_entry or "0")
            ## print('daaaaaa',roof_uplift)
            # roof_downpressure = float(roof_downpressure_entry or "0")
            wind_speed = float(wind_speed_entry or "0")
            snow_load_per_unit_area = float(snow_load_entry or "0")
            ice_load_per_unit_area = float(ice_load_entry or "0")

            # Calculate total snow and ice loads
            roof_area = areas[0]  # Assuming the XY area is the roof area
            total_snow_load = calculate_snow_load(roof_area, snow_load_per_unit_area)
            ice_load_total = calculate_ice_load(roof_area, ice_load_per_unit_area)
            seismic_load = compute_seismic_load(
                float(site_class_entry or "0"),
                float(importance_factor_entry or "0"),
                float(spectral_response_acceleration_entry or "0")
            )

            # Extract element counts
            element_counts = extract_element_counts(ifc_file_path)

            # Calculate wind loads
            wind_loads = calculate_wind_loads(ifc_file_path)

            # Calculate dead load
            dead_load = calculate_dead_load(ifc_file_path)

            # Calculate beam and column weights
            total_weight = calculate_beam_column_weight(ifc_file_path)

            # Create Auxiliary PDF
            create_Aux_pdf(
                element_counts, Aux_output_path, ifc_file_path, floor_count, forces, moments, perimeter,
                uplift_pressures, down_pressures, wind_speed, roof_perimeter, areas,
                wind_loads, dead_load, total_weight, total_snow_load, ice_load_total, live_loads,
                seismic_load
            )

            # Message about the number of stories
            multi_story_msg = "The building is a single story."
            if floor_count > 1:
                multi_story_msg = f"The building has {floor_count} stories."

            CTkMessagebox(title="Info", message=f"Plot saved to {output_path}\nAuxiliary data saved to {Aux_output_path}\n{multi_story_msg}")

        except ValueError as e:
            CTkMessagebox(title="Error", message=f"Please enter valid numbers: {e}")
    except Exception as e:
        print(f"Error in on_drop function: {e}")
        CTkMessagebox(title="Error", message=f"An error occurred: {e}", icon="cancel")


mode = "dark"
class CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

def get_path(event):
    dropped_file = event.data.replace("{","").replace("}", "")
    print(str(dropped_file))
    # do further operation

def change():
    global mode
    if mode == "dark":
        ctk.set_appearance_mode("light")
        mode = "light"
        # Clear text box if needed
    else:
        ctk.set_appearance_mode("dark")
        mode = "dark"
        # Clear text box if needed

def on_submit(entries):
    # Collect all the values
    values = {
        "snow_load_entry": entries["snow_load_entry"].get().strip(),
        "ice_load_entry": entries["ice_load_entry"].get().strip(),
        "wind_speed_entry": entries["wind_speed_entry"].get().strip(),
        "remove_zero_point_var": entries["remove_zero_point_var"].get(),
        "site_class_entry": entries["site_class_entry"].get().strip(),
        "importance_factor_entry": entries["importance_factor_entry"].get().strip(),
        "spectral_response_acceleration_entry": entries["spectral_response_acceleration_entry"].get().strip(),
    }
    
    # Process or print the collected values
    print(values)  # Replace this with actual processing code

def on_calculate(entries):
    # Collect all the values from entry widgets
    values = {
        "snow_load_entry": entries["snow_load_entry"].get().strip(),
        "ice_load_entry": entries["ice_load_entry"].get().strip(),
        "wind_speed_entry": entries["wind_speed_entry"].get().strip(),
        "remove_zero_point_var": entries["remove_zero_point_var"].get(),
        "site_class_entry": entries["site_class_entry"].get().strip(),
        "importance_factor_entry": entries["importance_factor_entry"].get().strip(),
        "spectral_response_acceleration_entry": entries["spectral_response_acceleration_entry"].get().strip(),
    }
    
    # Perform calculations based on the collected values
    # Replace this with your actual calculation logic
    result = f"Calculated values based on: {values}"
    print(result)  # Or display it in a label or messagebox

textcolor='white'

def calculate_seismic_load(site_class_entry, importance_factor_entry, spectral_response_acceleration_entry):
    # Retrieve user input
    site_class = float(site_class_entry.get().strip() or "0")  # Get value from Entry widget
    importance_factor = float(importance_factor_entry.get().strip() or "0")
    spectral_response_acceleration = float(spectral_response_acceleration_entry.get().strip() or "0")

    # Calculate seismic load
    seismic_load = compute_seismic_load(site_class, importance_factor, spectral_response_acceleration)
    print(f"Seismic Load: {seismic_load} kN")


def compute_seismic_load(site_class, importance_factor, spectral_response_acceleration):

    # Assuming amplification_factors is a dictionary of floats
    amplification_factors = {
        # Example data; replace with actual values
        0.0: 1.0,  # This is a placeholder;
        1.0: 1.5,
        2.0: 2.0,
    }
    
    # Use the float value to get the amplification factor
    amplification_factor = amplification_factors.get(site_class, 1.0)  # Default to 1.0 if not found

    seismic_load = (importance_factor * spectral_response_acceleration * amplification_factor)

    return seismic_load


def create_seismic_input_widgets(master):
    # Create and place widgets
    entry_width=200
    site_class_label = ctk.CTkLabel(master, text="Site Class" ,fg_color='transparent',font=("Arial", 16, "bold"))
    site_class_label.grid(row=0, column=0,pady=10,padx=(100,0))
    site_class_entry = ctk.CTkEntry(master,placeholder_text="Enter site class" ,width=entry_width)
    site_class_entry.grid(row=0, column=1,)

    importance_factor_label = ctk.CTkLabel(master, text="Importance Factor",fg_color='transparent',font=("Arial", 16, "bold"))
    importance_factor_label.grid(row=1, column=0,pady=10,padx=(100,0))
    importance_factor_entry = ctk.CTkEntry(master,placeholder_text="Enter Importance Factor",width=entry_width)
    importance_factor_entry.grid(row=1, column=1)

    spectral_response_acceleration_label = ctk.CTkLabel(master, text="Spectral Response Acceleration",fg_color='transparent',font=("Arial", 16, "bold"))
    spectral_response_acceleration_label.grid(row=2, column=0,pady=10,padx=(100,0))
    spectral_response_acceleration_entry = ctk.CTkEntry(master,placeholder_text="Enter Spectral Response Acceleration",width=entry_width)
    spectral_response_acceleration_entry.grid(row=2, column=1,pady=10,)

    calculate_button = ctk.CTkButton(master,height=40,width=200,font=("Arial", 16, "bold"),fg_color='#4C7766',hover_color='#4C7766', text="Calculate Seismic Load", 
                                 command=lambda: calculate_seismic_load(site_class_entry, 
                                                                        importance_factor_entry, 
                                                                        spectral_response_acceleration_entry))
    calculate_button.grid(row=3, columnspan=5,pady=30,padx=(350,0))

    return master
def compute_seismic_load(site_class, importance_factor, spectral_response_acceleration):
    # Example seismic load calculation based on ASCE 7-16
    # Note: This is a simplified example. Actual calculations will depend on the standard used.
    
    # Site class factors (example values)
    site_class_factors = {
        'A': 0.8,
        'B': 1.0,
        'C': 1.2,
        'D': 1.4,
        'E': 1.6,
        'F': 1.8,
    }
    
    site_class_factor = site_class_factors.get(site_class, 1.0)
    
    # Simplified seismic load formula
    seismic_load = importance_factor * spectral_response_acceleration * site_class_factor * 100  # Example formula
    return seismic_load


def equivalent_static_analysis(W, Cs):
    V = Cs * W
    return V

# Example usage
W = 1000  # total weight of the structure in kN
Cs = 0.2  # seismic response coefficient
V = equivalent_static_analysis(W, Cs)
print(f"Equivalent Static Analysis Base Shear: {V} kN")


def response_spectrum_analysis(Vx, Vy, Vz):
    V = np.sqrt(Vx**2 + Vy**2 + Vz**2)
    return V

# Example usage
Vx = 150  # response in x direction in kN
Vy = 120  # response in y direction in kN
Vz = 80   # response in z direction in kN
V = response_spectrum_analysis(Vx, Vy, Vz)
print(f"Response Spectrum Analysis Base Shear: {V} kN")


def time_history_analysis(masses, accelerations):
    V = np.sum(masses * accelerations)
    return V

# Example usage
masses = np.array([100, 200, 300])  # masses of different floors in kN
accelerations = np.array([0.05, 0.04, 0.03])  # accelerations in m/s^2
V = time_history_analysis(masses, accelerations)
print(f"Time History Analysis Base Shear: {V} kN")


def modal_analysis(mode_shapes, generalized_coords):
    U = np.sum(mode_shapes * generalized_coords, axis=0)
    return U

# Example usage
mode_shapes = np.array([[1, 0.8, 0.6], [0.9, 0.7, 0.5], [0.8, 0.6, 0.4]])  # mode shapes
generalized_coords = np.array([0.05, 0.04, 0.03])  # generalized coordinates
U = modal_analysis(mode_shapes, generalized_coords)
print(f"Modal Analysis Response: {U}")

def capacity_spectrum_method(Sd, T, xi):
    # This is a simplified example. Actual calculations would be more complex.
    Sa = Sd / (T * (1 + xi))
    return Sa

# Example usage
Sd = 0.05  # spectral displacement in meters
T = 1.0  # fundamental period in seconds
xi = 0.05  # damping ratio
Sa = capacity_spectrum_method(Sd, T, xi)
print(f"Capacity Spectrum Method Spectral Acceleration: {Sa} m/s^2")

def simplified_method(W, SDS, R, I):
    V = (SDS / (R / I)) * W
    return V

# Example usage
W = 1000  # total weight in kN
SDS = 1.0  # design spectral response acceleration
R = 8  # response modification factor
I = 1.25  # importance factor
V = simplified_method(W, SDS, R, I)
print(f"Simplified Method Base Shear: {V} kN")

def design_base_shear(W, SDS, R, I):
    V = (SDS / (R / I)) * W
    return V

# Example usage
W = 1000  # total weight in kN
SDS = 1.0  # design spectral response acceleration at short periods
R = 8  # response modification factor
I = 1.25  # importance factor
V = design_base_shear(W, SDS, R, I)
print(f"Design Base Shear (ASCE 7-16): {V} kN")

results = []

def live_load_widget(floor_count):
    live_loads = []
    # Create the main window
    root = ctk.CTk()
    root.title("Live Load Input")
    root.geometry("800x800")
    root.resizable(False, False)
    ctk.set_appearance_mode("system") 
    # Create a scrollable frame
    scrollable_frame = ctk.CTkScrollableFrame(master=root, width=480, height=480)
    scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

    header_percentage = ctk.CTkLabel(scrollable_frame, text="Live Load Percentage",font=("Arial", 16, "bold"),)
    header_percentage.grid(row=0, column=0, pady=50, padx=(20,0), sticky='w')

    header_area = ctk.CTkLabel(scrollable_frame, text="Live Load Area (sq. ft.)",font=("Arial", 16, "bold"))
    header_area.grid(row=0, column=1, pady=10, padx=(20,0), sticky='w')

    # Loop through each floor and create input fields
    for floor in range(1, floor_count + 1):
        load_info = {}
        load_info['floor'] = floor

        # Add a label and entry for percentage load
        percentage_label = ctk.CTkLabel(scrollable_frame, text=f"Floor {floor}:",font=("Arial", 12, "bold"))
        percentage_label.grid(row=floor, column=0, pady=5, padx=10, sticky='e',)

        percentage_entry = ctk.CTkEntry(scrollable_frame, placeholder_text="Enter %",font=("Arial", 12, "bold"))
        percentage_entry.grid(row=floor, column=1, pady=5, padx=10, sticky='w',columnspan=1)
        load_info['percentage_load'] = percentage_entry

        # Add a label and entry for area load
        area_entry = ctk.CTkEntry(scrollable_frame, placeholder_text="Enter sq. ft.",font=("Arial", 12, "bold"))
        area_entry.grid(row=floor, column=2, pady=5, padx=20, sticky='w',columnspan=2)
        load_info['area_load'] = area_entry
        
        percentage3 = load_info['percentage_load'].get()
        print(percentage3)
        live_loads.append(load_info)
    

    # Add a button to submit the inputs
    submit_button = ctk.CTkButton(scrollable_frame, text="Submit", command=lambda: on_submit(live_loads, root),font=("Arial", 16, "bold"),fg_color='#677791',hover_color='#677791',)
    submit_button.grid(row=floor_count + 1, columnspan=2, pady=20)
    my_button = ctk.CTkButton(scrollable_frame, text='Change Mode', command=change, font=("Arial", 16, "bold"), fg_color='#677791', hover_color='#677791', compound='left')
    my_button.grid(row=12, columnspan=1, pady=(50, 0), padx=(0, 0))
    root.mainloop()
    return results
    
def plot_coordinates(coordinates, areas, output_path, ifc_file_path):
    from read_methods import extract_ifc_data
    from calculate import calculate_perimeter,calculate_footing_perimeter
    if not all(len(coord) == 3 for coord in coordinates):
        raise ValueError("Some coordinates do not have exactly three values.")

    x_vals = [coord[0] for coord in coordinates]
    y_vals = [coord[1] for coord in coordinates]
    z_vals = [coord[2] for coord in coordinates]

    # Determine max height for plot uniformity
    fac = 0.30 * max(max(z_vals), max(x_vals), max(y_vals))
    max_height = max(z_vals)
    max_width = max(y_vals)
    max_length = max(x_vals)

    max_hw = max(max_height, max_width) + fac
    min_hw = min(min(y_vals), min(z_vals)) - fac

    max_lw = max(max_length, max_width) + fac
    min_lw = min(min(y_vals), min(x_vals)) - fac

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 14), constrained_layout=True)
    axes = axes.flatten()  # Flatten the 2x2 grid to 1D for easier indexing

    sns.set(style="whitegrid")
    
    # Font settings
    title_fontsize = 14
    label_fontsize = 12
    tick_fontsize = 10

    # XZ Plane
    axes[0].plot(x_vals, z_vals, color='royalblue', linewidth=1)
    axes[0].set_title('XZ Plane (Feet)', fontsize=title_fontsize)
    axes[0].set_xlabel('X (feet)', fontsize=label_fontsize)
    axes[0].set_ylabel('Z (feet)', fontsize=label_fontsize)
    axes[0].axis('equal')
    axes[0].set_xlim([min_lw, max_lw])
    axes[0].set_ylim([min_hw, max_hw])
    axes[0].tick_params(axis='both', which='major', labelsize=tick_fontsize)

        # YZ Plane
    axes[1].plot(y_vals, z_vals, color='royalblue', linewidth=1)
    axes[1].set_title('YZ Plane (Feet)', fontsize=title_fontsize)
    axes[1].set_xlabel('Y (feet)', fontsize=label_fontsize)
    axes[1].set_ylabel('Z (feet)', fontsize=label_fontsize)
    axes[1].axis('equal')
    axes[1].set_xlim([min_lw, max_lw])
    axes[1].set_ylim([min_hw, max_hw])
    axes[1].tick_params(axis='both', which='major', labelsize=tick_fontsize)

    # XY Plane
    axes[2].plot(x_vals, y_vals, color='royalblue', linewidth=1)
    axes[2].set_title('XY Plane (Feet)', fontsize=title_fontsize)
    axes[2].set_xlabel('X (feet)', fontsize=label_fontsize)
    axes[2].set_ylabel('Y (feet)', fontsize=label_fontsize)
    axes[2].axis('equal')
    axes[2].set_xlim([min_lw, max_lw])
    axes[2].set_ylim([min_hw, max_hw])
    axes[2].tick_params(axis='both', which='major', labelsize=tick_fontsize)

    ww = extract_ifc_data(ifc_file_path)
    perimeter = calculate_perimeter(coordinates)
    footing_perimeter_coords = calculate_footing_perimeter(coordinates)

    # Plot Footing Perimeter

    footing_perimeter_coords = calculate_footing_perimeter(coordinates)

    if footing_perimeter_coords:
        x_vals_fp = [point[0] for point in footing_perimeter_coords] + [footing_perimeter_coords[0][0]]
        y_vals_fp = [point[1] for point in footing_perimeter_coords] + [footing_perimeter_coords[0][1]]
        #axes[2].plot(x_vals_fp, y_vals_fp, color='red', linewidth=1)

    # Aux Info
    axes[3].axis('off')
    axes[3].text(0.1, 0.9, f'XZ Area: {areas[2]} sq. feet', horizontalalignment='left', verticalalignment='center', fontsize=label_fontsize)
    axes[3].text(0.1, 0.8, f'YZ Area: {areas[1]} sq. feet', horizontalalignment='left', verticalalignment='center', fontsize=label_fontsize)
    axes[3].text(0.1, 0.7, f'XY Area: {areas[0]} sq. feet', horizontalalignment='left', verticalalignment='center', fontsize=label_fontsize)
    axes[3].text(0.1, 0.6, f'CFS Weight: {ww} lbs.', horizontalalignment='left', verticalalignment='center', fontsize=label_fontsize)
    axes[3].text(0.1, 0.5, f'Footing Perimeter: {perimeter} feet', horizontalalignment='left', verticalalignment='center', fontsize=label_fontsize)

    plt.savefig(output_path)
    # plt.show()

def create_Aux_pdf(element_counts, output_path, ifc_path, floor_count, forces, moments, perimeter, roof_uplift, roof_downpressure, wind_force, wall_height, roof_perimeter, areas, wind_loads, dead_load, total_weight, total_snow_load, total_ice_load, live_loads, seismic_load):
    from calculate import calculate_linear_load, calculate_wall_moments
    pdf = FPDF()
    multi_story_msg = "The building is a single story."
    if floor_count > 1:
        multi_story_msg = f"The building has {floor_count} stories."

    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Auxiliary Data", ln=True, align='C')

    for element_type, count in element_counts.items():
        pdf.cell(200, 10, txt=f'{element_type} Count: {count}', ln=True)

    pdf.cell(200, 10, txt=multi_story_msg, ln=True)
    pdf.cell(200, 10, txt=f'Total_weight: {total_weight} lbs', ln=True)
    # pdf.cell(200, 10, txt=f'Total Beam Weight: {total_beam_weight} lbs', ln=True)
    # pdf.cell(200, 10, txt=f'Total Column Weight: {total_column_weight} lbs', ln=True)

    for floor in forces:
        total_force = np.sum(forces[floor])
        total_moment = np.sum(moments[floor])
        pdf.cell(200, 10, txt=f'{floor} - Total Force: {total_force} N, Total Moment: {total_moment} Nm', ln=True)

    linear_load = calculate_linear_load(perimeter, roof_uplift, roof_downpressure)
    wall_moment = calculate_wall_moments(wind_force, wall_height)
    
    wind_pressure = wind_loads['Wind Pressure']

    pdf.cell(200, 10, txt=f'Estimated Linear Load on Perimeter: {linear_load} lbs/ft', ln=True)
    pdf.cell(200, 10, txt=f'Wall Moment from Wind: {wall_moment} Nm', ln=True)
    pdf.cell(200, 10, txt=f'Wind Pressure on Roof: {wind_pressure} lbs/ft²', ln=True)

    pdf.cell(200, 10, txt=f'Roof Perimeter: {roof_perimeter} feet', ln=True)
    pdf.cell(200, 10, txt=f'XZ Area: {areas[2]} sq. feet', ln=True)
    pdf.cell(200, 10, txt=f'YZ Area: {areas[1]} sq. feet', ln=True)
    pdf.cell(200, 10, txt=f'XY Area: {areas[0]} sq. feet', ln=True)

    pdf.cell(200, 10, txt="Wind Load Calculation Results:", ln=True)
    pdf.cell(200, 10, txt=f"Wind Pressure: {wind_loads['Wind Pressure']} lbs/ft", ln=True)
    pdf.cell(200, 10, txt=f"Wall Moment: {wind_loads['Wall Moment']} ft-lbs", ln=True)

    pdf.cell(200, 10, txt="Dead Load Calculation Results:", ln=True)
    pdf.cell(200, 10, txt=f"Total Dead Load: {dead_load} lbs", ln=True)

    pdf.cell(200, 10, txt="Snow Load Calculation Results:", ln=True)
    pdf.cell(200, 10, txt=f"Total Snow Load: {total_snow_load} lbs", ln=True)

    pdf.cell(200, 10, txt="Ice Load Calculation Results:", ln=True)
    pdf.cell(200, 10, txt=f"Total Ice Load: {total_ice_load} lbs", ln=True)
    
    pdf.cell(200, 10, txt="Live Loads:", ln=True)
    for load_info in live_loads:
        pdf.cell(200, 10, txt=f"Floor {load_info['floor']} - Percentage Load: {load_info['percentage_load']}%, Area Load: {load_info['area_load']} sq. feet", ln=True)

    pdf.output(output_path)


def main():
    from gui import on_drop
    ctk.set_appearance_mode("system")  # Default to light mode
    root = CTk()

    root.drop_target_register(DND_ALL)
   
    root.title("IFC to PDF Converter")
    root.geometry("950x800")
    root.resizable(False, False)
    entry_width = 250
    
    dark_light_image = ctk.CTkImage(light_image=Image.open("dark-light.png"),
                        dark_image=Image.open("dark-light.png"), size=(30, 30))
    # Create a CTkScrollableFrame
    scrollable_frame = ctk.CTkScrollableFrame(root)
    scrollable_frame.pack(expand=True, fill='both')

    # Add a nested frame inside the scrollable frame to hold the widgets
    content_frame = ctk.CTkFrame(scrollable_frame)
    content_frame.pack(expand=True, fill='both')

    my_button = ctk.CTkButton(content_frame, text='Change Mode', command=change, font=("Arial", 16, "bold"), fg_color='#677791', hover_color='#677791',image=dark_light_image, compound='left')
    my_button.grid(row=0, column=2, pady=(0, 0), sticky='e')  # Adjusted to be visible

    remove_zero_point_var = BooleanVar(value=False)
    checkbox = ctk.CTkCheckBox(content_frame, text="Remove (0,0,0) Point", variable=remove_zero_point_var, font=("Arial", 16, "bold"), fg_color='#677791', hover_color='#677791')
    checkbox.grid(row=0, column=0, pady=50, padx=(50, 0), sticky='w')


    # Site Class Dropdown
    site_class_label = ctk.CTkLabel(content_frame, text="Site Class", fg_color='transparent', font=("Arial", 16, "bold"))
    site_class_label.grid(row=1, column=0, pady=10, padx=(50, 0), sticky='w')

    site_class_options = ["0", "1", "2"]  # Your available options
    site_class_entry = ctk.CTkOptionMenu(content_frame, values=site_class_options)
    site_class_entry.grid(row=1, column=1, padx=(50, 0), sticky='w')
    site_class_entry.set("0")  # Default value

    importance_factor_label = ctk.CTkLabel(content_frame, text="Importance Factor", fg_color='transparent', font=("Arial", 16, "bold"))
    importance_factor_label.grid(row=2, column=0, pady=10, padx=(50, 0), sticky='w')
    importance_factor_entry = ctk.CTkEntry(content_frame, placeholder_text="Enter Importance Factor", width=entry_width)
    importance_factor_entry.grid(row=2, column=1, padx=(50, 0), sticky='w')
    importance_factor_entry.insert(0,"1")  # Default value

    spectral_response_acceleration_label = ctk.CTkLabel(content_frame, text="Spectral Response Acceleration", fg_color='transparent', font=("Arial", 16, "bold"))
    spectral_response_acceleration_label.grid(row=3, column=0, pady=10, padx=(50, 0), sticky='w')
    spectral_response_acceleration_entry = ctk.CTkEntry(content_frame, placeholder_text="Enter Spectral Response Acceleration", width=entry_width)
    spectral_response_acceleration_entry.grid(row=3, column=1, pady=10, padx=(50, 0), sticky='w')
       
    label = ctk.CTkLabel(content_frame, text="Drag and Drop an IFC File Here..", corner_radius=10, font=("Arial", 16, "bold"))
    label.grid(row=3, column=2, pady=(10, 20), padx=(50, 0) )

    ctk.CTkLabel(content_frame, text="Ice Load (lbs/sq. ft.):", font=("Arial", 16, "bold")).grid(row=5, column=0, sticky='w', pady=10, padx=(50, 0))
    ice_load_entry = ctk.CTkEntry(content_frame, width=entry_width, placeholder_text="Enter ICE Load")
    ice_load_entry.grid(row=5, column=1,padx=(50,0), sticky='w')

    ctk.CTkLabel(content_frame, text="Snow Load (lbs/sq. ft.):", font=("Arial", 16, "bold")).grid(row=6, column=0, sticky='w', pady=10, padx=(50, 0))
    snow_load_entry = ctk.CTkEntry(content_frame, width=entry_width, placeholder_text="Enter Snow load")
    snow_load_entry.grid(row=6, column=1,padx=(50,0), sticky='w')

    ctk.CTkLabel(content_frame, text="Wind Speed (Mph)", font=("Arial", 16, "bold")).grid(row=7, column=0, sticky='w', pady=10, padx=(50, 0))
    wind_speed_entry = ctk.CTkEntry(content_frame, width=entry_width, placeholder_text="Enter Wind Speed")
    wind_speed_entry.grid(row=7, column=1,padx=(50,0), sticky='w')

     

    entries = {
        "snow_load_entry": snow_load_entry,
        "ice_load_entry": ice_load_entry,
        "wind_speed_entry": wind_speed_entry,
        "remove_zero_point_var": remove_zero_point_var,
        "site_class_entry": site_class_entry,
        "importance_factor_entry": importance_factor_entry,
        "spectral_response_acceleration_entry": spectral_response_acceleration_entry,
    }
    submit_button = ctk.CTkButton(content_frame, text="Submit", font=("Arial", 16, "bold"), fg_color='#677791', hover_color='#677791',
                                  command=lambda: on_submit(entries))
    submit_button.grid(row=8, column=1, pady=20, padx=(50, 0), sticky='w')

    calculate_button = ctk.CTkButton(content_frame, text="Calculate", font=("Arial", 16, "bold"), fg_color='#677791', hover_color='#677791',
                                     command=lambda: on_calculate(entries))
    calculate_button.grid(row=12, column=2, pady=20, padx=(50, 0), sticky='e')

    # Ensure the event is properly bound
    root.dnd_bind('<<Drop>>', lambda event: on_drop(event, entries))  
    root.mainloop()

if __name__ == '__main__':
    main()

