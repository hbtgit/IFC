import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

class Application(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Drag-and-Drop Test")
        self.geometry("400x300")
        self.create_widgets()
        self.register_drop_target()

    def create_widgets(self):
        self.result_label = tk.Label(self, text="Drag and drop a file here")
        self.result_label.pack(pady=20)

    def register_drop_target(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)

    def on_drop(self, event):
        print("Drop event received")
        print(f"Full event data: {event.data}")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
