"""
Vista de Panel Principal (Dashboard)
NEXORA TASKS - Tópicos Avanzados de Programación

Muestra indicadores clave de rendimiento (KPIs), desglose de tickets por estado
y la tabla de tareas recientes y prioritarias del sistema.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from models.user import User
from services.member_service import MemberService
from services.project_service import ProjectService
from services.ticket_service import TicketService
from ui.components.modals import TicketModal
from ui.theme import Theme


class DashboardView(tk.Frame):
    """Panel de control principal de la aplicación."""

    def __init__(
        self,
        parent: tk.Widget,
        current_user: User,
        project_service: ProjectService,
        member_service: MemberService,
        ticket_service: TicketService,
        on_navigate: Optional[Callable[[str], None]] = None
    ):
        super().__init__(parent, bg=Theme.BG_MAIN)
        self.current_user = current_user
        self.project_service = project_service
        self.member_service = member_service
        self.ticket_service = ticket_service
        self.on_navigate = on_navigate

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Construye los componentes visuales del Dashboard."""
        # Barra superior con título y bienvenida
        header_frame = tk.Frame(self, bg=Theme.BG_MAIN)
        header_frame.pack(fill="x", padx=24, pady=(20, 16))

        title_lbl = tk.Label(
            header_frame,
            text="Panel General de Control",
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MAIN
        )
        title_lbl.pack(side="left")

        subtitle_lbl = tk.Label(
            header_frame,
            text=f"Sesión activa: {self.current_user.full_name} ({self.current_user.role})",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_MAIN
        )
        subtitle_lbl.pack(side="left", padx=16, pady=(6, 0))

        btn_refresh = tk.Button(
            header_frame,
            text="🔄 Actualizar",
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.BORDER_COLOR,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.refresh
        )
        btn_refresh.pack(side="right")

        # Fila 1: Tarjetas KPI Totales
        cards_frame = tk.Frame(self, bg=Theme.BG_MAIN)
        cards_frame.pack(fill="x", padx=24, pady=(0, 16))

        # Tarjeta 1: Total Proyectos
        self.card_projects = self._create_kpi_card(
            cards_frame, "PROYECTOS", "0", "Activos en portafolio", Theme.PRIMARY_BLUE, 0
        )
        # Tarjeta 2: Total Miembros
        self.card_members = self._create_kpi_card(
            cards_frame, "INTEGRANTES", "0", "Equipo disponible", Theme.ACCENT_CYAN, 1
        )
        # Tarjeta 3: Total Tickets
        self.card_tickets = self._create_kpi_card(
            cards_frame, "TICKETS REGISTRADOS", "0", "Volumen global", Theme.ACCENT_PURPLE, 2
        )
        # Tarjeta 4: Vencidos / Alerta
        self.card_overdue = self._create_kpi_card(
            cards_frame, "TICKETS VENCIDOS", "0", "Requieren atención", Theme.DANGER, 3
        )

        # Fila 2: Indicadores de estado de tareas
        status_bar = tk.Frame(self, bg=Theme.BG_MAIN)
        status_bar.pack(fill="x", padx=24, pady=(0, 18))

        self.card_pending = self._create_status_pill(status_bar, "⏳ Pendientes", "0", Theme.WARNING, 0)
        self.card_progress = self._create_status_pill(status_bar, "⚡ En Progreso", "0", Theme.PRIMARY_LIGHT, 1)
        self.card_resolved = self._create_status_pill(status_bar, "✓ Resueltos", "0", Theme.SUCCESS, 2)

        # Sección: Tabla de Tickets Recientes
        table_container = tk.Frame(self, bg=Theme.BG_CARD, padx=16, pady=16)
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        tbl_header = tk.Frame(table_container, bg=Theme.BG_CARD)
        tbl_header.pack(fill="x", pady=(0, 10))

        lbl_tbl_title = tk.Label(
            tbl_header,
            text="Tickets Recientes y Prioritarios",
            font=Theme.FONT_TITLE_SECTION,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        lbl_tbl_title.pack(side="left")

        lbl_tbl_hint = tk.Label(
            tbl_header,
            text="Doble clic en un ticket para ver o editar detalles",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        lbl_tbl_hint.pack(side="right")

        # Treeview
        columns = ("code", "title", "project", "member", "priority", "status", "due_date")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", height=8)

        self.tree.heading("code", text="CÓDIGO")
        self.tree.heading("title", text="TÍTULO DE LA TAREA")
        self.tree.heading("project", text="PROYECTO")
        self.tree.heading("member", text="RESPONSABLE")
        self.tree.heading("priority", text="PRIORIDAD")
        self.tree.heading("status", text="ESTADO")
        self.tree.heading("due_date", text="LÍMITE")

        self.tree.column("code", width=95, anchor="center")
        self.tree.column("title", width=280, anchor="w")
        self.tree.column("project", width=160, anchor="w")
        self.tree.column("member", width=160, anchor="w")
        self.tree.column("priority", width=90, anchor="center")
        self.tree.column("status", width=110, anchor="center")
        self.tree.column("due_date", width=100, anchor="center")

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Evento de doble clic
        self.tree.bind("<Double-1>", self._on_ticket_double_click)

    def _create_kpi_card(
        self,
        parent: tk.Frame,
        title: str,
        value: str,
        subtitle: str,
        accent_color: str,
        col: int
    ) -> dict[str, tk.Widget]:
        """Crea una tarjeta KPI estilizada en la cuadrícula."""
        card = tk.Frame(
            parent,
            bg=Theme.BG_CARD,
            padx=16,
            pady=14,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR
        )
        card.grid(row=0, column=col, sticky="nsew", padx=6)
        parent.columnconfigure(col, weight=1)

        # Franja lateral de acento
        accent_bar = tk.Frame(card, bg=accent_color, height=3)
        accent_bar.pack(fill="x", pady=(0, 8))

        lbl_title = tk.Label(
            card,
            text=title,
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_title.pack(anchor="w")

        lbl_val = tk.Label(
            card,
            text=value,
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        lbl_val.pack(anchor="w", pady=(2, 2))

        lbl_sub = tk.Label(
            card,
            text=subtitle,
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        lbl_sub.pack(anchor="w")

        return {"card": card, "val": lbl_val, "sub": lbl_sub}

    def _create_status_pill(
        self,
        parent: tk.Frame,
        label: str,
        value: str,
        color: str,
        col: int
    ) -> dict[str, tk.Widget]:
        """Crea una píldora indicadora de estado en la segunda fila."""
        pill = tk.Frame(
            parent,
            bg=Theme.BG_CARD,
            padx=16,
            pady=10,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR
        )
        pill.grid(row=0, column=col, sticky="nsew", padx=6)
        parent.columnconfigure(col, weight=1)

        lbl_text = tk.Label(
            pill,
            text=label,
            font=Theme.FONT_BODY_BOLD,
            fg=color,
            bg=Theme.BG_CARD
        )
        lbl_text.pack(side="left")

        lbl_val = tk.Label(
            pill,
            text=value,
            font=Theme.FONT_TITLE_SECTION,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD
        )
        lbl_val.pack(side="right")

        return {"pill": pill, "val": lbl_val}

    def refresh(self) -> None:
        """Consulta los servicios y refresca las métricas y la tabla."""
        projects = self.project_service.get_all_projects()
        members = self.member_service.get_all_members()
        metrics = self.ticket_service.get_metrics_summary()

        # Actualizar Tarjetas Fila 1
        self.card_projects["val"].config(text=str(len(projects)))
        self.card_members["val"].config(text=str(len(members)))
        self.card_tickets["val"].config(text=str(metrics["total_tickets"]))
        self.card_overdue["val"].config(text=str(metrics["overdue_count"]))

        # Color de alerta para vencidos
        if metrics["overdue_count"] > 0:
            self.card_overdue["val"].config(fg=Theme.DANGER)
        else:
            self.card_overdue["val"].config(fg=Theme.SUCCESS)

        # Actualizar Píldoras Fila 2
        self.card_pending["val"].config(text=str(metrics["pending_count"]))
        self.card_progress["val"].config(text=str(metrics["in_progress_count"]))
        self.card_resolved["val"].config(text=str(metrics["resolved_count"]))

        # Limpiar y poblar tabla de tickets recientes
        for row in self.tree.get_children():
            self.tree.delete(row)

        all_tickets = self.ticket_service.get_all_tickets()
        # Mostrar los 15 más recientes
        for t in all_tickets[:15]:
            p_name = f"[{t.project_code}] {t.project_name}" if t.project_code else "N/A"
            m_name = t.member_name or "(Sin asignar)"
            self.tree.insert(
                "",
                "end",
                iid=str(t.id),
                values=(
                    t.ticket_code,
                    t.title,
                    p_name,
                    m_name,
                    t.priority,
                    t.status,
                    t.due_date
                )
            )

    def _on_ticket_double_click(self, event: tk.Event) -> None:
        """Abre el modal de edición de ticket al hacer doble clic."""
        selected = self.tree.selection()
        if not selected:
            return
        ticket_id = int(selected[0])
        ticket = self.ticket_service.get_ticket_by_id(ticket_id)
        if ticket:
            TicketModal(
                self,
                ticket_service=self.ticket_service,
                project_service=self.project_service,
                member_service=self.member_service,
                ticket=ticket,
                on_success=self.refresh
            )
