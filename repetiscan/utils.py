import os
import subprocess
from tkinter import filedialog
from CTkMessagebox import CTkMessagebox
import csv
from repetiscan.language import t

def play(filepath):
    try:
        os.startfile(filepath)
    except:
        subprocess.call(["xdg-open", filepath])


def export_csv(self):
    if not self.groups:
        CTkMessagebox(title=t("export_error", self.lang, self.translations), message=t("export_error_text", self.lang, self.translations), icon="warning")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if path:
        try:
            with open(path, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Grupo", "Canciones"])
                for idx, group in enumerate(self.groups):
                    names = [t for t, _, _ in group]
                    writer.writerow([f"Grupo {idx+1}", ", ".join(names)])
            CTkMessagebox(title=t("exported", self.lang, self.translations), message=t("exported_text", self.lang, self.translations).format(path=path))
        except Exception as e:
            CTkMessagebox(title="Error", message=t("export_patch_error", self.lang, self.translations).format(e=e), icon="warning")




