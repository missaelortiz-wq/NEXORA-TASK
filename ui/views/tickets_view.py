"""
Vista de Gestión de Tickets y Tareas
NEXORA TASKS - Tópicos Avanzados de Programación

Permite crear, consultar, modificar, reasignar y eliminar tickets de trabajo.
Incorpora filtrado por proyecto, miembro responsable, prioridad y estado,
mostrando las relaciones foráneas obtenidas mediante SQL JOIN.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from models.ticket import Ticket
from models.user import User
from services.member_service import MemberService
from services.project_service import ProjectService
from services.ticket_service import TicketService
from ui.components.modals import TicketModal
from ui.theme import Theme


class TicketsView(tk.Frame):
    """Módulo de administración del ciclo de vida de Tickets."""

    def __init__(
        self,
        parent: tk.Widget,
        current_user: User,
        ticket_service: TicketService,
        project_service: ProjectService,
        member_service: MemberService
    ):
        super().__init__(parent, bg=Theme.BG_MAIN)
        self.current_user = current_user
        self.ticket_service = ticket_service
        self.project_service = project_service
        self.member_service = member_service

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Construye la interfaz de tickets."""
        # Encabezado
        header = tk.Frame(self, bg=Theme.BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 14))

        lbl_title = tk.Label(
            header,
            text="Gestión de Tickets y Tareas",
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MAIN
        )
        lbl_title.pack(side="left")

        btn_new = tk.Button(
            header,
            text="+ Nuevo Ticket",
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

        # Barra Superior de Filtros
        filter_bar_1 = tk.Frame(self, bg=Theme.BG_CARD, padx=14, pady=8)
        filter_bar_1.pack(fill="x", padx=24, pady=(0, 4))

        lbl_search = tk.Label(filter_bar_1, text="Buscar:", font=Theme.FONT_BODY_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_search.pack(side="left", padx=(0, 6))

        self.ent_search = tk.Entry(
            filter_bar_1,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            width=22
        )
        self.ent_search.pack(side="left", padx=(0, 16), ipady=3)
        self.ent_search.bind("<KeyRelease>", lambda e: self.refresh())

        lbl_proj = tk.Label(filter_bar_1, text="Proyecto:", font=Theme.FONT_BODY_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_proj.pack(side="left", padx=(0, 6))

        self.cmb_filter_proj = ttk.Combobox(filter_bar_1, state="readonly", font=Theme.FONT_BODY, width=20)
        self.cmb_filter_proj.pack(side="left", padx=(0, 16))
        self.cmb_filter_proj.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        lbl_prio = tk.Label(filter_bar_1, text="Prioridad:", font=Theme.FONT_BODY_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_prio.pack(side="left", padx=(0, 6))

        self.cmb_filter_prio = ttk.Combobox(
            filter_bar_1,
            values=["(Todas)"] + list(Ticket.VALID_PRIORITIES),
            state="readonly",
            font=Theme.FONT_BODY,
            width=12
        )
        self.cmb_filter_prio.set("(Todas)")
        self.cmb_filter_prio.pack(side="left", padx=(0, 16))
        self.cmb_filter_prio.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        lbl_status = tk.Label(filter_bar_1, text="Estado:", font=Theme.FONT_BODY_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_status.pack(side="left", padx=(0, 6))

        self.cmb_filter_status = ttk.Combobox(
            filter_bar_1,
            values=["(Todos)"] + list(Ticket.VALID_STATUSES),
            state="readonly",
            font=Theme.FONT_BODY,
            width=14
        )
        self.cmb_filter_status.set("(Todos)")
        self.cmb_filter_status.pack(side="left", padx=(0, 14))
        self.cmb_filter_status.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Botones de Acción de Filtros
        btn_clear = tk.Button(
            filter_bar_1,
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

        # Barra de Operaciones Rápidas
        actions_bar = tk.Frame(self, bg=Theme.BG_CARD, padx=14, pady=6)
        actions_bar.pack(fill="x", padx=24, pady=(0, 14))

        self.lbl_count_info = tk.Label(
            actions_bar,
            text="Cargando tickets...",
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_CARD
        )
        self.lbl_count_info.pack(side="left", pady=3)

        btn_delete = tk.Button(
            actions_bar,
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

        btn_quick_status = tk.Button(
            actions_bar,
            text="⚡ Cambiar Estado Rápido",
            font=Theme.FONT_BODY,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._quick_change_status
        )
        btn_quick_status.pack(side="right", padx=(0, 8))

        btn_edit = tk.Button(
            actions_bar,
            text="✏ Editar Ticket",
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

        columns = ("id", "code", "title", "project", "member", "priority", "due_date", "status")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="CÓDIGO")
        self.tree.heading("title", text="TÍTULO DE LA TAREA")
        self.tree.heading("project", text="PROYECTO")
        self.tree.heading("member", text="RESPONSABLE")
        self.tree.heading("priority", text="PRIORIDAD")
        self.tree.heading("due_date", text="FECHA LÍMITE")
        self.tree.heading("status", text="ESTADO")

        self.tree.column("id", width=45, anchor="center")
        self.tree.column("code", width=100, anchor="center")
        self.tree.column("title", width=280, anchor="w")
        self.tree.column("project", width=170, anchor="w")
        self.tree.column("member", width=170, anchor="w")
        self.tree.column("priority", width=95, anchor="center")
        self.tree.column("due_date", width=105, anchor="center")
        self.tree.column("status", width=115, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

    def _populate_filter_combos(self) -> None:
        """Carga la lista de proyectos en el selector de filtros."""
        projects = self.project_service.get_all_projects()
        self.proj_filter_map = {"(Todos)": None}
        for p in projects:
            self.proj_filter_map[f"[{p.code}] {p.name}"] = p.id
        self.cmb_filter_proj["values"] = list(self.proj_filter_map.keys())
        if not self.cmb_filter_proj.get():
            self.cmb_filter_proj.set("(Todos)")

    def _clear_filters(self) -> None:
        self.ent_search.delete(0, "end")
        self.cmb_filter_proj.set("(Todos)")
        self.cmb_filter_prio.set("(Todas)")
        self.cmb_filter_status.set("(Todos)")
        self.refresh()

    def refresh(self) -> None:
        """Actualiza y filtra los tickets en la tabla."""
        self._populate_filter_combos()

        for item in self.tree.get_children():
            self.tree.delete(item)

        proj_choice = self.cmb_filter_proj.get()
        project_id = self.proj_filter_map.get(proj_choice)

        prio_choice = self.cmb_filter_prio.get()
        priority_param = None if prio_choice == "(Todas)" else prio_choice

        status_choice = self.cmb_filter_status.get()
        status_param = None if status_choice == "(Todos)" else status_choice

        search_query = self.ent_search.get().strip().lower()

        tickets = self.ticket_service.get_all_tickets(
            status=status_param,
            project_id=project_id,
            priority=priority_param
        )

        visible_count = 0
        for t in tickets:
            if search_query:
                in_code = search_query in t.ticket_code.lower()
                in_title = search_query in t.title.lower()
                in_proj = search_query in (t.project_name or "").lower() or search_query in (t.project_code or "").lower()
                in_resp = search_query in (t.member_name or "").lower()
                if not (in_code or in_title or in_proj or in_resp):
                    continue

            visible_count += 1
            p_display = f"[{t.project_code}] {t.project_name}" if t.project_code else "N/A"
            m_display = t.member_name or "(Sin asignar)"

            self.tree.insert(
                "",
                "end",
                iid=str(t.id),
                values=(
                    t.id,
                    t.ticket_code,
                    t.title,
                    p_display,
                    m_display,
                    t.priority,
                    t.due_date,
                    t.status
                )
            )

        self.lbl_count_info.config(text=f"Mostrando {visible_count} ticket(s) filtrados")

    def _get_selected_ticket(self) -> Optional[Ticket]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Seleccione un ticket de la tabla.", parent=self)
            return None
        t_id = int(selected[0])
        return self.ticket_service.get_ticket_by_id(t_id)

    def _open_new_modal(self) -> None:
        TicketModal(
            self,
            ticket_service=self.ticket_service,
            project_service=self.project_service,
            member_service=self.member_service,
            ticket=None,
            on_success=self.refresh
        )

    def _edit_selected(self) -> None:
        ticket = self._get_selected_ticket()
        if ticket:
            TicketModal(
                self,
                ticket_service=self.ticket_service,
                project_service=self.project_service,
                member_service=self.member_service,
                ticket=ticket,
                on_success=self.refresh
            )

    def _quick_change_status(self) -> None:
        """Abre un diálogo rápido para actualizar el estado del ticket seleccionado."""
        ticket = self._get_selected_ticket()
        if not ticket:
            return

        modal = tk.Toplevel(self)
        modal.title(f"Estado de {ticket.ticket_code}")
        modal.configure(bg=Theme.BG_MODAL)
        modal.geometry("380x220")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()

        lbl_info = tk.Label(
            modal,
            text=f"Modificar estado de:\n[{ticket.ticket_code}] {ticket.title}",
            font=Theme.FONT_BODY_BOLD,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MODAL,
            justify="left"
        )
        lbl_info.pack(padx=20, pady=(16, 10), anchor="w")

        lbl_st = tk.Label(modal, text="Nuevo Estado:", font=Theme.FONT_SMALL_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MODAL)
        lbl_st.pack(padx=20, anchor="w")

        cmb = ttk.Combobox(modal, values=list(Ticket.VALID_STATUSES), state="readonly", font=Theme.FONT_BODY)
        cmb.set(ticket.status)
        cmb.pack(padx=20, pady=(4, 16), fill="x")

        def _apply():
            new_st = cmb.get()
            try:
                self.ticket_service.change_ticket_status(ticket.id, new_st)
                messagebox.showinfo("Éxito", f"Estado de {ticket.ticket_code} actualizado a '{new_st}'.", parent=modal)
                modal.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=modal)

        btn_save = tk.Button(
            modal,
            text="Guardar Estado",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=_apply
        )
        btn_save.pack(side="right", padx=20, pady=10)

        btn_cancel = tk.Button(
            modal,
            text="Cancelar",
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_SECONDARY,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=modal.destroy
        )
        btn_cancel.pack(side="right", pady=10)

    def _delete_selected(self) -> None:
        ticket = self._get_selected_ticket()
        if not ticket:
            return

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar permanentemente el ticket '{ticket.ticket_code}'?\n\n"
            f"Título: {ticket.title}",
            parent=self
        )
        if confirm:
            try:
                self.ticket_service.delete_ticket(ticket.id)
                messagebox.showinfo("Ticket Eliminado", f"El ticket {ticket.ticket_code} fue eliminado.", parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error al eliminar", str(e), parent=self)
