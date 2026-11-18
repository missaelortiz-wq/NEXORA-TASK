"""
Vista de Gestión de Cuentas de Acceso (Usuarios del Sistema)
NEXORA TASKS - Tópicos Avanzados de Programación

Módulo restringido exclusivamente para usuarios con rol de Administrador.
Permite listar cuentas, registrar nuevos operadores, cambiar estados y restablecer contraseñas.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from models.user import User
from services.auth_service import AuthService
from ui.components.modals import PasswordResetModal, UserModal
from ui.theme import Theme


class UsersView(tk.Frame):
    """Módulo administrativo para la gestión de cuentas y control de accesos."""

    def __init__(
        self,
        parent: tk.Widget,
        current_user: User,
        auth_service: AuthService
    ):
        super().__init__(parent, bg=Theme.BG_MAIN)
        self.current_user = current_user
        self.auth_service = auth_service

        self._build_ui()
        if self.current_user.is_admin():
            self.refresh()
        else:
            self._show_access_denied()

    def _show_access_denied(self) -> None:
        """Muestra mensaje de restricción si un usuario sin rol administrativo accede."""
        for widget in self.winfo_children():
            widget.destroy()

        denied_frame = tk.Frame(self, bg=Theme.BG_CARD, padx=40, pady=40)
        denied_frame.place(relx=0.5, rely=0.5, anchor="center")

        lbl_icon = tk.Label(denied_frame, text="🔒", font=("Segoe UI", 48), fg=Theme.DANGER, bg=Theme.BG_CARD)
        lbl_icon.pack(pady=(0, 10))

        lbl_title = tk.Label(denied_frame, text="Acceso Restringido", font=Theme.FONT_TITLE_HERO, fg=Theme.DANGER, bg=Theme.BG_CARD)
        lbl_title.pack(pady=(0, 8))

        lbl_desc = tk.Label(
            denied_frame,
            text="Este módulo está reservado exclusivamente para cuentas con rol de Administrador.\nSu rol actual ('Operador') no cuenta con privilegios de gestión de usuarios.",
            font=Theme.FONT_BODY,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD,
            justify="center"
        )
        lbl_desc.pack()

    def _build_ui(self) -> None:
        """Construye la interfaz de administración de usuarios."""
        header = tk.Frame(self, bg=Theme.BG_MAIN)
        header.pack(fill="x", padx=24, pady=(20, 14))

        lbl_title = tk.Label(
            header,
            text="Control de Cuentas y Accesos",
            font=Theme.FONT_TITLE_HERO,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_MAIN
        )
        lbl_title.pack(side="left")

        btn_new = tk.Button(
            header,
            text="+ Nueva Cuenta",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._open_new_user_modal
        )
        btn_new.pack(side="right")

        # Barra de Acciones
        action_bar = tk.Frame(self, bg=Theme.BG_CARD, padx=14, pady=10)
        action_bar.pack(fill="x", padx=24, pady=(0, 14))

        lbl_info = tk.Label(
            action_bar,
            text="Gestión de credenciales con hashing seguro PBKDF2-HMAC-SHA256 y roles diferenciados",
            font=Theme.FONT_SMALL,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_CARD
        )
        lbl_info.pack(side="left")

        btn_reset_pass = tk.Button(
            action_bar,
            text="🔑 Restablecer Contraseña",
            font=Theme.FONT_BODY,
            bg=Theme.BORDER_COLOR,
            fg=Theme.TEXT_PRIMARY,
            activebackground=Theme.PRIMARY_BLUE,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._reset_password_selected
        )
        btn_reset_pass.pack(side="right")

        btn_toggle_active = tk.Button(
            action_bar,
            text="🔄 Habilitar / Deshabilitar",
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
        btn_toggle_active.pack(side="right", padx=(0, 8))

        # Tabla Treeview
        table_container = tk.Frame(self, bg=Theme.BG_CARD, padx=12, pady=12)
        table_container.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        columns = ("id", "username", "name", "role", "status", "created_at")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings")

        self.tree.heading("id", text="ID")
        self.tree.heading("username", text="USUARIO (LOGIN)")
        self.tree.heading("name", text="NOMBRE COMPLETO")
        self.tree.heading("role", text="ROL DE SISTEMA")
        self.tree.heading("status", text="ESTADO DE CUENTA")
        self.tree.heading("created_at", text="FECHA DE ALTA")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("username", width=160, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("role", width=140, anchor="center")
        self.tree.column("status", width=140, anchor="center")
        self.tree.column("created_at", width=170, anchor="center")

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def refresh(self) -> None:
        """Carga los usuarios del sistema."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            users = self.auth_service.get_all_users(requester=self.current_user)
            for u in users:
                status_str = "HABILITADO" if u.is_active else "DESHABILITADO"
                self.tree.insert(
                    "",
                    "end",
                    iid=str(u.id),
                    values=(
                        u.id,
                        u.username,
                        u.full_name,
                        u.role,
                        status_str,
                        u.created_at or "—"
                    )
                )
        except PermissionError as pe:
            messagebox.showerror("Permiso denegado", str(pe), parent=self)

    def _get_selected_user(self) -> Optional[User]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Seleccione un usuario de la lista.", parent=self)
            return None
        u_id = int(selected[0])
        # Buscar usuario
        users = self.auth_service.get_all_users(self.current_user)
        for u in users:
            if u.id == u_id:
                return u
        return None

    def _open_new_user_modal(self) -> None:
        UserModal(
            self,
            auth_service=self.auth_service,
            current_admin=self.current_user,
            on_success=self.refresh
        )

    def _toggle_active_selected(self) -> None:
        target = self._get_selected_user()
        if not target:
            return

        if target.id == self.current_user.id:
            messagebox.showwarning("Acción denegada", "No puedes deshabilitar tu propia cuenta activa de Administrador.", parent=self)
            return

        new_status = not target.is_active
        action_verb = "habilitar" if new_status else "deshabilitar"
        confirm = messagebox.askyesno(
            "Confirmar Estado de Cuenta",
            f"¿Desea {action_verb} el acceso a '{target.username}' ({target.full_name})?",
            parent=self
        )
        if confirm:
            try:
                self.auth_service.set_user_active_status(
                    user_id=target.id,
                    is_active=new_status,
                    requester=self.current_user
                )
                messagebox.showinfo("Éxito", f"Cuenta de '{target.username}' actualizada.", parent=self)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self)

    def _reset_password_selected(self) -> None:
        target = self._get_selected_user()
        if not target:
            return

        PasswordResetModal(
            self,
            auth_service=self.auth_service,
            target_user=target,
            current_admin=self.current_user,
            on_success=self.refresh
        )
