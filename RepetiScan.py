import os
import difflib
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tokenize import group
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import subprocess
from send2trash import send2trash
from pathlib import Path
import json
import sys

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

def get_mp3_titles(folder):
    songs = []
    for filename in os.listdir(folder):
        if filename.lower().endswith('.mp3'):
            filepath = os.path.join(folder, filename)
            try:
                audio = MP3(filepath, ID3=EasyID3)
                title = audio.get("title", [os.path.splitext(filename)[0]])[0]
                artist = audio.get("artist", [""])[0]
                songs.append((title, filepath, artist))
            except Exception as e:
                print(f"Error leyendo {filename}: {e}")
    return songs

def group_songs_by_title(songs):
    grouped = {}
    for title, path, artist in songs:
        if title not in grouped:
            grouped[title] = []
        grouped[title].append((title, path, artist))
    return list(grouped.values())

def find_similar_groups_by_ratio(songs, threshold, blacklist):
    groups = []
    seen = set()
    for i in range(len(songs)):
        title_i, file_i, artist_i = songs[i]
        if file_i in seen:
            continue
        group = [(title_i, file_i, artist_i)]
        seen.add(file_i)
        clean_i = clean_title(title_i, blacklist)
        for j in range(i+1, len(songs)):
            title_j, file_j, artist_j = songs[j]
            if file_j in seen:
                continue
            clean_j = clean_title(title_j, blacklist)
            similarity = difflib.SequenceMatcher(None, clean_i, clean_j).ratio()
            if similarity >= threshold:
                group.append((title_j, file_j, artist_j))
                seen.add(file_j)
        if len(group) > 1:
            groups.append(group)
    return groups

def find_similar_groups_by_words(songs, min_overlap, blacklist):
    groups = []
    seen = set()
    for i in range(len(songs)):
        title_i, file_i, artist_i = songs[i]
        if file_i in seen:
            continue
        group = [(title_i, file_i, artist_i)]
        words_i = set(clean_title(title_i, blacklist).split())
        seen.add(file_i)
        for j in range(i+1, len(songs)):
            title_j, file_j, artist_j = songs[j]
            if file_j in seen:
                continue
            words_j = set(clean_title(title_j, blacklist).split())
            if len(words_i & words_j) >= min_overlap:
                group.append((title_j, file_j, artist_j))
                seen.add(file_j)
        if len(group) > 1:
            groups.append(group)
    return groups


class SimilarityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 RepetiScan Music")
        self.folder = ""
        self.threshold = tk.DoubleVar(value=0.8)
        self.min_overlap = tk.IntVar(value=2)
        self.excluded_artist = tk.StringVar(value="")
        self.groups = []
        self.current_mode = "ratio"
        self.blacklist = load_blacklist()
        self.lang = "es"
        self.translations = self.load_translations()

        self.build_ui()

    def load_translations(self):
        if getattr(sys, 'frozen', False):  # Si está corriendo como .exe
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)

        lang_path = os.path.join(base_path, "lang.json")

        with open(lang_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def t(self, key):
        return self.translations.get(self.lang, {}).get(key, key)
    
    def toggle_language(self):
        self.lang = "en" if self.lang == "es" else "es"
        self.refresh_ui()

    def refresh_ui(self):
        # Elimina los widgets actuales de la interfaz y reconstruye todo
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_ui()


    def build_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10, padx=20, anchor='center')

        

        # Fila 1: Seleccionar carpeta e idioma
        tk.Button(control_frame, text=self.t("select_folder"), command=self.select_folder, width=30).grid(row=0, column=0, padx=5, pady=5)
        tk.Button(control_frame, text=self.t("change_language"), command=self.toggle_language, width=30).grid(row=0, column=2, padx=5, pady=5)

        # Fila 2: Buscar por porcentaje
        tk.Label(control_frame, text=self.t("similarity_label")).grid(row=1, column=0, sticky="w", padx=5)
        tk.Entry(control_frame, textvariable=self.threshold, width=6).grid(row=1, column=1, padx=5)
        tk.Button(control_frame, text=self.t("search_ratio"), command=self.analyze_by_ratio, width=30).grid(row=1, column=2, padx=5, pady=5)

        # Fila 3: Buscar por palabras
        tk.Label(control_frame, text=self.t("min_common_words")).grid(row=2, column=0, sticky="w", padx=5)
        tk.Entry(control_frame, textvariable=self.min_overlap, width=6).grid(row=2, column=1, padx=5)
        tk.Button(control_frame, text=self.t("search_words"), command=self.analyze_by_words, width=30).grid(row=2, column=2, padx=5, pady=5)

        # Fila 4: Buscar no artista
        tk.Label(control_frame, text=self.t("exclude_artist")).grid(row=3, column=0, sticky="w", padx=5)
        tk.Entry(control_frame, textvariable=self.excluded_artist, width=20).grid(row=3, column=1, padx=5)
        tk.Button(control_frame, text=self.t("search_not_artist"), command=self.analyze_excluding_artist, width=30).grid(row=3, column=2, padx=5, pady=5)

        # Fila 5: Editar blacklist
        tk.Button(control_frame, text=self.t("edit_blacklist"), command=self.open_blacklist_editor, width=30).grid(row=4, column=0, padx=5, pady=5)

        # Fila 6: Exportar CSV
        tk.Button(control_frame, text=self.t("export_csv"), command=self.export_csv, width=30).grid(row=4, column=1, padx=5, pady=5)

        # Fila 7: Ayuda
        tk.Button(control_frame, text=self.t("help"), command=self.show_help, width=30).grid(row=4, column=2, padx=5, pady=5)


        # Tabla
        self.tree = ttk.Treeview(self.root, columns=("Grupo"), show="headings", selectmode="extended")
        self.tree.heading("Grupo", text=self.t("similar_songs"))
        self.tree.column("Grupo", width=800)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.pack(padx=10, pady=10, fill='both', expand=True)


    def open_blacklist_editor(self):
        editor = tk.Toplevel(self.root)
        editor.title(self.t("edit_blacklist"))
        editor.geometry("400x500")

        frame = tk.Frame(editor)
        frame.pack(fill='both', expand=True, padx=10, pady=10)

        check_vars = {}

        def refresh_checkboxes():
            for widget in frame.winfo_children():
                widget.destroy()
            check_vars.clear()

            for word, active in self.blacklist.items():
                var = tk.BooleanVar(value=active)
                chk = tk.Checkbutton(frame, text=word, variable=var, anchor='w', width=30)
                chk.pack(anchor='w')
                check_vars[word] = var

        def add_word():
            new_word = new_word_var.get().strip().lower()
            if new_word and new_word not in self.blacklist:
                self.blacklist[new_word] = True
                refresh_checkboxes()
                new_word_var.set("")

        def save_and_close():
            for word, var in check_vars.items():
                self.blacklist[word] = var.get()
            with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.blacklist, f, indent=4)
            editor.destroy()

        # Entrada para nueva palabra
        add_frame = tk.Frame(editor)
        add_frame.pack(pady=(0,10))

        new_word_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=new_word_var, width=20).pack(side=tk.LEFT, padx=5)
        tk.Button(add_frame, text=self.t("add_word"), command=add_word).pack(side=tk.LEFT)

        # Inicializar los checkboxes
        refresh_checkboxes()

        # Guardar y cerrar
        tk.Button(editor, text=self.t("save_close"), command=save_and_close).pack(pady=10)



    def show_help(self):
        msg = (
            f"{self.t('help_text')}"
        )
        messagebox.showinfo(self.t("help_multiple_files"), msg)

    def on_right_click(self, event):
        selected = self.tree.selection()
        if self.current_mode != "not_artist" or not selected:
            return

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="🗑️ Eliminar grupo(s)", command=lambda: self.delete_selected_groups(selected))
        menu.tk_popup(event.x_root, event.y_root)

    def delete_selected_groups(self, selected):
        confirm = messagebox.askyesno(self.t("confirm_delete"), self.t("confirm_delete_text"))
        if not confirm:
            return
        indices = [int(i) for i in selected]
        for idx in sorted(indices, reverse=True):
            for _, path, _ in self.groups[idx]:
                try:
                    send2trash(str(Path(path)))
                except:
                    pass
            self.tree.delete(idx)
            self.groups.pop(idx)

    def select_folder(self):
        self.folder = filedialog.askdirectory()
        if self.folder:
            messagebox.showinfo(self.t("select_folder"), self.folder)

    def analyze_by_ratio(self):
        self.current_mode = "ratio"
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            messagebox.showerror("Error", self.t("folder_error"))
            return

        songs = get_mp3_titles(self.folder)
        self.groups = find_similar_groups_by_ratio(songs, self.threshold.get(), self.blacklist)

        if not self.groups:
            messagebox.showinfo(self.t("no_coincidence"), self.t("no_coincidence_text"))
            return

        for idx, group in enumerate(self.groups):
            names = ",  ".join([t for t, _, _ in group])
            self.tree.insert('', 'end', iid=idx, values=(names,))


    def analyze_by_words(self):
        self.current_mode = "words"
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            messagebox.showerror("Error", self.t("folder_error"))
            return

        songs = get_mp3_titles(self.folder)
        self.groups = find_similar_groups_by_words(songs, self.min_overlap.get(), self.blacklist)

        if not self.groups:
            messagebox.showinfo(self.t("no_coincidence"), self.t("no_coincidence_text"))
            return

        for idx, group in enumerate(self.groups):
            names = ",  ".join([t for t, _, _ in group])
            self.tree.insert('', 'end', iid=idx, values=(names,))


    def analyze_excluding_artist(self):
        self.current_mode = "not_artist"
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            messagebox.showerror("Error", self.t("folder_error"))
            return

        songs = get_mp3_titles(self.folder)
        songs = [s for s in songs if self.excluded_artist.get().strip().lower() not in (s[2] or '').lower()]
        self.groups = group_songs_by_title(songs)

        if not self.groups:
            messagebox.showinfo(self.t("no_coincidence"), self.t("no_coincidence_text"))
            return

        for idx, group in enumerate(self.groups):
            names = ",  ".join([f"{t} ({a})" for t, _, a in group])
            self.tree.insert('', 'end', iid=idx, values=(names,))


    def on_double_click(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_indices = [int(item) for item in selected_items]
        selected_groups = [self.groups[idx] for idx in selected_indices]

        win = tk.Toplevel(self.root)
        win.title(self.t("group_action"))
        win.geometry("900x300")

        h_scroll = tk.Scrollbar(win, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        canvas = tk.Canvas(win, xscrollcommand=h_scroll.set)
        canvas.pack(side="top", fill="both", expand=True)
        h_scroll.config(command=canvas.xview)

        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def delete_all():
            confirm = messagebox.askyesno(self.t("delete_all"), self.t("delete_all_text"))
            if confirm:
                for group in selected_groups:
                    for _, path, _ in group:
                        try:
                            send2trash(str(Path(path)))
                        except:
                            pass
                win.destroy()
                if self.current_mode == "not_artist":
                    for idx in sorted(selected_indices, reverse=True):
                        self.groups.pop(idx)
                        self.tree.delete(idx)
                else:
                    self.analyze_by_ratio()

        for group in selected_groups:
            for title, path, artist in group:
                sub = tk.Frame(content_frame, relief="groove", bd=2)
                sub.pack(side="left", padx=10, pady=5)
                tk.Label(sub, text=title, wraplength=150).pack(pady=2)
                tk.Label(sub, text=f"👤 {artist}", wraplength=150).pack(pady=2)
                tk.Button(sub, text=self.t("reproduce"), command=lambda p=path: self.play(p)).pack(pady=2)
                tk.Button(sub, text=self.t("move_to_trash"), command=lambda p=path: self.delete(p, win)).pack(pady=2)

        if self.current_mode == "not_artist":
            tk.Button(content_frame, text=self.t("delete_entire_group"), command=delete_all, bg="red", fg="white").pack(pady=10)

        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def play(self, filepath):
        try:
            os.startfile(filepath)
        except:
            subprocess.call(["xdg-open", filepath])

    def delete(self, filepath, window=None):
        confirm = messagebox.askyesno(self.t("move_to_trash"), self.t("move_to_trash_text").format(filepath=filepath))
        if confirm:
            try:
                if not os.path.exists(filepath):
                    messagebox.showerror(self.t("file_not_found"), self.t("file_not_found_text").format(filepath=filepath))
                    return
                send2trash(str(Path(filepath)))
                messagebox.showinfo(self.t("deleted"), self.t("deleted_text").format(filepath=filepath))
                if window:
                    window.destroy()
                if self.current_mode == "ratio":
                    self.analyze_by_ratio()
                elif self.current_mode == "words":
                    self.analyze_by_words()
                elif self.current_mode == "not_artist":
                    self.analyze_excluding_artist()
            except Exception as e:
                messagebox.showerror("Error", self.t("trash_error").format(e=e))

    def export_csv(self):
        if not self.groups:
            messagebox.showwarning(self.t("export_error"), self.t("export_error_text"))
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
                messagebox.showinfo(self.t("exported"), self.t("exported_text").format(path=path))
            except Exception as e:
                messagebox.showerror("Error", self.t("export_patch_error").format(e=e))


if __name__ == "__main__":
    root = tk.Tk()
    app = SimilarityApp(root)
    root.mainloop()
    
