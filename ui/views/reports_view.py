"""
Vista de Reportes y Auditoría de Tickets
NEXORA TASKS - Tópicos Avanzados de Programación

Muestra estadísticas por estado, desglose por prioridad y la lista
de tickets vencidos pendientes de resolución con filtros cruzados.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from models.ticket import Ticket
from models.user import User
from services.ticket_service import TicketService
from ui.theme import Theme


class ReportsView(tk.Frame):
    """Módulo de analítica, estadísticas y auditoría de tickets vencidos."""

    def __init__(
        self,
        parent: tk.Widget,
        current_user: User,
        ticket_service: TicketService
    ):
        super().__init__(parent, bg=Theme.BG_MAIN)
        self.current_user = current_user
        self.ticket_service = ticket_service

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Construye la interfaz de reportes."""
        header = tk.Frame(self, bg=Theme.BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 14))

        lbl_title = tk.Label(
            header,
            text="Reportes y Métricas Operativas",
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MAIN
        )
        lbl_title.pack(side="left")

        btn_refresh = tk.Button(
            header,
            text="🔄 Actualizar Reportes",
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.BORDER_COLOR,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=5,
            command=self.refresh
        )
        btn_refresh.pack(side="right")

        # Fila Superior: Tarjetas de Resumen por Estado
        stats_frame = tk.Frame(self, bg=Theme.BG_MAIN)
        stats_frame.pack(fill="x", padx=24, pady=(0, 16))

        self.pill_total = self._create_stat_card(stats_frame, "Total Registrados", "0", Theme.PRIMARY_BLUE, 0)
        self.pill_pending = self._create_stat_card(stats_frame, "Pendientes", "0", Theme.WARNING, 1)
        self.pill_progress = self._create_stat_card(stats_frame, "En Progreso", "0", Theme.PRIMARY_LIGHT, 2)
        self.pill_review = self._create_stat_card(stats_frame, "En Revisión", "0", Theme.ACCENT_CYAN, 3)
        self.pill_resolved = self._create_stat_card(stats_frame, "Resueltos", "0", Theme.SUCCESS, 4)
        self.pill_overdue = self._create_stat_card(stats_frame, "Vencidos Activos", "0", Theme.DANGER, 5)

        # Sección: Tickets Vencidos con Filtros
        overdue_container = tk.Frame(self, bg=Theme.BG_CARD, padx=16, pady=16)
        overdue_container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        sec_header = tk.Frame(overdue_container, bg=Theme.BG_CARD)
        sec_header.pack(fill="x", pady=(0, 10))

        lbl_sec_title = tk.Label(
            sec_header,
            text="⚠️ Tickets Vencidos No Resueltos ni Cancelados",
            font=Theme.FONT_TITLE_SECTION,
            fg=Theme.DANGER,
            bg=Theme.BG_CARD
        )
        lbl_sec_title.pack(side="left")

        # Filtros cruzados para el reporte
        filter_box = tk.Frame(sec_header, bg=Theme.BG_CARD)
        filter_box.pack(side="right")

        lbl_fprio = tk.Label(filter_box, text="Prioridad:", font=Theme.FONT_SMALL_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_fprio.pack(side="left", padx=(0, 6))

        self.cmb_prio = ttk.Combobox(
            filter_box,
            values=["(Todas)"] + list(Ticket.VALID_PRIORITIES),
            state="readonly",
            font=Theme.FONT_SMALL,
            width=12
        )
        self.cmb_prio.set("(Todas)")
        self.cmb_prio.pack(side="left", padx=(0, 12))
        self.cmb_prio.bind("<<ComboboxSelected>>", lambda e: self._refresh_overdue_table())

        lbl_fst = tk.Label(filter_box, text="Estado:", font=Theme.FONT_SMALL_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_fst.pack(side="left", padx=(0, 6))

        self.cmb_status = ttk.Combobox(
            filter_box,
            values=["(Todos Activos)", "Pendiente", "En Progreso", "En Revisión"],
            state="readonly",
            font=Theme.FONT_SMALL,
            width=14
        )
        self.cmb_status.set("(Todos Activos)")
        self.cmb_status.pack(side="left", padx=(0, 10))
        self.cmb_status.bind("<<ComboboxSelected>>", lambda e: self._refresh_overdue_table())

        # Tabla de Vencidos
        columns = ("code", "title", "project", "member", "priority", "due_date", "status")
        self.tree = ttk.Treeview(overdue_container, columns=columns, show="headings", height=8)

        self.tree.heading("code", text="CÓDIGO")
        self.tree.heading("title", text="TÍTULO DE LA TAREA")
        self.tree.heading("project", text="PROYECTO")
        self.tree.heading("member", text="RESPONSABLE")
        self.tree.heading("priority", text="PRIORIDAD")
        self.tree.heading("due_date", text="VENCIMIENTO")
        self.tree.heading("status", text="ESTADO")

        self.tree.column("code", width=100, anchor="center")
        self.tree.column("title", width=280, anchor="w")
        self.tree.column("project", width=170, anchor="w")
        self.tree.column("member", width=170, anchor="w")
        self.tree.column("priority", width=95, anchor="center")
        self.tree.column("due_date", width=110, anchor="center")
        self.tree.column("status", width=115, anchor="center")

        scrollbar = ttk.Scrollbar(overdue_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_stat_card(
        self,
        parent: tk.Frame,
        label: str,
        value: str,
        color: str,
        col: int
    ) -> dict[str, tk.Widget]:
        """Crea una tarjeta de conteo por estado."""
        card = tk.Frame(
            parent,
            bg=Theme.BG_CARD,
            padx=12,
            pady=10,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR
        )
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        parent.columnconfigure(col, weight=1)

        accent = tk.Frame(card, bg=color, height=3)
        accent.pack(fill="x", pady=(0, 4))

        lbl_l = tk.Label(card, text=label, font=Theme.FONT_SMALL, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_CARD)
        lbl_l.pack(anchor="w")

        lbl_v = tk.Label(card, text=value, font=Theme.FONT_TITLE_SECTION, fg=Theme.TEXT_PRIMARY, bg=Theme.BG_CARD)
        lbl_v.pack(anchor="w")

        return {"card": card, "val": lbl_v}

    def refresh(self) -> None:
        """Actualiza todas las métricas y la tabla de tickets vencidos."""
        metrics = self.ticket_service.get_metrics_summary()
        by_status = metrics["by_status"]

        self.pill_total["val"].config(text=str(metrics["total_tickets"]))
        self.pill_pending["val"].config(text=str(by_status.get("Pendiente", 0)))
        self.pill_progress["val"].config(text=str(by_status.get("En Progreso", 0)))
        self.pill_review["val"].config(text=str(by_status.get("En Revisión", 0)))
        self.pill_resolved["val"].config(text=str(by_status.get("Resuelto", 0)))
        self.pill_overdue["val"].config(text=str(metrics["overdue_count"]))

        self._refresh_overdue_table()

    def _refresh_overdue_table(self) -> None:
        """Filtra y recarga la tabla de tickets vencidos."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        prio_choice = self.cmb_prio.get()
        prio_param = None if prio_choice == "(Todas)" else prio_choice

        st_choice = self.cmb_status.get()
        st_param = None if st_choice == "(Todos Activos)" else st_choice

        overdue_tickets = self.ticket_service.get_overdue_tickets(priority=prio_param, status=st_param)

        for t in overdue_tickets:
            p_display = f"[{t.project_code}] {t.project_name}" if t.project_code else "N/A"
            m_display = t.member_name or "(Sin asignar)"

            self.tree.insert(
                "",
                "end",
                iid=str(t.id),
                values=(
                    t.ticket_code,
                    t.title,
                    p_display,
                    m_display,
                    t.priority,
                    t.due_date,
                    t.status
                )
            )
