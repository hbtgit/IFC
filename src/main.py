import customtkinter as ctk
from tkinter import BooleanVar
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinterdnd2 import TkinterDnD, DND_ALL
from Seismicwidget import create_seismic_input_widgets
from PIL import Image

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

     

    values = {
        "snow_load_entry": snow_load_entry.get().strip(),
        "ice_load_entry": ice_load_entry.get().strip(),
        "wind_speed_entry": wind_speed_entry.get().strip(),
        "remove_zero_point_var": remove_zero_point_var,
        "site_class_entry": site_class_entry.get().strip(),
        "importance_factor_entry": importance_factor_entry.get().strip(),
        "spectral_response_acceleration_entry": spectral_response_acceleration_entry.get().strip(),
    }

    # Ensure the event is properly bound
    root.dnd_bind('<<Drop>>', lambda event: on_drop(event, values))  
    root.mainloop()

if __name__ == '__main__':
    main()