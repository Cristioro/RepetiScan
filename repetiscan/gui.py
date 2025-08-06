import os
import tkinter as tk
import customtkinter
from CTkMessagebox import CTkMessagebox
from tkinter import filedialog, ttk
from send2trash import send2trash
from pathlib import Path
from repetiscan.language import t, load_translations
from repetiscan.blacklist import refresh_checkboxes, add_word, save_and_close, load_blacklist
from repetiscan.utils import play, export_csv
from repetiscan.core import *

BLACKLIST_FILE = "blacklist.json"

class SimilarityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 RepetiScan Music")
        self.sidebar_visible = False
        self.sidebar_frame = None
        self.folder = ""
        self.threshold = customtkinter.DoubleVar(value=0.8)
        self.min_overlap = customtkinter.IntVar(value=2)
        self.excluded_artist = customtkinter.StringVar(value="")
        self.groups = []
        self.current_mode = "ratio"
        self.blacklist = load_blacklist()
        self.lang = "es"
        self.translations = load_translations()
        self.language_names = self.translations.get("LANGUAGES", {})

        self.build_ui()

        style = ttk.Style(self.root)
        style.theme_use("clam")  # "clam" permite más personalización

        style.configure(
            "Treeview",
            background="#222222",      # Fondo oscuro
            foreground="#EEEEEE",      # Texto claro
            fieldbackground="#222222", # Fondo de celdas
            rowheight=28,              # Opcional: altura de filas
            bordercolor="#222222",
            borderwidth=0
        )
        style.configure(
            "Treeview.Heading",
            background="#222222",
            foreground="#EEEEEE",
            relief="flat"
        )
        style.map(
            "Treeview",
            background=[("selected", "#444444")],  # Color de selección
            foreground=[("selected", "#FFFFFF")]
        )


    def build_ui(self):
        control_frame = customtkinter.CTkFrame(self.root)
        # Botón de configuración (sidebar)
        config_btn = customtkinter.CTkButton(self.root, text="⚙️", width=40, command=self.toggle_sidebar)
        config_btn.place(x=10, y=10)
        control_frame.pack(pady=10, padx=20, anchor='center')
        
        # Fila 1: Seleccionar carpeta
        customtkinter.CTkButton(control_frame, text=t("select_folder", self.lang, self.translations), command=self.select_folder, width=30).grid(row=0, column=0, padx=5, pady=5)

        # Fila 2: Buscar por porcentaje
        customtkinter.CTkLabel(control_frame, text=t("similarity_label", self.lang, self.translations)).grid(row=1, column=0, sticky="w", padx=5)
        customtkinter.CTkEntry(control_frame, textvariable=self.threshold, width=40).grid(row=1, column=1, padx=5)
        customtkinter.CTkButton(control_frame, text=t("search_ratio", self.lang, self.translations), command=lambda: analyze_by_ratio(self), width=30).grid(row=1, column=2, padx=5, pady=5)

        # Fila 3: Buscar por palabras
        customtkinter.CTkLabel(control_frame, text=t("min_common_words", self.lang, self.translations)).grid(row=2, column=0, sticky="w", padx=5)
        customtkinter.CTkEntry(control_frame, textvariable=self.min_overlap, width=40).grid(row=2, column=1, padx=5)
        customtkinter.CTkButton(control_frame, text=t("search_words", self.lang, self.translations), command=lambda: analyze_by_words(self), width=30).grid(row=2, column=2, padx=5, pady=5)

        # Fila 4: Buscar no artista
        customtkinter.CTkLabel(control_frame, text=t("exclude_artist", self.lang, self.translations)).grid(row=3, column=0, sticky="w", padx=5)
        customtkinter.CTkEntry(control_frame, textvariable=self.excluded_artist, width=120).grid(row=3, column=1, padx=5)
        customtkinter.CTkButton(control_frame, text=t("search_not_artist", self.lang, self.translations), command=lambda: analyze_excluding_artist(self), width=30).grid(row=3, column=2, padx=5, pady=5)

        # Fila 5: Editar blacklist
        customtkinter.CTkButton(control_frame, text=t("edit_blacklist", self.lang, self.translations), command=self.open_blacklist_editor, width=30).grid(row=4, column=0, padx=5, pady=5)

        # Fila 6: Exportar CSV
        customtkinter.CTkButton(control_frame, text=t("export_csv", self.lang, self.translations), command=lambda: export_csv(self), width=30).grid(row=4, column=1, padx=5, pady=5)

        # Fila 7: Ayuda
        customtkinter.CTkButton(control_frame, text=t("help", self.lang, self.translations), command=self.show_help, width=30).grid(row=4, column=2, padx=5, pady=5)


        # Tabla
        self.tree = ttk.Treeview(self.root, columns=("Grupo",), show="headings", selectmode="extended")
        self.tree.heading("Grupo", text=t("similar_songs", self.lang, self.translations))
        self.tree.column("Grupo", width=800)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        self.tree.pack(padx=10, pady=10, fill='both', expand=True)

    def refresh_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.build_ui()

    # Toggle sidebar
    def toggle_sidebar(self):
        if self.sidebar_visible:
            if self.sidebar_frame:
                self.sidebar_frame.destroy()
            self.sidebar_visible = False
        else:
            self.sidebar_frame = customtkinter.CTkFrame(self.root, width=200, corner_radius=0)
            self.sidebar_frame.place(x=0, y=0, relheight=1)
            # Botón para cerrar
            close_btn = customtkinter.CTkButton(self.sidebar_frame, text="✖", width=10, command=self.toggle_sidebar)
            close_btn.pack(pady=(10, 20), padx=16, anchor="ne")  # <-- margen exterior horizontal
            # Selector de idioma
            lang_label = customtkinter.CTkLabel(self.sidebar_frame, text=t("change_language", self.lang, self.translations))
            lang_label.pack(pady=(20, 10), padx=16)  # <-- margen exterior horizontal

            lang_option = customtkinter.CTkOptionMenu(
                self.sidebar_frame,
                values=list(self.language_names.values()),
                command=self.set_language_full
            )
            lang_option.set(self.language_names[self.lang])
            lang_option.pack(pady=10, padx=16)  # <-- margen exterior horizontal
            
            self.sidebar_visible = True

    def set_language_full(self, lang_name):
        for code, name in self.language_names.items():
            if name == lang_name:
                self.lang = code
                break
        self.refresh_ui()
        self.toggle_sidebar()

    # Show groups in treeview
    def show_groups_in_tree(self, groups, formatter=None):
        self.tree.delete(*self.tree.get_children())
        if not groups:
            CTkMessagebox(title=t("no_coincidence", self.lang, self.translations), message=t("no_coincidence_text", self.lang, self.translations))
            return
        for idx, group in enumerate(groups):
            if formatter:
                names = formatter(group)
            else:
                names = ",  ".join([t for t, _, _ in group])
            self.tree.insert('', 'end', iid=idx, values=(names,))

    # Open blacklist editor
    def open_blacklist_editor(self):
        editor = customtkinter.CTkToplevel(self.root)
        editor.title(t("edit_blacklist", self.lang, self.translations))
        editor.geometry("400x500")
        editor.transient(self.root)      # <-- Asociar a la ventana principal
        editor.grab_set()                # <-- Hacer modal
        editor.focus()                   # <-- Darle el foco

        frame = customtkinter.CTkFrame(editor)
        frame.pack(fill='both', expand=True, padx=10, pady=10)


        # Entrada para nueva palabra
        add_frame = customtkinter.CTkFrame(editor)
        add_frame.pack(pady=(0,10))

        new_word_var = customtkinter.StringVar()
        customtkinter.CTkEntry(add_frame, textvariable=new_word_var, width=200).pack(side=tk.LEFT, padx=5)
        customtkinter.CTkButton(add_frame, text=t("add_word", self.lang, self.translations), command=lambda: add_word(new_word_var, self, frame)).pack(side=tk.LEFT)
        # Inicializar los checkboxes
        refresh_checkboxes(frame, self)

        # Guardar y cerrar
        customtkinter.CTkButton(editor, text=t("save_close", self.lang, self.translations), command=lambda: save_and_close(editor, self)).pack(pady=10)

    
    def show_help(self):
        msg = (
            f"{t('help_text', self.lang, self.translations)}\n\n"
        )
        CTkMessagebox(title=t("help_multiple_files", self.lang, self.translations), message=msg)

    def on_right_click(self, event):
        selected = self.tree.selection()
        if self.current_mode != "not_artist" or not selected:
            return

        menu = customtkinter.CTkMenu(self.root, tearoff=0)
        menu.add_command(label="🗑️ Eliminar grupo(s)", command=lambda: self.delete_selected_groups(selected))
        menu.tk_popup(event.x_root, event.y_root)

    def delete_selected_groups(self, selected):
        confirm = CTkMessagebox(title=t("confirm_delete", self.lang, self.translations), message=t("confirm_delete_text", self.lang, self.translations), option_1="Yes", option_2="No", icon="warning")
        if not confirm == "Yes":
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
            CTkMessagebox(title=t("select_folder", self.lang, self.translations), message=self.folder)


    def on_double_click(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_indices = [int(item) for item in selected_items]
        selected_groups = [self.groups[idx] for idx in selected_indices]

        win = customtkinter.CTkToplevel(self.root)
        win.title(t("group_action", self.lang, self.translations))
        win.geometry("900x300")
        win.configure(fg_color="#444444")  # Fondo dark

        h_scroll = tk.Scrollbar(win, orient="horizontal")
        h_scroll.pack(side="bottom", fill="x")

        canvas = customtkinter.CTkCanvas(win, xscrollcommand=h_scroll.set, bg="#444444", highlightthickness=0)
        canvas.pack(side="top", fill="both", expand=True)
        h_scroll.config(command=canvas.xview)

        content_frame = customtkinter.CTkFrame(canvas, fg_color="#444444")  # Fondo dark
        canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def delete_all():
            confirm = CTkMessagebox(title=t("delete_all", self.lang, self.translations), message=t("delete_all_text", self.lang, self.translations), option_1="Yes", option_2="No", icon="warning")
            if confirm.get() == "Yes":
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
                    analyze_by_ratio(self)

        for group in selected_groups:
            for title, path, artist in group:
                sub = customtkinter.CTkFrame(content_frame, fg_color="#222222")
                sub.pack(side="left", padx=10, pady=5)
                customtkinter.CTkLabel(sub, text=title, wraplength=150).pack(pady=2)
                customtkinter.CTkLabel(sub, text=f"👤 {artist}", wraplength=150).pack(pady=2)
                customtkinter.CTkButton(sub, text=t("reproduce", self.lang, self.translations), command=lambda p=path: play(p)).pack(pady=2, padx=5, fill="x")
                customtkinter.CTkButton(sub, text=t("move_to_trash", self.lang, self.translations), command=lambda p=path: self.delete(p, win)).pack(pady=5, padx=5, fill="x")

        if self.current_mode == "not_artist":
            customtkinter.CTkButton(content_frame, text=t("delete_entire_group", self.lang, self.translations), command=delete_all, fg_color="red", text_color="white").pack(pady=10)

        content_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))


    def delete(self, filepath, window=None):
        confirm = CTkMessagebox(
            title=t("move_to_trash", self.lang, self.translations),
            message=t("move_to_trash_text", self.lang, self.translations).format(filepath=filepath),
            option_1="Yes", option_2="No", icon="warning"
        )
        if confirm.get() == "Yes":
            try:
                if not os.path.exists(filepath):
                    CTkMessagebox(
                        title=t("file_not_found", self.lang, self.translations),
                        message=t("file_not_found_text", self.lang, self.translations).format(filepath=filepath),
                        icon="cancel"
                    )
                    return
                send2trash(str(Path(filepath)))
                CTkMessagebox(
                    title=t("deleted", self.lang, self.translations),
                    message=t("deleted_text", self.lang, self.translations).format(filepath=filepath)
                )
                if window:
                    window.destroy()
                if self.current_mode == "ratio":
                    analyze_by_ratio(self)
                elif self.current_mode == "words":
                    analyze_by_words(self)
                elif self.current_mode == "not_artist":
                    analyze_excluding_artist(self)
            except Exception as e:
                CTkMessagebox(
                    title="Error",
                    message=t("trash_error", self.lang, self.translations).format(e=e),
                    icon="cancel"
                )
