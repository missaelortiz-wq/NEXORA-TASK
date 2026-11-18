"""
Vista de Gestión de Proyectos
NEXORA TASKS - Tópicos Avanzados de Programación

Permite crear, consultar, editar y eliminar proyectos en una tabla Treeview.
Aplica la regla de negocio que prohíbe eliminar proyectos con tickets activos
y requiere confirmación previa para proyectos sin tickets activos.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from models.project import Project
from models.user import User
from services.project_service import ProjectService
from ui.components.modals import ProjectModal
from ui.theme import Theme


class ProjectsView(tk.Frame):
    """Módulo de administración del catálogo de Proyectos."""

    def __init__(
        self,
        parent: tk.Widget,
        current_user: User,
        project_service: ProjectService
    ):
        super().__init__(parent, bg=Theme.BG_MAIN)
        self.current_user = current_user
        self.project_service = project_service

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Construye la interfaz del módulo de proyectos."""
        # Encabezado
        header = tk.Frame(self, bg=Theme.BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 14))

        lbl_title = tk.Label(
            header,
            text="Gestión de Proyectos",
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MAIN
        )
        lbl_title.pack(side="left")

        # Botón Nuevo Proyecto
        btn_new = tk.Button(
            header,
            text="+ Nuevo Proyecto",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._open_new_modal
        )
        btn_new.pack(side="right")

        # Barra de Filtros y Búsqueda
        filter_bar = tk.Frame(self, bg=Theme.BG_CARD, padx=14, pady=10)
        filter_bar.pack(fill="x", padx=24, pady=(0, 14))

        lbl_search = tk.Label(
            filter_bar,
            text="Buscar:",
            font=Theme.FONT_BODY_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_search.pack(side="left", padx=(0, 6))

        self.ent_search = tk.Entry(
            filter_bar,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            width=26
        )
        self.ent_search.pack(side="left", padx=(0, 16), ipady=3)
        self.ent_search.bind("<KeyRelease>", lambda e: self.refresh())

        lbl_filter_status = tk.Label(
            filter_bar,
            text="Estado:",
            font=Theme.FONT_BODY_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_filter_status.pack(side="left", padx=(0, 6))

        self.cmb_filter_status = ttk.Combobox(
            filter_bar,
            values=["(Todos)"] + list(Project.VALID_STATUSES),
            state="readonly",
            font=Theme.FONT_BODY,
            width=16
        )
        self.cmb_filter_status.set("(Todos)")
        self.cmb_filter_status.pack(side="left", padx=(0, 14))
        self.cmb_filter_status.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        btn_clear = tk.Button(
            filter_bar,
            text="Limpiar Filtros",
            font=Theme.FONT_SMALL,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_SECONDARY,
            activebackground=Theme.BORDER_COLOR,
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._clear_filters
        )
        btn_clear.pack(side="left")

        # Acciones sobre elemento seleccionado
        btn_delete = tk.Button(
            filter_bar,
            text="🗑 Eliminar",
            font=Theme.FONT_BODY,
            bg=Theme.DANGER,
            fg="#ffffff",
            activebackground="#dc2626",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._delete_selected
        )
        btn_delete.pack(side="right")

        btn_edit = tk.Button(
            filter_bar,
            text="✏ Editar",
            font=Theme.FONT_BODY,
            bg=Theme.BORDER_COLOR,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.PRIMARY_BLUE,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._edit_selected
        )
        btn_edit.pack(side="right", padx=(0, 8))

        # Contenedor de Tabla Treeview
        table_container = tk.Frame(self, bg=Theme.BG_CARD, padx=12, pady=12)
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        columns = ("id", "code", "name", "start_date", "status", "description")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="CLAVE")
        self.tree.heading("name", text="NOMBRE DEL PROYECTO")
        self.tree.heading("start_date", text="FECHA INICIO")
        self.tree.heading("status", text="ESTADO")
        self.tree.heading("description", text="DESCRIPCIÓN")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("code", width=120, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("start_date", width=110, anchor="center")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("description", width=360, anchor="w")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

    def _clear_filters(self) -> None:
        self.ent_search.delete(0, "end")
        self.cmb_filter_status.set("(Todos)")
        self.refresh()

    def refresh(self) -> None:
        """Carga y filtra los proyectos en la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_st = self.cmb_filter_status.get()
        status_param = None if filter_st == "(Todos)" else filter_st

        search_query = self.ent_search.get().strip().lower()

        projects = self.project_service.get_all_projects(status=status_param)

        for p in projects:
            # Filtrar por búsqueda de texto
            if search_query:
                in_code = search_query in p.code.lower()
                in_name = search_query in p.name.lower()
                in_desc = search_query in (p.description or "").lower()
                if not (in_code or in_name or in_desc):
                    continue

            self.tree.insert(
                "",
                "end",
                iid=str(p.id),
                values=(
                    p.id,
                    p.code,
                    p.name,
                    p.start_date,
                    p.status,
                    p.description or ""
                )
            )

    def _get_selected_project(self) -> Optional[Project]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un proyecto de la lista.", parent=self)
            return None
        proj_id = int(selected[0])
        return self.project_service.get_project_by_id(proj_id)

    def _open_new_modal(self) -> None:
        ProjectModal(
            self,
            project_service=self.project_service,
            project=None,
            on_success=self.refresh
        )

    def _edit_selected(self) -> None:
        project = self._get_selected_project()
        if project:
            ProjectModal(
                self,
                project_service=self.project_service,
                project=project,
                on_success=self.refresh
            )

    def _delete_selected(self) -> None:
        """
        Ejecuta la regla de negocio para la eliminación de proyectos:
        1. Consulta si existen tickets activos (Pendiente / En Progreso / En Revisión).
        2. Si existen, muestra error claro y bloquea el borrado.
        3. Si no existen, exige confirmación con messagebox.askyesno.
        4. Si se confirma, llama a project_service.delete_project(id, confirmed=True).
        """
        project = self._get_selected_project()
        if not project:
            return

        # 1 & 2. Evaluar aptitud de borrado con la capa de servicios
        can_delete, reason, active_tickets = self.project_service.can_delete_project(project.id)
        if not can_delete:
            messagebox.showerror(
                "Eliminación Bloqueada",
                reason,
                parent=self
            )
            return

        # 3. Confirmación obligatoria desde la interfaz
        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el proyecto '{project.name}' ({project.code})?\n\n"
            f"El proyecto no tiene tickets activos. Esta acción eliminará el registro de forma definitiva.",
            parent=self
        )

        if not confirm:
            return

        try:
            # 4. Ejecución con confirmación explícita
            self.project_service.delete_project(project.id, confirmed=True)
            messagebox.showinfo(
                "Proyecto Eliminado",
                f"El proyecto '{project.name}' ha sido eliminado exitosamente.",
                parent=self
            )
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error al eliminar", str(e), parent=self)
