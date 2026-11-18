"""
Vista de Gestión de Integrantes del Equipo (Miembros)
NEXORA TASKS - Tópicos Avanzados de Programación

Permite crear, consultar, modificar, activar/desactivar y eliminar miembros del equipo.
Asegura la validación de correos electrónicos únicos y el control de disponibilidad
para asignación de tickets.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from models.member import Member
from models.user import User
from services.member_service import MemberService
from ui.components.modals import MemberModal
from ui.theme import Theme


class MembersView(tk.Frame):
    """Módulo de administración del catálogo de Miembros."""

    def __init__(
        self,
        parent: tk.Widget,
        current_user: User,
        member_service: MemberService
    ):
        super().__init__(parent, bg=Theme.BG_MAIN)
        self.current_user = current_user
        self.member_service = member_service

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Construye la interfaz de miembros."""
        # Encabezado
        header = tk.Frame(self, bg=Theme.BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 14))

        lbl_title = tk.Label(
            header,
            text="Integrantes del Equipo",
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MAIN
        )
        lbl_title.pack(side="left")

        btn_new = tk.Button(
            header,
            text="+ Nuevo Integrante",
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

        # Barra de Filtros y Acciones
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

        lbl_filter_st = tk.Label(
            filter_bar,
            text="Disponibilidad:",
            font=Theme.FONT_BODY_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_filter_st.pack(side="left", padx=(0, 6))

        self.cmb_filter_active = ttk.Combobox(
            filter_bar,
            values=["(Todos)", "Solo Activos", "Solo Inactivos"],
            state="readonly",
            font=Theme.FONT_BODY,
            width=14
        )
        self.cmb_filter_active.set("(Todos)")
        self.cmb_filter_active.pack(side="left", padx=(0, 14))
        self.cmb_filter_active.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        btn_clear = tk.Button(
            filter_bar,
            text="Limpiar",
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

        # Botones de Acción
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

        self.btn_toggle_active = tk.Button(
            filter_bar,
            text="🔄 Activar / Desactivar",
            font=Theme.FONT_BODY,
            bg=Theme.WARNING,
            fg="#000000",
            activebackground="#d97706",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._toggle_active_selected
        )
        self.btn_toggle_active.pack(side="right", padx=(0, 8))

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

        # Tabla Treeview
        table_container = tk.Frame(self, bg=Theme.BG_CARD, padx=12, pady=12)
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        columns = ("id", "name", "email", "role", "dept", "phone", "status")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="NOMBRE COMPLETO")
        self.tree.heading("email", text="CORREO ELECTRÓNICO")
        self.tree.heading("role", text="CARGO / ROL")
        self.tree.heading("dept", text="DEPARTAMENTO")
        self.tree.heading("phone", text="TELÉFONO")
        self.tree.heading("status", text="ESTADO")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("email", width=230, anchor="w")
        self.tree.column("role", width=190, anchor="w")
        self.tree.column("dept", width=160, anchor="w")
        self.tree.column("phone", width=130, anchor="center")
        self.tree.column("status", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

    def _clear_filters(self) -> None:
        self.ent_search.delete(0, "end")
        self.cmb_filter_active.set("(Todos)")
        self.refresh()

    def refresh(self) -> None:
        """Carga y actualiza los miembros en la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        filter_choice = self.cmb_filter_active.get()
        active_only = (filter_choice == "Solo Activos")
        search_query = self.ent_search.get().strip().lower()

        members = self.member_service.get_all_members(active_only=active_only)

        for m in members:
            if filter_choice == "Solo Inactivos" and m.is_active:
                continue

            if search_query:
                in_name = search_query in m.full_name.lower()
                in_email = search_query in m.email.lower()
                in_role = search_query in m.role_title.lower()
                in_dept = search_query in m.department.lower()
                if not (in_name or in_email or in_role or in_dept):
                    continue

            status_str = "ACTIVO" if m.is_active else "INACTIVO"
            self.tree.insert(
                "",
                "end",
                iid=str(m.id),
                values=(
                    m.id,
                    m.full_name,
                    m.email,
                    m.role_title,
                    m.department,
                    m.phone or "—",
                    status_str
                )
            )

    def _get_selected_member(self) -> Optional[Member]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Seleccione un integrante de la lista.", parent=self)
            return None
        m_id = int(selected[0])
        return self.member_service.get_member_by_id(m_id)

    def _open_new_modal(self) -> None:
        MemberModal(
            self,
            member_service=self.member_service,
            member=None,
            on_success=self.refresh
        )

    def _edit_selected(self) -> None:
        member = self._get_selected_member()
        if member:
            MemberModal(
                self,
                member_service=self.member_service,
                member=member,
                on_success=self.refresh
            )

    def _toggle_active_selected(self) -> None:
        member = self._get_selected_member()
        if not member:
            return

        new_state = not member.is_active
        action_name = "desactivar" if member.is_active else "activar"
        confirm = messagebox.askyesno(
            "Confirmar Cambio de Estado",
            f"¿Desea {action_name} al integrante '{member.full_name}'?\n\n"
            f"{'Los miembros inactivos no pueden recibir nuevas asignaciones de tickets.' if new_state is False else 'El miembro volverá a estar disponible para recibir asignaciones.'}",
            parent=self
        )
        if confirm:
            try:
                self.member_service.set_active_status(member.id, new_state)
                messagebox.showinfo("Estado Actualizado", f"El integrante ahora está {'Activo' if new_state else 'Inactivo'}.", parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)

    def _delete_selected(self) -> None:
        member = self._get_selected_member()
        if not member:
            return

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar a '{member.full_name}'?\n\n"
            "Nota: Sus tickets asignados no se perderán; quedarán desasignados (Sin asignar).",
            parent=self
        )
        if confirm:
            try:
                self.member_service.delete_member(member.id)
                messagebox.showinfo("Miembro Eliminado", f"'{member.full_name}' fue eliminado exitosamente.", parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error al eliminar", str(e), parent=self)
