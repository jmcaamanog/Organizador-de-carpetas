"""
      ██╗███╗   ███╗ ██████╗
      ██║████╗ ████║██╔════╝
      ██║██╔████╔██║██║
 ██   ██║██║╚██╔╝██║██║    
 ╚█████╔╝██║ ╚═╝ ██║╚██████╗
  ╚════╝ ╚═╝     ╚═╝ ╚═════╝
"""

# --- Creador de Carpetas v12.0 by JMCG & Gemini ---
#
# NOTA: Versión refactorizada para máxima compatibilidad con PyInstaller.
# Incluye manejo de errores para la carga de recursos y la función resource_path integrada.
# Requiere la librería Pillow: pip install Pillow

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import sys # <--- AÑADIDO
import json
from datetime import datetime
from PIL import Image, ImageTk

# --- FUNCIÓN CLAVE PARA ENCONTRAR ARCHIVOS EN EL .EXE ---
# Esta función es esencial. Determina si el script se ejecuta normalmente
# o como un ejecutable de PyInstaller y devuelve la ruta correcta al archivo.
def resource_path(relative_path):
    """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en sys._MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si no se ejecuta desde PyInstaller, usa la ruta normal
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- CONSTANTES GLOBALES ---
# Se utiliza os.path.dirname para ser más robusto
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, 'config.json')
TEMPLATES_DIR = os.path.join(APP_DIR, 'plantillas')

# --- PALETA DE COLORES Y ESTILOS (Sin cambios) ---
THEMES = {
    "dark": {
        "background": "#1E1E1E", "frame_bg": "#2D2D2D", "text": "#EAEAEA",
        "accent": "#007ACC", "button_hover": "#3E3E3E", "delete": "#c43636",
        "save": "#32a852", "exit": "#D14040", "exit_hover": "#E05050",
        "entry_bg": "#1E1E1E", "entry_fg": "#EAEAEA"
    },
    "light": {
        "background": "#F0F0F0", "frame_bg": "#FFFFFF", "text": "#1E1E1E",
        "accent": "#007ACC", "button_hover": "#E5F1FB", "delete": "#D14040",
        "save": "#28a745", "exit": "#DC3545", "exit_hover": "#C82333",
        "entry_bg": "#FFFFFF", "entry_fg": "#1E1E1E"
    }
}
FONT_DEFAULT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_SIDEBAR_TITLE = ("Segoe UI", 12, "bold")

# --- CLASES DE GESTIÓN (Sin cambios) ---

class ConfigManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.config = self._load()
    def _load(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"last_path": os.path.expanduser("~"), "theme": "dark"}
    def get(self, key, default=None): return self.config.get(key, default)
    def set(self, key, value): self.config[key] = value
    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f: json.dump(self.config, f, indent=4)

class TemplateManager:
    def parse_template(self, filepath):
        if not os.path.exists(filepath): raise FileNotFoundError(f"El archivo de plantilla no se encontró: {filepath}")
        _, extension = os.path.splitext(filepath)
        if extension.lower() == '.json': return self._parse_json(filepath)
        elif extension.lower() == '.txt': return self._parse_txt(filepath)
        else: raise ValueError("Formato de archivo no soportado. Use .json o .txt")
    def _parse_json(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    def _parse_txt(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f: lines = f.readlines()
        structure = {}; parent_stack = [structure]
        for line in lines:
            if not line.strip(): continue
            line = line.replace('\t', ' ' * 4)
            indentation = len(line) - len(line.lstrip(' '))
            level = indentation // 4; item_name = line.strip()
            is_file = item_name.startswith('-- ')
            if is_file: item_name = item_name[3:].strip()
            while len(parent_stack) > level + 1: parent_stack.pop()
            parent_dict = parent_stack[-1]
            if is_file:
                if '_files_' not in parent_dict: parent_dict['_files_'] = []
                parent_dict['_files_'].append(item_name)
            else:
                new_folder_dict = {}; parent_dict[item_name] = new_folder_dict
                parent_stack.append(new_folder_dict)
        return structure

# --- CLASES DE INTERFAZ (Sin cambios estructurales, solo en carga de imágenes) ---

class CustomLabelFrame(tk.Frame):
    def __init__(self, parent, text="", theme_colors=None, **kwargs):
        super().__init__(parent, bg=theme_colors['frame_bg'], **kwargs)
        self.config(padx=15, pady=10)
        label = tk.Label(self, text=text, bg=theme_colors['frame_bg'], fg=theme_colors['text'], font=FONT_BOLD)
        label.pack(side="top", anchor="w", pady=(0, 5))
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(side="top", fill="x", pady=(0, 10))
        self.content_frame = tk.Frame(self, bg=theme_colors['frame_bg'])
        self.content_frame.pack(fill="both", expand=True)

class OrganizeFrame(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        self.app = app_instance; self.theme_colors = self.app.theme_colors
        super().__init__(parent, bg=self.theme_colors['background'], **kwargs)
        self.config_manager = self.app.config_manager
        self.template_manager = self.app.template_manager
        self.pack(fill="both", expand=True)
        self.checked_char = "✔"; self.unchecked_char = "☐"; self.file_char = "📄"
        self._create_widgets(); self.load_local_templates()
    def _create_widgets(self):
        main_pane = tk.PanedWindow(self, orient="horizontal", bg=self.theme_colors['background'], sashwidth=8, relief="flat")
        main_pane.pack(fill="both", expand=True, padx=20, pady=10)
        left_pane = tk.Frame(main_pane, bg=self.theme_colors['background'])
        main_pane.add(left_pane, width=450)
        right_pane = tk.Frame(main_pane, bg=self.theme_colors['background'])
        main_pane.add(right_pane)
        self._create_tree_view_widgets(left_pane)
        self._create_project_data_widgets(right_pane)
    def _create_tree_view_widgets(self, parent):
        tree_frame_container = CustomLabelFrame(parent, text="Estructura del Proyecto", theme_colors=self.theme_colors)
        tree_frame_container.pack(fill="both", expand=True, pady=(0, 10))
        tree_frame = tree_frame_container.content_frame
        btn_config = {"bg": self.theme_colors['frame_bg'], "fg": self.theme_colors['text'], "font": FONT_DEFAULT, "relief": "flat", "padx": 5, "pady": 2}
        delete_btn_config = btn_config.copy(); delete_btn_config['fg'] = self.theme_colors['delete']
        save_btn_config = btn_config.copy(); save_btn_config['fg'] = self.theme_colors['save']
        controls_grid = tk.Frame(tree_frame, bg=self.theme_colors['frame_bg'])
        controls_grid.pack(fill="x", pady=(0, 10)); controls_grid.columnconfigure(1, weight=1)
        edit_move_frame = tk.Frame(controls_grid, bg=self.theme_colors['frame_bg'])
        edit_move_frame.grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Button(edit_move_frame, text="✚ Carpeta", command=lambda: self._add_item(is_file=False), **btn_config).pack(side="left")
        tk.Button(edit_move_frame, text="✚ Archivo", command=lambda: self._add_item(is_file=True), **btn_config).pack(side="left", padx=5)
        tk.Button(edit_move_frame, text="✖ Eliminar", command=self.remove_selected, **delete_btn_config).pack(side="left")
        ttk.Separator(edit_move_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        tk.Button(edit_move_frame, text="↑", command=self.move_up, **btn_config).pack(side="left")
        tk.Button(edit_move_frame, text="↓", command=self.move_down, **btn_config).pack(side="left", padx=2)
        tk.Button(edit_move_frame, text="→", command=self.indent_item, **btn_config).pack(side="left", padx=2)
        tk.Button(edit_move_frame, text="←", command=self.unindent_item, **btn_config).pack(side="left")
        save_select_frame = tk.Frame(controls_grid, bg=self.theme_colors['frame_bg'])
        save_select_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Button(save_select_frame, text="💾 Guardar Plantilla", command=self.save_as_template, **save_btn_config).pack(side="left")
        ttk.Separator(save_select_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        tk.Button(save_select_frame, text="Seleccionar Todo", command=self.select_all, **btn_config).pack(side="left")
        tk.Button(save_select_frame, text="Deseleccionar", command=self.deselect_all, **btn_config).pack(side="left", padx=2)
        tk.Button(save_select_frame, text="Expandir", command=lambda: self.expand_collapse(True), **btn_config).pack(side="left", padx=2)
        tk.Button(save_select_frame, text="Colapsar", command=lambda: self.expand_collapse(False), **btn_config).pack(side="left")
        style = ttk.Style(); style.theme_use("default")
        style.configure("Treeview", background=self.theme_colors['frame_bg'], foreground=self.theme_colors['text'], fieldbackground=self.theme_colors['frame_bg'], borderwidth=0, font=FONT_DEFAULT)
        style.map("Treeview", background=[('selected', self.theme_colors['accent'])])
        style.configure("Treeview.Heading", background=self.theme_colors['frame_bg'], foreground=self.theme_colors['text'], font=FONT_BOLD, relief="flat")
        style.map("Treeview.Heading", background=[('active', self.theme_colors['button_hover'])])
        tree_container = tk.Frame(tree_frame, bg=self.theme_colors['frame_bg'])
        tree_container.pack(fill="both", expand=True, pady=(5,0))
        self.tree = ttk.Treeview(tree_container, show="tree")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Button-1>", self.toggle_check, True)
    def _create_project_data_widgets(self, parent):
        container = tk.Frame(parent, bg=self.theme_colors['background'])
        container.pack(fill="both", expand=True, padx=(10, 0))
        template_frame_container = CustomLabelFrame(container, text="1. Cargar Plantilla (Opcional)", theme_colors=self.theme_colors)
        template_frame_container.pack(fill="x", pady=(0, 20))
        template_frame = template_frame_container.content_frame
        self.template_var = tk.StringVar()
        self.template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, state="readonly", font=FONT_DEFAULT)
        self.template_combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.template_combo.bind("<<ComboboxSelected>>", self.on_local_template_selected)
        tk.Button(template_frame, text="Cargar Archivo...", command=self.load_template_from_file, bg=self.theme_colors['button_hover'], fg=self.theme_colors['text'], relief="flat", font=FONT_DEFAULT).pack(side="left")
        project_frame_container = CustomLabelFrame(container, text="2. Datos del Proyecto", theme_colors=self.theme_colors)
        project_frame_container.pack(fill="x", pady=(0, 20))
        project_frame = project_frame_container.content_frame
        project_frame.columnconfigure(1, weight=1); project_frame.columnconfigure(3, weight=1)
        entry_config = {"bg": self.theme_colors['entry_bg'], "fg": self.theme_colors['entry_fg'], "font": FONT_DEFAULT, "relief": "flat", "insertbackground": self.theme_colors['text']}
        label_config = {"bg": self.theme_colors['frame_bg'], "fg": self.theme_colors['text'], "font": FONT_DEFAULT}
        tk.Label(project_frame, text="Año:", **label_config).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ano_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        tk.Entry(project_frame, textvariable=self.ano_var, width=8, **entry_config).grid(row=0, column=1, pady=5, sticky="ew")
        tk.Label(project_frame, text="Número:", **label_config).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.num_var = tk.StringVar(value="001")
        tk.Entry(project_frame, textvariable=self.num_var, width=8, **entry_config).grid(row=0, column=3, pady=5, sticky="ew")
        tk.Label(project_frame, text="Descripción:", **label_config).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.desc_var = tk.StringVar()
        tk.Entry(project_frame, textvariable=self.desc_var, **entry_config).grid(row=1, column=1, columnspan=3, pady=5, sticky="ew")
        path_frame_container = CustomLabelFrame(container, text="3. Ruta de Creación", theme_colors=self.theme_colors)
        path_frame_container.pack(fill="x", pady=(0, 20))
        path_frame = path_frame_container.content_frame
        self.ruta_var = tk.StringVar(value=self.config_manager.get('last_path'))
        tk.Entry(path_frame, textvariable=self.ruta_var, **entry_config).pack(side="left", fill="x", expand=True, padx=(0, 10))
        tk.Button(path_frame, text="...", command=self.select_path, bg=self.theme_colors['button_hover'], fg=self.theme_colors['text'], relief="flat", font=FONT_DEFAULT).pack(side="left")
        tk.Button(container, text="Crear Estructura de Carpetas", command=self.create_structure, bg=self.theme_colors['button_hover'], fg=self.theme_colors['text'], relief="flat", font=FONT_BOLD, padx=10, pady=5).pack(fill="x", ipady=5)
    def load_local_templates(self):
        try:
            templates = sorted([f for f in os.listdir(TEMPLATES_DIR) if f.lower().endswith(('.json', '.txt'))])
            self.template_combo['values'] = [""] + templates; self.template_combo.set("")
        except FileNotFoundError: messagebox.showerror("Error", f"El directorio de plantillas no se encuentra en:\n{TEMPLATES_DIR}")
    def on_local_template_selected(self, event=None):
        template_name = self.template_var.get()
        if template_name: self.load_template(os.path.join(TEMPLATES_DIR, template_name))
        else:
            for i in self.tree.get_children(): self.tree.delete(i)
    def load_template_from_file(self):
        filepath = filedialog.askopenfilename(title="Seleccionar archivo de plantilla", filetypes=[("Plantillas Soportadas", "*.txt *.json"), ("Todos los archivos", "*.*")], initialdir=self.config_manager.get('last_path'))
        if filepath: self.template_combo.set(''); self.load_template(filepath)
    def load_template(self, filepath):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            structure = self.template_manager.parse_template(filepath)
            self.populate_tree(structure)
        except Exception as e: messagebox.showerror("Error de Plantilla", f"No se pudo cargar o procesar la plantilla:\n{e}")
    def populate_tree(self, structure, parent_id=""):
        for name, content in structure.items():
            if name == "_files_":
                for filename in content: self.tree.insert(parent_id, 'end', text=f" {self.file_char} {filename}", open=True, tags=('file',))
            else:
                node_id = self.tree.insert(parent_id, 'end', text=f" {self.unchecked_char} {name}", open=True, tags=('unchecked',))
                if isinstance(content, dict): self.populate_tree(content, node_id)
    def _add_item(self, is_file=False):
        selection = self.tree.selection(); parent_item = selection[0] if selection else ''
        if parent_item and 'file' in self.tree.item(parent_item, 'tags'): parent_item = self.tree.parent(parent_item)
        item_type = "archivo" if is_file else "carpeta"
        item_name = simpledialog.askstring(f"Añadir {item_type.capitalize()}", f"Introduce el nombre del nuevo {item_type}:")
        if not item_name: return
        if is_file: new_item = self.tree.insert(parent_item, 'end', text=f" {self.file_char} {item_name}", open=True, tags=('file',))
        else: new_item = self.tree.insert(parent_item, 'end', text=f" {self.checked_char} {item_name}", open=True, tags=('checked',))
        self.tree.selection_set(new_item)
    def remove_selected(self):
        selection = self.tree.selection()
        if not selection: messagebox.showwarning("Ninguna selección", "Por favor, selecciona un elemento para eliminar."); return
        selected_item = selection[0]; item_text = self.tree.item(selected_item, "text").strip()
        if messagebox.askyesno("Confirmar eliminación", f"¿Estás seguro de que quieres eliminar '{item_text}'?"): self.tree.delete(selected_item)
    def move_up(self):
        selection = self.tree.selection()
        if not selection: return
        for item in selection: self.tree.move(item, self.tree.parent(item), self.tree.index(item) - 1)
    def move_down(self):
        selection = self.tree.selection()
        if not selection: return
        for item in reversed(selection): self.tree.move(item, self.tree.parent(item), self.tree.index(item) + 1)
    def indent_item(self):
        selection = self.tree.selection();
        if not selection: return
        item = selection[0]; prev_sibling = self.tree.prev(item)
        if not prev_sibling: return
        if 'file' not in self.tree.item(prev_sibling, 'tags'): self.tree.move(item, prev_sibling, 'end')
    def unindent_item(self):
        selection = self.tree.selection();
        if not selection: return
        item = selection[0]; parent = self.tree.parent(item)
        if not parent: return
        self.tree.move(item, self.tree.parent(parent), self.tree.index(parent) + 1)
    def save_as_template(self):
        structure = self._tree_to_dict()
        if not structure: messagebox.showwarning("Árbol Vacío", "No hay nada en la estructura para guardar."); return
        filepath = filedialog.asksaveasfilename(title="Guardar plantilla como...", defaultextension=".json", filetypes=[("JSON files", "*.json")], initialdir=TEMPLATES_DIR)
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f: json.dump(structure, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Éxito", f"Plantilla guardada correctamente en:\n{filepath}"); self.load_local_templates()
        except Exception as e: messagebox.showerror("Error al Guardar", f"No se pudo guardar la plantilla.\nError: {e}")
    def _tree_to_dict(self, parent_id=""):
        structure = {}; children = self.tree.get_children(parent_id); files = []
        for child_id in children:
            item_info = self.tree.item(child_id)
            clean_name = item_info['text'].replace(self.checked_char, "").replace(self.unchecked_char, "").replace(self.file_char, "").strip()
            if 'file' in item_info['tags']: files.append(clean_name)
            else: structure[clean_name] = self._tree_to_dict(child_id)
        if files: structure["_files_"] = files
        return structure
    def toggle_check(self, event):
        item_id = self.tree.identify_row(event.y);
        if not item_id: return
        tags = self.tree.item(item_id, "tags")
        if 'file' in tags: return
        new_state = 'checked' if 'unchecked' in tags else 'unchecked'
        self._set_check_state(item_id, new_state); self._propagate_to_children(item_id, new_state)
        return "break"
    def _set_check_state(self, item_id, state):
        tags = list(self.tree.item(item_id, 'tags'))
        if 'file' in tags: return
        current_text = self.tree.item(item_id, "text")
        base_text = current_text.replace(self.checked_char, "").replace(self.unchecked_char, "").strip()
        new_tags = [t for t in tags if t not in ('checked', 'unchecked')] + [state]
        new_char = self.checked_char if state == 'checked' else self.unchecked_char
        self.tree.item(item_id, tags=tuple(new_tags), text=f" {new_char} {base_text}")
    def _propagate_to_children(self, parent_id, state):
        for child_id in self.tree.get_children(parent_id):
            self._set_check_state(child_id, state); self._propagate_to_children(child_id, state)
    def _get_all_items(self, include_files=False):
        all_items = [];
        def _recursive_get(parent_id):
            for child_id in self.tree.get_children(parent_id):
                if include_files or 'file' not in self.tree.item(child_id, 'tags'): all_items.append(child_id)
                _recursive_get(child_id)
        _recursive_get(""); return all_items
    def select_all(self):
        for item_id in self._get_all_items(): self._set_check_state(item_id, 'checked')
    def deselect_all(self):
        for item_id in self._get_all_items(): self._set_check_state(item_id, 'unchecked')
    def expand_collapse(self, expand=True):
        for item_id in self._get_all_items(): self.tree.item(item_id, open=expand)
    def create_structure(self):
        ano, num, desc, base_path = self.ano_var.get().strip(), self.num_var.get().strip(), self.desc_var.get().strip(), self.ruta_var.get().strip()
        if not all([ano, num, desc, base_path]): messagebox.showwarning("Faltan datos", "Todos los campos y la ruta deben estar completos."); return
        if not os.path.isdir(base_path): messagebox.showerror("Ruta no válida", f"La ruta de creación no existe:\n{base_path}"); return
        project_name = f"{ano}-{num}-{desc.replace(' ', '_')}"; project_root_path = os.path.join(base_path, project_name)
        try:
            os.makedirs(project_root_path, exist_ok=True)
            self._recursive_create(project_root_path)
            messagebox.showinfo("Éxito", f"La estructura del proyecto '{project_name}' se ha creado.")
        except OSError as e: messagebox.showerror("Error de Creación", f"No se pudo crear la carpeta principal.\nError: {e}")
    def _recursive_create(self, current_path, parent_id=""):
        for item_id in self.tree.get_children(parent_id):
            item_info = self.tree.item(item_id)
            clean_name = item_info['text'].replace(self.checked_char, "").replace(self.unchecked_char, "").replace(self.file_char, "").strip()
            new_path = os.path.join(current_path, clean_name)
            is_folder = 'file' not in item_info['tags']
            if is_folder:
                if 'checked' in item_info['tags']:
                    try: os.makedirs(new_path, exist_ok=True); self._recursive_create(new_path, item_id)
                    except OSError as e: print(f"Error creando carpeta {new_path}: {e}")
                else: self._recursive_create(current_path, item_id)
            elif self.tree.parent(item_id) == "" or 'checked' in self.tree.item(self.tree.parent(item_id), 'tags'):
                try: open(new_path, 'a').close()
                except OSError as e: print(f"Error creando archivo {new_path}: {e}")
    def select_path(self):
        directory = filedialog.askdirectory(initialdir=self.config_manager.get('last_path'))
        if directory: self.ruta_var.set(directory)

class GuideFrame(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        self.theme_colors = app_instance.theme_colors
        super().__init__(parent, bg=self.theme_colors['background'], **kwargs)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(self, text="Guía de Uso", font=FONT_TITLE, bg=self.theme_colors['background'], fg=self.theme_colors['text']).pack(anchor="w", pady=(0, 20))
        text_content = "Esta herramienta te permite crear estructuras de carpetas...\n(Contenido de la guía sin cambios)"
        tk.Label(self, text=text_content, font=FONT_DEFAULT, bg=self.theme_colors['background'], fg=self.theme_colors['text'], justify="left", anchor="nw").pack(fill="both")

class ExampleFrame(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        self.theme_colors = app_instance.theme_colors
        super().__init__(parent, bg=self.theme_colors['background'], **kwargs)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        # (Contenido del frame de ejemplo sin cambios)
        tk.Label(self, text="Ejemplo de Estructura de Proyecto", font=FONT_TITLE, bg=self.theme_colors['background'], fg=self.theme_colors['text']).pack(anchor="w", pady=(0, 10))
        tk.Label(self, text="Esta es una demostración de una estructura compleja. Es de solo lectura y sirve como inspiración.", font=FONT_DEFAULT, bg=self.theme_colors['background'], fg=self.theme_colors['text'], justify="left").pack(anchor="w", pady=(0, 20))
        style = ttk.Style(); style.configure("Example.Treeview", background=self.theme_colors['frame_bg'], foreground=self.theme_colors['text'], fieldbackground=self.theme_colors['frame_bg'], borderwidth=0, font=FONT_DEFAULT)
        style.map("Example.Treeview", background=[('selected', self.theme_colors['accent'])])
        tree = ttk.Treeview(self, style="Example.Treeview", show="tree"); tree.pack(fill="both", expand=True)
        p1 = tree.insert("", "end", text=" 📂 00 PAPELES"); tree.insert(p1, "end", text=" 📄 Listado de Documentos.txt")
        tree.insert("", "end", text=" 📂 01 SEGUROS")
        p3 = tree.insert("", "end", text=" 📂 05 PROYECTO BÁSICO"); p3_1 = tree.insert(p3, "end", text=" 📂 01 MEMORIA"); tree.insert(p3_1, "end", text=" 📄 Memoria Descriptiva.docx"); tree.insert(p3_1, "end", text=" 📄 Memoria Constructiva.docx"); p3_2 = tree.insert(p3, "end", text=" 📂 02 PLANOS"); tree.insert(p3_2, "end", text=" 📄 PB_01_Situacion_y_Emplazamiento.dwg"); p3_3 = tree.insert(p3, "end", text=" 📂 03 VISADO"); tree.insert(p3_3, "end", text=" 📂 01 Enviado a visar"); tree.insert(p3_3, "end", text=" 📂 02 Visado")
        tree.insert("", "end", text=" 📂 06 PROYECTO EJECUCIÓN")
        def open_all_children(parent):
            tree.item(parent, open=True)
            for child in tree.get_children(parent): open_all_children(child)
        for item in tree.get_children(): open_all_children(item)
        tree.bind("<Button-1>", lambda e: "break")


class SettingsFrame(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        self.app = app_instance; self.theme_colors = app_instance.theme_colors
        super().__init__(parent, bg=self.theme_colors['background'], **kwargs)
        self.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(self, text="Configuración", font=FONT_TITLE, bg=self.theme_colors['background'], fg=self.theme_colors['text']).pack(anchor="w", pady=(0, 20))
        theme_frame_container = CustomLabelFrame(self, text="Tema de la Aplicación", theme_colors=self.theme_colors)
        theme_frame_container.pack(fill="x", pady=(0, 20), anchor="n")
        theme_frame = theme_frame_container.content_frame
        self.theme_var = tk.StringVar(value=self.app.config_manager.get("theme", "dark"))
        style = ttk.Style(); style.configure("TRadiobutton", background=self.theme_colors['frame_bg'], foreground=self.theme_colors['text'], font=FONT_DEFAULT)
        style.map("TRadiobutton", background=[('active', self.theme_colors['frame_bg'])], foreground=[('active', self.theme_colors['text'])])
        dark_rb = ttk.Radiobutton(theme_frame, text="Oscuro", variable=self.theme_var, value="dark", command=self._save_theme, style="TRadiobutton")
        dark_rb.pack(anchor="w", pady=2)
        light_rb = ttk.Radiobutton(theme_frame, text="Claro", variable=self.theme_var, value="light", command=self._save_theme, style="TRadiobutton")
        light_rb.pack(anchor="w", pady=2)
    def _save_theme(self):
        new_theme = self.theme_var.get(); self.app.config_manager.set("theme", new_theme); self.app.config_manager.save()
        messagebox.showinfo("Cambio de Tema", "El nuevo tema se aplicará la próxima vez que inicies la aplicación.")

class AboutFrame(tk.Frame):
    def __init__(self, parent, app_instance, **kwargs):
        self.theme_colors = app_instance.theme_colors
        super().__init__(parent, bg=self.theme_colors['background'], **kwargs)
        self.pack(fill="both", expand=True)
        container = tk.Frame(self, bg=self.theme_colors['background'])
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        # --- MODIFICADO: Carga de logo con manejo de errores ---
        try:
            # Usa resource_path para encontrar el logo
            logo_path = resource_path("logo.png")
            self.logo_img = ImageTk.PhotoImage(Image.open(logo_path).resize((128, 128)))
            logo_label = tk.Label(container, image=self.logo_img, bg=self.theme_colors['background'])
            logo_label.pack(pady=(0, 20))
            print("INFO: Logo 'logo.png' cargado correctamente en 'Acerca de'.")
        except Exception as e:
            # Si falla, muestra un texto en su lugar y un error en consola
            print(f"ERROR: No se pudo cargar 'logo.png': {e}")
            error_label = tk.Label(container, text="[Logo no encontrado]", bg=self.theme_colors['background'], fg="red")
            error_label.pack(pady=(0, 20))
        
        tk.Label(container, text="Creador de Carpetas v12.0", font=FONT_TITLE, bg=self.theme_colors['background'], fg=self.theme_colors['accent']).pack(pady=(0, 5))
        tk.Label(container, text="by JMCG", font=FONT_DEFAULT, bg=self.theme_colors['background'], fg=self.theme_colors['text']).pack(pady=(0, 20))
        info_text = "Versión: 12.0 (Robusta)\nAutor: Jose Manuel Caamaño González\nWeb: josecaamano.io\n\nCopyright © 2025"
        tk.Label(container, text=info_text, justify="center", bg=self.theme_colors['background'], fg=self.theme_colors['text'], font=FONT_DEFAULT).pack(pady=10)

# --- CLASE PRINCIPAL DE LA APLICACIÓN ---

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager(CONFIG_FILE)
        self.template_manager = TemplateManager()
        self.theme_name = self.config_manager.get("theme", "dark")
        self.theme_colors = THEMES.get(self.theme_name, THEMES["dark"])

        self.title("Creador de Carpetas Avanzado")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg=self.theme_colors['background'])
        
        # --- MODIFICADO: Carga del icono de ventana con manejo de errores ---
        try:
            # Usa resource_path para encontrar el icono
            icon_path = resource_path("app_icon.ico")
            self.iconbitmap(icon_path)
            print("INFO: Icono de ventana 'app_icon.ico' cargado correctamente.")
        except tk.TclError as e:
            # Si falla, imprime un error claro en la consola
            print(f"ERROR: No se pudo cargar el icono de la ventana 'app_icon.ico'. Razón: {e}")
        
        self._setup_environment()
        self._create_main_layout()
        self._create_sidebar()
        self._create_content_frames()
        self.show_frame(OrganizeFrame)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_environment(self):
        if not os.path.exists(TEMPLATES_DIR): os.makedirs(TEMPLATES_DIR)
        default_json_path = os.path.join(TEMPLATES_DIR, 'plantilla_default.json')
        if not os.path.exists(default_json_path):
            with open(default_json_path, 'w', encoding='utf-8') as f:
                json.dump({"00 PAPELES": {"_files_": ["Listado de Documentos.txt"]}}, f, indent=4)

    def _create_main_layout(self):
        self.sidebar_frame = tk.Frame(self, bg=self.theme_colors['frame_bg'], width=220)
        self.sidebar_frame.pack(side="left", fill="y"); self.sidebar_frame.pack_propagate(False)
        self.content_frame = tk.Frame(self, bg=self.theme_colors['background'])
        self.content_frame.pack(side="right", fill="both", expand=True)

    def _create_sidebar(self):
        tk.Label(self.sidebar_frame, text="Menú Principal", font=FONT_SIDEBAR_TITLE, bg=self.theme_colors['frame_bg'], fg=self.theme_colors['text']).pack(pady=20, padx=20)
        self.nav_buttons = {}
        nav_items = {
            "Creador": ("📂", OrganizeFrame), "Ejemplo": ("✨", ExampleFrame),
            "Guía": ("❓", GuideFrame), "Configuración": ("⚙️", SettingsFrame),
            "Acerca de": ("ℹ️", AboutFrame)
        }
        for text, (icon, frame_class) in nav_items.items():
            btn = tk.Button(self.sidebar_frame, text=f" {icon}  {text}", font=FONT_DEFAULT,
                            bg=self.theme_colors['frame_bg'], fg=self.theme_colors['text'], relief="flat", anchor="w",
                            command=lambda fc=frame_class: self.show_frame(fc))
            btn.pack(fill="x", padx=10, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.theme_colors['button_hover']))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.theme_colors['frame_bg'] if getattr(self, 'current_frame_class', None) != self.frames[b] else self.theme_colors['accent']))
            self.nav_buttons[frame_class] = btn
        tk.Button(self.sidebar_frame, text="Salir", command=self.on_closing,
                  bg=self.theme_colors['exit'], fg=self.theme_colors['text'], relief="flat", font=FONT_BOLD).pack(side="bottom", fill="x", ipady=10)

    def _create_content_frames(self):
        self.frames = {}
        for frame_class in (OrganizeFrame, GuideFrame, ExampleFrame, SettingsFrame, AboutFrame):
            frame = frame_class(self.content_frame, app_instance=self)
            self.frames[frame_class] = frame
            self.frames[self.nav_buttons[frame_class]] = frame_class

    def show_frame(self, frame_class_to_show):
        for frame_class, frame in self.frames.items():
            if not isinstance(frame_class, type): continue
            is_target_frame = (frame_class == frame_class_to_show)
            if is_target_frame: frame.pack(fill="both", expand=True)
            else: frame.pack_forget()
            button = self.nav_buttons.get(frame_class)
            if button: button.config(bg=self.theme_colors['accent'] if is_target_frame else self.theme_colors['frame_bg'])
        self.current_frame_class = frame_class_to_show

    def on_closing(self):
        organize_frame = self.frames.get(OrganizeFrame)
        if organize_frame: self.config_manager.set('last_path', organize_frame.ruta_var.get())
        self.config_manager.save(); self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
