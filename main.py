from tkinterdnd2 import TkinterDnD
from sproutcv.gui.gui_app import SproutGUI

def launch_gui():
    root = TkinterDnD.Tk()
    app = SproutGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_gui()
