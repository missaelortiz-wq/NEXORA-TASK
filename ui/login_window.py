"""
Ventana de Autenticación (Login)
NEXORA TASKS - Tópicos Avanzados de Programación

Proporciona la interfaz de inicio de sesión con diseño moderno oscuro y acentos azules.
Valida las credenciales mediante AuthService sin almacenar contraseñas en texto plano
y diferencia perfiles de Administrador y Operador.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models.user import User
from services.auth_service import AuthService
from ui.theme import Theme, setup_ttk_styles


class LoginWindow(tk.Tk):
    """Ventana principal de inicio de sesión de NEXORA TASKS."""

    def __init__(
        self,
        auth_service: AuthService,
        on_login_success: Callable[[User], None]
    ):
        super().__init__()
        self.auth_service = auth_service
        self.on_login_success = on_login_success

        self.title("NEXORA TASKS - Inicio de Sesión")
        self.configure(bg=Theme.BG_ROOT)
        self.resizable(False, False)

        setup_ttk_styles(self)

        width = 460
        height = 620
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{max(0, pos_x)}+{max(0, pos_y)}")

        self._build_ui()

        # Asegurar que la ventana aparezca al frente en Windows sin bloquear otros modales
        self.deiconify()
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)
        self.focus_force()

    def _build_ui(self) -> None:
        """Construye los widgets del formulario de login."""
        # Contenedor central
        main_card = tk.Frame(
            self,
            bg=Theme.BG_CARD,
            padx=32,
            pady=30,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR
        )
        main_card.pack(fill="both", expand=True, padx=24, pady=24)

        # Logotipo / Título
        lbl_brand = tk.Label(
            main_card,
            text="⚡ NEXORA TASKS",
            font=("Segoe UI", 20, "bold"),
            fg=Theme.PRIMARY_LIGHT,
            bg=Theme.BG_CARD
        )
        lbl_brand.pack(pady=(0, 2))

        lbl_course = tk.Label(
            main_card,
            text="Tópicos Avanzados de Programación",
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_CARD
        )
        lbl_course.pack(pady=(0, 4))

        lbl_desc = tk.Label(
            main_card,
            text="Gestión de Proyectos, Tickets y Miembros",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_desc.pack(pady=(0, 20))

        # Separador decorativo
        sep = tk.Frame(main_card, bg=Theme.PRIMARY_BLUE, height=2)
        sep.pack(fill="x", pady=(0, 20))

        # Campo: Usuario
        lbl_user = tk.Label(
            main_card,
            text="Nombre de Usuario:",
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_user.pack(anchor="w", pady=(0, 4))

        self.ent_user = tk.Entry(
            main_card,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            highlightcolor=Theme.PRIMARY_BLUE
        )
        self.ent_user.pack(fill="x", ipady=6, pady=(0, 16))
        self.ent_user.focus_set()

        # Campo: Contraseña
        lbl_pass = tk.Label(
            main_card,
            text="Contraseña de Acceso:",
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_pass.pack(anchor="w", pady=(0, 4))

        self.ent_pass = tk.Entry(
            main_card,
            show="•",
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            highlightcolor=Theme.PRIMARY_BLUE
        )
        self.ent_pass.pack(fill="x", ipady=6, pady=(0, 8))

        # Checkbox mostrar contraseña
        self.var_show_pass = tk.BooleanVar(value=False)
        chk_show = tk.Checkbutton(
            main_card,
            text="Mostrar contraseña",
            variable=self.var_show_pass,
            font=Theme.FONT_SMALL,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_SECONDARY,
            selectcolor=Theme.BG_INPUT,
            activebackground=Theme.BG_CARD,
            activeforeground=Theme.TEXT_PRIMARY,
            command=self._toggle_show_password
        )
        chk_show.pack(anchor="w", pady=(0, 16))

        # Botón Iniciar Sesión
        self.btn_login = tk.Button(
            main_card,
            text="Iniciar Sesión",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self._handle_login
        )
        self.btn_login.pack(fill="x", pady=(0, 20))

        # Enlace de tecla Enter
        self.bind("<Return>", lambda e: self._handle_login())

        # Tarjeta inferior con cuentas de prueba
        hint_box = tk.Frame(
            main_card,
            bg=Theme.BG_ROOT,
            padx=12,
            pady=10,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR
        )
        hint_box.pack(fill="x")

        lbl_hint_title = tk.Label(
            hint_box,
            text="Credenciales de Prueba (Clic para autocompletar):",
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_ROOT
        )
        lbl_hint_title.pack(anchor="w", pady=(0, 4))

        # Botón rápido para Admin
        btn_quick_admin = tk.Button(
            hint_box,
            text="👑 Administrador: admin / admin123",
            font=Theme.FONT_SMALL,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.PRIMARY_BLUE,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            anchor="w",
            padx=6,
            pady=2,
            command=lambda: self._prefill("admin", "admin123")
        )
        btn_quick_admin.pack(fill="x", pady=2)

        # Botón rápido para Operador
        btn_quick_oper = tk.Button(
            hint_box,
            text="👤 Operador: operador / operador123",
            font=Theme.FONT_SMALL,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.PRIMARY_BLUE,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            anchor="w",
            padx=6,
            pady=2,
            command=lambda: self._prefill("operador", "operador123")
        )
        btn_quick_oper.pack(fill="x", pady=2)

    def _toggle_show_password(self) -> None:
        """Alterna la visualización del texto de la contraseña."""
        if self.var_show_pass.get():
            self.ent_pass.config(show="")
        else:
            self.ent_pass.config(show="•")

    def _prefill(self, u: str, p: str) -> None:
        """Autocompleta el formulario con credenciales de prueba para agilizar la revisión."""
        self.ent_user.delete(0, "end")
        self.ent_user.insert(0, u)
        self.ent_pass.delete(0, "end")
        self.ent_pass.insert(0, p)

    def _handle_login(self) -> None:
        """Valida las credenciales contra AuthService."""
        username = self.ent_user.get().strip()
        password = self.ent_pass.get()

        if not username or not password:
            messagebox.showwarning(
                "Campos Incompletos",
                "Por favor ingrese tanto el usuario como la contraseña.",
                parent=self
            )
            return

        success, msg, user = self.auth_service.login(username, password)

        if not success or user is None:
            messagebox.showerror(
                "Error de Autenticación",
                msg,
                parent=self
            )
            return

        # Notificar y transferir control a MainWindow
        self.destroy()
        self.on_login_success(user)
