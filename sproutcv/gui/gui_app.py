# %%
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
from sproutcv.pipeline import run_pipeline


class SproutGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("SproutCV")
        self.root.geometry("650x450")

        self.folder = None
        self.csv = None

        self.build_ui()

    # ---------------- UI ----------------

    def build_ui(self):

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        tk.Button(frame, text="Browse Image Folder", command=self.select_folder).grid(row=0, column=0, padx=5)
        tk.Button(frame, text="Browse Calibration CSV", command=self.select_csv).grid(row=0, column=1, padx=5)

        self.drop_box = tk.Label(
            self.root,
            text="Drag & Drop Folder or CSV Here",
            bg="#dddddd",
            width=60,
            height=5
        )
        self.drop_box.pack(pady=10)

        self.drop_box.drop_target_register(DND_FILES)
        self.drop_box.dnd_bind("<<Drop>>", self.drop_event)

        self.progress = ttk.Progressbar(self.root, length=400)
        self.progress.pack(pady=10)

        tk.Button(self.root, text="RUN ANALYSIS", bg="green", fg="white",
                  command=self.run_analysis).pack(pady=10)

        self.log = ScrolledText(self.root, height=12)
        self.log.pack(fill="both", expand=True)

    # ---------------- File Selection ----------------

    def select_folder(self):
        self.folder = filedialog.askdirectory()
        self.write_log(f"Selected folder: {self.folder}")

    def select_csv(self):
        self.csv = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        self.write_log(f"Selected CSV: {self.csv}")

    def drop_event(self, event):
        path = event.data.strip("{}")

        if path.lower().endswith(".csv"):
            self.csv = path
            self.write_log(f"CSV Dropped: {path}")
        else:
            self.folder = path
            self.write_log(f"Folder Dropped: {path}")

    # ---------------- Logging ----------------

    def write_log(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    # ---------------- Progress ----------------

    def update_progress(self, value):
        self.progress["value"] = value * 100
        self.root.update_idletasks()

    # ---------------- Run ----------------

    def run_analysis(self):

        if not self.folder or not self.csv:
            self.write_log("Please select folder and CSV first.")
            return

        threading.Thread(target=self._run_pipeline).start()

    def _run_pipeline(self):

        try:
            run_pipeline(
                self.folder,
                self.csv,
                log_callback=self.write_log,
                progress_callback=self.update_progress
            )

            self.write_log("Processing complete!")

        except Exception as e:
            self.write_log(f"ERROR: {str(e)}")


# --------- Launch App ---------

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = SproutGUI(root)
    root.mainloop()




