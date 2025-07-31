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


def find_similar_groups_by_ratio(songs, threshold):
    groups = []
    seen = set()
    for i in range(len(songs)):
        title_i, file_i, artist_i = songs[i]
        if file_i in seen:
            continue
        group = [(title_i, file_i, artist_i)]
        seen.add(file_i)
        for j in range(i+1, len(songs)):
            title_j, file_j, artist_j = songs[j]
            if file_j in seen:
                continue
            similarity = difflib.SequenceMatcher(None, title_i.lower(), title_j.lower()).ratio()
            if similarity >= threshold:
                group.append((title_j, file_j, artist_j))
                seen.add(file_j)
        if len(group) > 1:
            groups.append(group)
    return groups


def find_similar_groups_by_words(songs, min_overlap):
    groups = []
    seen = set()
    for i in range(len(songs)):
        title_i, file_i, artist_i = songs[i]
        if file_i in seen:
            continue
        group = [(title_i, file_i, artist_i)]
        words_i = set(title_i.lower().split())
        seen.add(file_i)
        for j in range(i+1, len(songs)):
            title_j, file_j, artist_j = songs[j]
            if file_j in seen:
                continue
            words_j = set(title_j.lower().split())
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

        self.build_ui()

    def build_ui(self):
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10, padx=20, anchor='center')

        tk.Button(control_frame, text="📁 Seleccionar carpeta", command=self.select_folder, width=22).grid(row=0, column=0, padx=5, pady=5)
        tk.Label(control_frame, text="Similitud mínima (0.0 - 1.0):").grid(row=0, column=1, padx=5, sticky="e")
        tk.Entry(control_frame, textvariable=self.threshold, width=6).grid(row=0, column=2, padx=5)
        tk.Button(control_frame, text="% Buscar por porcentaje", command=self.analyze_by_ratio, width=22).grid(row=0, column=3, padx=5, pady=5)

        tk.Label(control_frame, text="Palabras mínimas en común:").grid(row=1, column=1, padx=5, sticky="e")
        tk.Entry(control_frame, textvariable=self.min_overlap, width=6).grid(row=1, column=2, padx=5)
        tk.Button(control_frame, text="🔤 Buscar por palabras", command=self.analyze_by_words, width=22).grid(row=1, column=3, padx=5, pady=5)

        tk.Label(control_frame, text="Mostrar si no es artista:").grid(row=2, column=1, padx=5, sticky="e")
        tk.Entry(control_frame, textvariable=self.excluded_artist, width=20).grid(row=2, column=2, padx=5)
        tk.Button(control_frame, text="❌ Buscar no artista", command=self.analyze_excluding_artist, width=22).grid(row=2, column=3, padx=5, pady=5)
        tk.Button(control_frame, text="📤 Exportar CSV", command=self.export_csv, width=22).grid(row=3, column=3, padx=5, pady=5)
        tk.Button(control_frame, text="ℹ️ Ayuda", command=self.show_help, width=22).grid(row=3, column=0, padx=5, pady=5)

        self.tree = ttk.Treeview(self.root, columns=("Grupo"), show="headings", selectmode="extended")
        self.tree.heading("Grupo", text="Canciones similares")
        self.tree.column("Grupo", width=800)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.pack(padx=10, pady=10, fill='both', expand=True)

    def show_help(self):
        msg = (
            "✅ Cómo eliminar múltiples grupos en 'No Artista':\n\n"
            "1. Selecciona varias filas con Ctrl (o Cmd en Mac).\n"
            "2. Haz doble clic en una de ellas para abrir la ventana.\n"
            "3. Usa el botón '🗑️ Eliminar TODO el grupo'.\n\n"
            "También puedes hacer clic derecho sobre la selección y elegir 'Eliminar grupo(s)'."
        )
        messagebox.showinfo("Ayuda para eliminación múltiple", msg)

    def on_right_click(self, event):
        selected = self.tree.selection()
        if self.current_mode != "not_artist" or not selected:
            return

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="🗑️ Eliminar grupo(s)", command=lambda: self.delete_selected_groups(selected))
        menu.tk_popup(event.x_root, event.y_root)

    def delete_selected_groups(self, selected):
        confirm = messagebox.askyesno("Confirmar eliminación", "¿Eliminar TODAS las canciones de los grupos seleccionados?")
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
            messagebox.showinfo("Carpeta seleccionada", self.folder)

    def analyze_by_ratio(self):
        self.current_mode = "ratio"
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            messagebox.showerror("Error", "Selecciona una carpeta primero.")
            return

        songs = get_mp3_titles(self.folder)
        self.groups = find_similar_groups_by_ratio(songs, self.threshold.get())

        if not self.groups:
            messagebox.showinfo("Sin coincidencias", "No se encontraron canciones similares.")
            return

        for idx, group in enumerate(self.groups):
            names = ",  ".join([t for t, _, _ in group])
            self.tree.insert('', 'end', iid=idx, values=(names,))

    def analyze_by_words(self):
        self.current_mode = "words"
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            messagebox.showerror("Error", "Selecciona una carpeta primero.")
            return

        songs = get_mp3_titles(self.folder)
        self.groups = find_similar_groups_by_words(songs, self.min_overlap.get())

        if not self.groups:
            messagebox.showinfo("Sin coincidencias", "No se encontraron canciones similares.")
            return

        for idx, group in enumerate(self.groups):
            names = ",  ".join([t for t, _, _ in group])
            self.tree.insert('', 'end', iid=idx, values=(names,))

    def analyze_excluding_artist(self):
        self.current_mode = "not_artist"
        self.tree.delete(*self.tree.get_children())
        if not self.folder:
            messagebox.showerror("Error", "Selecciona una carpeta primero.")
            return

        songs = get_mp3_titles(self.folder)
        songs = [s for s in songs if self.excluded_artist.get().strip().lower() not in (s[2] or '').lower()]
        self.groups = group_songs_by_title(songs)

        if not self.groups:
            messagebox.showinfo("Sin coincidencias", "No se encontraron canciones distintas a ese artista.")
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
        win.title("Acciones para grupo")
        win.geometry("900x300")

        h_scroll = tk.Scrollbar(win, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        canvas = tk.Canvas(win, xscrollcommand=h_scroll.set)
        canvas.pack(side="top", fill="both", expand=True)
        h_scroll.config(command=canvas.xview)

        content_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def delete_all():
            confirm = messagebox.askyesno("Confirmar eliminación", "¿Eliminar TODAS las canciones de los grupos seleccionados?")
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
                tk.Button(sub, text="▶ Reproducir", command=lambda p=path: self.play(p)).pack(pady=2)
                tk.Button(sub, text="🗑️ Mover a papelera", command=lambda p=path: self.delete(p, win)).pack(pady=2)

        if self.current_mode == "not_artist":
            tk.Button(content_frame, text="🗑️ Eliminar TODO el grupo", command=delete_all, bg="red", fg="white").pack(pady=10)

        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def play(self, filepath):
        try:
            os.startfile(filepath)
        except:
            subprocess.call(["xdg-open", filepath])

    def delete(self, filepath, window=None):
        confirm = messagebox.askyesno("Confirmar eliminación", f"¿Mover a papelera?\n{filepath}")
        if confirm:
            try:
                if not os.path.exists(filepath):
                    messagebox.showerror("Archivo no encontrado", f"El archivo no existe:\n{filepath}")
                    return
                send2trash(str(Path(filepath)))
                messagebox.showinfo("Eliminado", "El archivo se movió a la papelera.")
                if window:
                    window.destroy()
                if self.current_mode == "ratio":
                    self.analyze_by_ratio()
                elif self.current_mode == "words":
                    self.analyze_by_words()
                elif self.current_mode == "not_artist":
                    self.analyze_excluding_artist()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo mover:\n{e}")

    def export_csv(self):
        if not self.groups:
            messagebox.showwarning("Nada que exportar", "No hay coincidencias.")
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
                messagebox.showinfo("Exportado", f"Datos guardados en:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo exportar:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SimilarityApp(root)
    root.mainloop()
