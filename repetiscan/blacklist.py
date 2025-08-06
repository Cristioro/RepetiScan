import tkinter as tk
import customtkinter
import json
import os

check_vars = {}


BLACKLIST_FILE = "blacklist.json"

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        default = {"remastered": True, "live": True, "bonus track": False, "demo": False, "radio edit": True}
        with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(default, f, indent=4)
    with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def clean_title(title, blacklist):
    lowered = title.lower()
    for word, active in blacklist.items():
        if active and word in lowered:
            lowered = lowered.replace(word, '')
    return lowered.strip()

def add_word(new_word_var, selfie, frame):
    new_word = new_word_var.get().strip().lower()
    if new_word and new_word not in selfie.blacklist:
        selfie.blacklist[new_word] = True
        refresh_checkboxes(frame, selfie)
        new_word_var.set("")

def refresh_checkboxes(frame, self):
    for widget in frame.winfo_children():
        widget.destroy()
    check_vars.clear()
    for word, active in self.blacklist.items():
        var = tk.BooleanVar(value=active)
        chk = customtkinter.CTkCheckBox(frame, text=word, variable=var)
        chk.pack(anchor='w')
        check_vars[word] = var



def save_and_close(editor, self):
    for word, var in check_vars.items():
        self.blacklist[word] = var.get()
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(self.blacklist, f, indent=4)
    editor.destroy()