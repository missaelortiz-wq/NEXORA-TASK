"""
Ventana Principal de la Aplicación (MainWindow)
NEXORA TASKS - Tópicos Avanzados de Programación

Gestiona la navegación modular mediante menú lateral (Sidebar),
el área de contenido dinámico y el control de sesiones y permisos por rol.
"""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models.user import User
from services.auth_service import AuthService
from services.member_service import MemberService
from services.project_service import ProjectService
from services.ticket_service import TicketService
from ui.theme import Theme, setup_ttk_styles
from ui.views.dashboard_view import DashboardView
from ui.views.members_view import MembersView
from ui.views.projects_view import ProjectsView
from ui.views.reports_view import ReportsView
from ui.views.tickets_view import TicketsView
from ui.views.users_view import UsersView


class MainWindow(tk.Tk):
    """Ventana principal del sistema NEXORA TASKS."""

    def __init__(
        self,
        current_user: User,
        auth_service: AuthService,
        project_service: ProjectService,
        member_service: MemberService,
        ticket_service: TicketService,
        on_logout: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.current_user = current_user
        self.auth_service = auth_service
        self.project_service = project_service
        self.member_service = member_service
        self.ticket_service = ticket_service
        self.on_logout = on_logout

        self.title(f"NEXORA TASKS - {self.current_user.full_name} [{self.current_user.role}]")
        self.configure(bg=Theme.BG_MAIN)
        self.minsize(1050, 680)

        # Dimensiones y centrado
        width = 1180
        height = 760
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{max(0, pos_x)}+{max(0, pos_y)}")

        setup_ttk_styles(self)

        # Diccionario para almacenar instancias de vistas y botones de navegación
        self.views = {}
        self.nav_buttons = {}
        self.current_view_key = ""

        self._build_layout()
        self.navigate_to("dashboard")

        # Asegurar elevación inicial al frente en Windows sin bloquear modales
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.focus_force()

    def _build_layout(self) -> None:
        """Construye la estructura general: Barra Lateral (Sidebar) + Contenedor de Vistas."""
        # 1. BARRA LATERAL (SIDEBAR)
        self.sidebar = tk.Frame(self, bg=Theme.BG_SIDEBAR, width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand / Logotipo
        brand_frame = tk.Frame(self.sidebar, bg=Theme.BG_SIDEBAR, padx=18, pady=20)
        brand_frame.pack(fill="x")

        lbl_brand = tk.Label(
            brand_frame,
            text="⚡ NEXORA TASKS",
            font=("Segoe UI", 16, "bold"),
            fg=Theme.PRIMARY_LIGHT,
            bg=Theme.BG_SIDEBAR
        )
        lbl_brand.pack(anchor="w")

        lbl_subbrand = tk.Label(
            brand_frame,
            text="Gestor de Proyectos & Tickets",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_SIDEBAR
        )
        lbl_subbrand.pack(anchor="w", pady=(2, 0))

        # Divisor
        div = tk.Frame(self.sidebar, bg=Theme.BORDER_COLOR, height=1)
        div.pack(fill="x", padx=16, pady=(0, 16))

        # Menú de Botones de Navegación
        self.menu_frame = tk.Frame(self.sidebar, bg=Theme.BG_SIDEBAR)
        self.menu_frame.pack(fill="both", expand=True, padx=10)

        # Definición de módulos de navegación
        modules = [
            ("dashboard", "📊  Panel General", "dashboard"),
            ("projects", "📁  Proyectos", "projects"),
            ("members", "👥  Integrantes", "members"),
            ("tickets", "🎫  Tickets y Tareas", "tickets"),
            ("reports", "📈  Reportes y Métricas", "reports")
        ]

        # REQUISITO 7: El Administrador puede gestionar cuentas. El Operador NO.
        if self.current_user.is_admin():
            modules.append(("users", "🔐  Cuentas de Acceso", "users"))

        for key, text, tag in modules:
            btn = self._create_nav_button(self.menu_frame, text, key)
            self.nav_buttons[key] = btn

        # Tarjeta Inferior de Usuario en la Barra Lateral
        user_card = tk.Frame(
            self.sidebar,
            bg=Theme.BG_CARD,
            padx=14,
            pady=12,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR
        )
        user_card.pack(fill="x", side="bottom", padx=12, pady=16)

        lbl_u_name = tk.Label(
            user_card,
            text=self.current_user.full_name,
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        lbl_u_name.pack(fill="x")

        # Insignia de Rol
        role_color = Theme.PRIMARY_LIGHT if self.current_user.is_admin() else Theme.ACCENT_CYAN
        lbl_u_role = tk.Label(
            user_card,
            text=f"Rol: {self.current_user.role}",
            font=Theme.FONT_SMALL,
            fg=role_color,
            bg=Theme.BG_CARD,
            anchor="w"
        )
        lbl_u_role.pack(fill="x", pady=(2, 8))

        btn_logout = tk.Button(
            user_card,
            text="🚪 Cerrar Sesión",
            font=Theme.FONT_SMALL_BOLD,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_SECONDARY,
            activebackground=Theme.DANGER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=4,
            command=self._handle_logout
        )
        btn_logout.pack(fill="x")

        # 2. CONTENEDOR CENTRAL DE VISTAS (MAIN AREA)
        self.content_area = tk.Frame(self, bg=Theme.BG_MAIN)
        self.content_area.pack(side="right", fill="both", expand=True)

    def _create_nav_button(self, parent: tk.Frame, text: str, key: str) -> tk.Button:
        """Crea un botón estilizado para el menú lateral."""
        btn = tk.Button(
            parent,
            text=text,
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_SIDEBAR,
            activebackground=Theme.BG_CARD,
            activeforeground="#ffffff",
            relief="flat",
            anchor="w",
            padx=14,
            pady=9,
            cursor="hand2",
            command=lambda: self.navigate_to(key)
        )
        btn.pack(fill="x", pady=2)
        return btn

    def navigate_to(self, view_key: str) -> None:
        """Cambia dinámicamente la vista activa en el contenedor central."""
        if self.current_view_key == view_key and view_key in self.views:
            # Si ya está activa, simplemente refrescar
            self.views[view_key].refresh()
            return

        # Resaltar botón activo en la barra lateral
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.config(
                    bg=Theme.PRIMARY_BLUE,
                    fg="#ffffff",
                    font=Theme.FONT_BODY_BOLD
                )
            else:
                btn.config(
                    bg=Theme.BG_SIDEBAR,
                    fg=Theme.TEXT_SECONDARY,
                    font=Theme.FONT_BODY
                )

        # Ocultar vista actual si existe
        if self.current_view_key and self.current_view_key in self.views:
            self.views[self.current_view_key].pack_forget()

        # Instanciar vista si aún no fue creada
        if view_key not in self.views:
            if view_key == "dashboard":
                view = DashboardView(
                    self.content_area,
                    current_user=self.current_user,
                    project_service=self.project_service,
                    member_service=self.member_service,
                    ticket_service=self.ticket_service,
                    on_navigate=self.navigate_to
                )
            elif view_key == "projects":
                view = ProjectsView(
                    self.content_area,
                    current_user=self.current_user,
                    project_service=self.project_service
                )
            elif view_key == "members":
                view = MembersView(
                    self.content_area,
                    current_user=self.current_user,
                    member_service=self.member_service
                )
            elif view_key == "tickets":
                view = TicketsView(
                    self.content_area,
                    current_user=self.current_user,
                    ticket_service=self.ticket_service,
                    project_service=self.project_service,
                    member_service=self.member_service
                )
            elif view_key == "reports":
                view = ReportsView(
                    self.content_area,
                    current_user=self.current_user,
                    ticket_service=self.ticket_service
                )
            elif view_key == "users":
                view = UsersView(
                    self.content_area,
                    current_user=self.current_user,
                    auth_service=self.auth_service
                )
            else:
                return

            self.views[view_key] = view

        # Mostrar la vista seleccionada y refrescar datos
        self.views[view_key].pack(fill="both", expand=True)
        self.views[view_key].refresh()
        self.current_view_key = view_key

    def _handle_logout(self) -> None:
        """Cierra la sesión actual y solicita confirmación."""
        confirm = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Desea cerrar la sesión actual de NEXORA TASKS?",
            parent=self
        )
        if confirm:
            self.destroy()
            if self.on_logout:
                self.on_logout()
