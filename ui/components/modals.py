"""
Módulo de Ventanas Modales y Formularios de Edición
NEXORA TASKS - Tópicos Avanzados de Programación

Implementa los diálogos emergentes reutilizables para Crear y Editar:
- Proyectos (ProjectModal)
- Integrantes (MemberModal)
- Tickets y Tareas (TicketModal)
- Cuentas de Acceso (UserModal y PasswordResetModal)
"""

from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models.member import Member
from models.project import Project
from models.ticket import Ticket
from models.user import User
from services.auth_service import AuthService
from services.member_service import MemberService
from services.project_service import ProjectService
from services.ticket_service import TicketService
from ui.theme import Theme


class BaseModal(tk.Toplevel):
    """Clase base para ventanas modales centradas y con tema oscuro."""

    def __init__(self, parent: tk.Widget, title: str, width: int = 520, height: int = 540):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=Theme.BG_MODAL)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())

        # Centrar la ventana respecto al padre
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()

        if parent_w > 100 and parent_h > 100:
            pos_x = parent_x + (parent_w - width) // 2
            pos_y = parent_y + (parent_h - height) // 2
        else:
            pos_x = (self.winfo_screenwidth() - width) // 2
            pos_y = (self.winfo_screenheight() - height) // 2

        self.geometry(f"{width}x{height}+{max(0, pos_x)}+{max(0, pos_y)}")

        # Forzar foco modal
        self.grab_set()

        # Encabezado estándar
        self.header_frame = tk.Frame(self, bg=Theme.BG_ROOT, height=50)
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        self.lbl_title = tk.Label(
            self.header_frame,
            text=title,
            font=Theme.FONT_TITLE_SECTION,
            fg=Theme.TEXT_PRIMARY,
            bg=Theme.BG_ROOT
        )
        self.lbl_title.pack(side="left", padx=20, pady=12)

        # Contenedor central scrolleable o con padding
        self.body_frame = tk.Frame(self, bg=Theme.BG_MODAL, padx=24, pady=16)
        self.body_frame.pack(fill="both", expand=True)

        # Pie con botones de acción
        self.footer_frame = tk.Frame(self, bg=Theme.BG_ROOT, height=60, padx=20)
        self.footer_frame.pack(fill="x", side="bottom")
        self.footer_frame.pack_propagate(False)

        self.btn_cancel = tk.Button(
            self.footer_frame,
            text="Cancelar",
            font=Theme.FONT_BODY,
            bg=Theme.BG_CARD,
            fg=Theme.TEXT_SECONDARY,
            activebackground=Theme.BORDER_COLOR,
            activeforeground=Theme.TEXT_PRIMARY,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.destroy
        )
        self.btn_cancel.pack(side="right", padx=(10, 0), pady=12)

    def _create_label(self, parent: tk.Widget, text: str) -> tk.Label:
        """Crea una etiqueta con tipografía y contraste adaptados al tema."""
        lbl = tk.Label(
            parent,
            text=text,
            font=Theme.FONT_SMALL_BOLD,
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_MODAL,
            anchor="w"
        )
        lbl.pack(fill="x", pady=(8, 2))
        return lbl

    def _create_entry(self, parent: tk.Widget, default_val: str = "") -> tk.Entry:
        """Crea una caja de texto adaptada al tema oscuro."""
        entry = tk.Entry(
            parent,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            highlightcolor=Theme.PRIMARY_BLUE
        )
        entry.pack(fill="x", ipady=4)
        if default_val:
            entry.insert(0, default_val)
        return entry


class ProjectModal(BaseModal):
    """Modal para dar de alta o modificar Proyectos."""

    def __init__(
        self,
        parent: tk.Widget,
        project_service: ProjectService,
        project: Optional[Project] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.project_service = project_service
        self.project = project
        self.on_success = on_success

        is_edit = project is not None
        title = "Editar Proyecto" if is_edit else "Nuevo Proyecto"
        super().__init__(parent, title, width=540, height=560)

        # Campos
        self._create_label(self.body_frame, "Clave Única del Proyecto (ej. NEX-01):")
        self.ent_code = self._create_entry(
            self.body_frame,
            default_val=project.code if is_edit else ""
        )

        self._create_label(self.body_frame, "Nombre del Proyecto:")
        self.ent_name = self._create_entry(
            self.body_frame,
            default_val=project.name if is_edit else ""
        )

        self._create_label(self.body_frame, "Fecha de Inicio (AAAA-MM-DD):")
        default_date = project.start_date if is_edit else date.today().isoformat()
        self.ent_date = self._create_entry(self.body_frame, default_val=default_date)

        self._create_label(self.body_frame, "Estado del Proyecto:")
        self.cmb_status = ttk.Combobox(
            self.body_frame,
            values=list(Project.VALID_STATUSES),
            state="readonly",
            font=Theme.FONT_BODY
        )
        self.cmb_status.set(project.status if is_edit else "Planificación")
        self.cmb_status.pack(fill="x", ipady=4)

        self._create_label(self.body_frame, "Descripción / Alcance:")
        self.txt_desc = tk.Text(
            self.body_frame,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            height=4,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            highlightcolor=Theme.PRIMARY_BLUE
        )
        self.txt_desc.pack(fill="x", pady=(0, 10))
        if is_edit and project.description:
            self.txt_desc.insert("1.0", project.description)

        # Botón Guardar en footer
        self.btn_save = tk.Button(
            self.footer_frame,
            text="Guardar Cambios" if is_edit else "Crear Proyecto",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self._save
        )
        self.btn_save.pack(side="right", pady=12)

    def _save(self) -> None:
        code = self.ent_code.get().strip()
        name = self.ent_name.get().strip()
        start_date = self.ent_date.get().strip()
        status = self.cmb_status.get()
        description = self.txt_desc.get("1.0", "end-1c").strip()

        try:
            if self.project is None:
                # Crear nuevo
                self.project_service.create_project(
                    code=code,
                    name=name,
                    start_date=start_date,
                    status=status,
                    description=description
                )
                messagebox.showinfo("Éxito", f"Proyecto '{code}' creado satisfactoriamente.", parent=self)
            else:
                # Editar existente
                self.project_service.update_project(
                    project_id=self.project.id,
                    code=code,
                    name=name,
                    start_date=start_date,
                    status=status,
                    description=description
                )
                messagebox.showinfo("Éxito", f"Proyecto '{code}' actualizado correctamente.", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error al guardar proyecto", str(e), parent=self)


class MemberModal(BaseModal):
    """Modal para dar de alta o modificar Integrantes del Equipo."""

    def __init__(
        self,
        parent: tk.Widget,
        member_service: MemberService,
        member: Optional[Member] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.member_service = member_service
        self.member = member
        self.on_success = on_success

        is_edit = member is not None
        title = "Editar Integrante" if is_edit else "Nuevo Integrante"
        super().__init__(parent, title, width=520, height=550)

        self._create_label(self.body_frame, "Nombre Completo:")
        self.ent_name = self._create_entry(
            self.body_frame,
            default_val=member.full_name if is_edit else ""
        )

        self._create_label(self.body_frame, "Correo Electrónico (Único):")
        self.ent_email = self._create_entry(
            self.body_frame,
            default_val=member.email if is_edit else ""
        )

        self._create_label(self.body_frame, "Cargo / Rol Técnico:")
        self.ent_role = self._create_entry(
            self.body_frame,
            default_val=member.role_title if is_edit else ""
        )

        self._create_label(self.body_frame, "Departamento / Área:")
        self.ent_dept = self._create_entry(
            self.body_frame,
            default_val=member.department if is_edit else ""
        )

        self._create_label(self.body_frame, "Teléfono de Contacto (Opcional):")
        self.ent_phone = self._create_entry(
            self.body_frame,
            default_val=member.phone if (is_edit and member.phone) else ""
        )

        # Checkbox Activo / Inactivo
        self.var_active = tk.BooleanVar(value=member.is_active if is_edit else True)
        self.chk_active = tk.Checkbutton(
            self.body_frame,
            text="Miembro Activo (Disponible para asignación de tickets)",
            variable=self.var_active,
            font=Theme.FONT_BODY,
            bg=Theme.BG_MODAL,
            fg=Theme.TEXT_PRIMARY,
            selectcolor=Theme.BG_CARD,
            activebackground=Theme.BG_MODAL,
            activeforeground=Theme.TEXT_PRIMARY
        )
        self.chk_active.pack(anchor="w", pady=(14, 0))

        # Botón Guardar
        self.btn_save = tk.Button(
            self.footer_frame,
            text="Guardar Cambios" if is_edit else "Registrar Miembro",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self._save
        )
        self.btn_save.pack(side="right", pady=12)

    def _save(self) -> None:
        full_name = self.ent_name.get().strip()
        email = self.ent_email.get().strip()
        role_title = self.ent_role.get().strip()
        department = self.ent_dept.get().strip()
        phone = self.ent_phone.get().strip()
        is_active = self.var_active.get()

        try:
            if self.member is None:
                new_m = self.member_service.register_member(
                    full_name=full_name,
                    email=email,
                    role_title=role_title,
                    department=department,
                    phone=phone
                )
                if not is_active:
                    self.member_service.set_active_status(new_m.id, False)
                messagebox.showinfo("Éxito", f"Miembro '{full_name}' registrado exitosamente.", parent=self)
            else:
                self.member_service.update_member_details(
                    member_id=self.member.id,
                    full_name=full_name,
                    email=email,
                    role_title=role_title,
                    department=department,
                    phone=phone,
                    is_active=is_active
                )
                messagebox.showinfo("Éxito", f"Miembro '{full_name}' actualizado correctamente.", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error al guardar miembro", str(e), parent=self)


class TicketModal(BaseModal):
    """Modal para crear y editar Tickets / Tareas con validaciones de negocio."""

    def __init__(
        self,
        parent: tk.Widget,
        ticket_service: TicketService,
        project_service: ProjectService,
        member_service: MemberService,
        ticket: Optional[Ticket] = None,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.ticket_service = ticket_service
        self.project_service = project_service
        self.member_service = member_service
        self.ticket = ticket
        self.on_success = on_success

        is_edit = ticket is not None
        title = "Editar Ticket / Tarea" if is_edit else "Nuevo Ticket"
        super().__init__(parent, title, width=580, height=640)

        # Obtener listas de proyectos y miembros
        all_projects = self.project_service.get_all_projects()
        # Regla: Si es nuevo ticket, no permitir seleccionar proyectos cerrados
        if not is_edit:
            self.projects = [p for p in all_projects if p.status not in ("Completado", "Cancelado")]
        else:
            self.projects = all_projects

        # Regla: Filtrar miembros activos
        self.members = self.member_service.get_all_members(active_only=True)

        # Mapeos para Combobox
        self.proj_map = {f"[{p.code}] {p.name}": p.id for p in self.projects}
        self.member_map = {"(Sin asignar)": None}
        for m in self.members:
            self.member_map[f"{m.full_name} ({m.email})"] = m.id

        # Campos
        self._create_label(self.body_frame, "Código Único del Ticket (ej. TCK-101):")
        self.ent_code = self._create_entry(
            self.body_frame,
            default_val=ticket.ticket_code if is_edit else ""
        )

        self._create_label(self.body_frame, "Título o Asunto de la Tarea:")
        self.ent_title = self._create_entry(
            self.body_frame,
            default_val=ticket.title if is_edit else ""
        )

        self._create_label(self.body_frame, "Proyecto Asociado:")
        self.cmb_proj = ttk.Combobox(
            self.body_frame,
            values=list(self.proj_map.keys()),
            state="readonly",
            font=Theme.FONT_BODY
        )
        if is_edit:
            curr_proj = self.project_service.get_project_by_id(ticket.project_id)
            if curr_proj:
                key = f"[{curr_proj.code}] {curr_proj.name}"
                self.cmb_proj.set(key)
        elif self.projects:
            self.cmb_proj.current(0)
        self.cmb_proj.pack(fill="x", ipady=3)

        self._create_label(self.body_frame, "Responsable Asignado (Solo miembros activos):")
        self.cmb_member = ttk.Combobox(
            self.body_frame,
            values=list(self.member_map.keys()),
            state="readonly",
            font=Theme.FONT_BODY
        )
        if is_edit and ticket.assigned_member_id:
            curr_m = self.member_service.get_member_by_id(ticket.assigned_member_id)
            if curr_m:
                key = f"{curr_m.full_name} ({curr_m.email})"
                if key not in self.member_map:
                    self.member_map[key] = curr_m.id
                    self.cmb_member["values"] = list(self.member_map.keys())
                self.cmb_member.set(key)
            else:
                self.cmb_member.set("(Sin asignar)")
        else:
            self.cmb_member.set("(Sin asignar)")
        self.cmb_member.pack(fill="x", ipady=3)

        # Fila horizontal: Prioridad, Estado y Fecha límite
        row_frame = tk.Frame(self.body_frame, bg=Theme.BG_MODAL)
        row_frame.pack(fill="x", pady=(6, 0))

        # Prioridad
        col1 = tk.Frame(row_frame, bg=Theme.BG_MODAL)
        col1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        lbl_prio = tk.Label(col1, text="Prioridad:", font=Theme.FONT_SMALL_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MODAL)
        lbl_prio.pack(anchor="w", pady=(0, 2))
        self.cmb_prio = ttk.Combobox(col1, values=list(Ticket.VALID_PRIORITIES), state="readonly", font=Theme.FONT_BODY)
        self.cmb_prio.set(ticket.priority if is_edit else "Media")
        self.cmb_prio.pack(fill="x")

        # Estado
        col2 = tk.Frame(row_frame, bg=Theme.BG_MODAL)
        col2.pack(side="left", fill="x", expand=True, padx=6)
        lbl_st = tk.Label(col2, text="Estado:", font=Theme.FONT_SMALL_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MODAL)
        lbl_st.pack(anchor="w", pady=(0, 2))
        self.cmb_status = ttk.Combobox(col2, values=list(Ticket.VALID_STATUSES), state="readonly", font=Theme.FONT_BODY)
        self.cmb_status.set(ticket.status if is_edit else "Pendiente")
        self.cmb_status.pack(fill="x")

        # Fecha límite
        col3 = tk.Frame(row_frame, bg=Theme.BG_MODAL)
        col3.pack(side="left", fill="x", expand=True, padx=(6, 0))
        lbl_due = tk.Label(col3, text="Vence (AAAA-MM-DD):", font=Theme.FONT_SMALL_BOLD, fg=Theme.TEXT_SECONDARY, bg=Theme.BG_MODAL)
        lbl_due.pack(anchor="w", pady=(0, 2))
        default_due = ticket.due_date if is_edit else (date.today() + timedelta(days=7)).isoformat()
        self.ent_due = tk.Entry(
            col3,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            highlightcolor=Theme.PRIMARY_BLUE
        )
        self.ent_due.insert(0, default_due)
        self.ent_due.pack(fill="x", ipady=2)

        self._create_label(self.body_frame, "Descripción Técnica / Pasos:")
        self.txt_desc = tk.Text(
            self.body_frame,
            font=Theme.FONT_BODY,
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            height=3,
            relief="solid",
            highlightthickness=1,
            highlightbackground=Theme.BORDER_COLOR,
            highlightcolor=Theme.PRIMARY_BLUE
        )
        self.txt_desc.pack(fill="x", pady=(0, 6))
        if is_edit and ticket.description:
            self.txt_desc.insert("1.0", ticket.description)

        # Botón Guardar
        self.btn_save = tk.Button(
            self.footer_frame,
            text="Guardar Cambios" if is_edit else "Crear Ticket",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self._save
        )
        self.btn_save.pack(side="right", pady=12)

    def _save(self) -> None:
        code = self.ent_code.get().strip()
        title = self.ent_title.get().strip()
        proj_str = self.cmb_proj.get()
        member_str = self.cmb_member.get()
        priority = self.cmb_prio.get()
        status = self.cmb_status.get()
        due_date = self.ent_due.get().strip()
        description = self.txt_desc.get("1.0", "end-1c").strip()

        project_id = self.proj_map.get(proj_str)
        if project_id is None:
            messagebox.showerror("Error", "Debe seleccionar un proyecto válido.", parent=self)
            return

        assigned_id = self.member_map.get(member_str)

        try:
            if self.ticket is None:
                self.ticket_service.create_ticket(
                    ticket_code=code,
                    title=title,
                    project_id=project_id,
                    priority=priority,
                    due_date=due_date,
                    status=status,
                    description=description,
                    assigned_member_id=assigned_id
                )
                messagebox.showinfo("Éxito", f"Ticket '{code}' creado con éxito.", parent=self)
            else:
                self.ticket_service.update_ticket(
                    ticket_id=self.ticket.id,
                    ticket_code=code,
                    title=title,
                    project_id=project_id,
                    priority=priority,
                    due_date=due_date,
                    status=status,
                    description=description,
                    assigned_member_id=assigned_id
                )
                messagebox.showinfo("Éxito", f"Ticket '{code}' actualizado con éxito.", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error al guardar ticket", str(e), parent=self)


class UserModal(BaseModal):
    """Modal de Creación de Usuarios (Exclusivo para rol Administrador)."""

    def __init__(
        self,
        parent: tk.Widget,
        auth_service: AuthService,
        current_admin: User,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.auth_service = auth_service
        self.current_admin = current_admin
        self.on_success = on_success

        super().__init__(parent, "Crear Cuenta de Acceso", width=480, height=480)

        self._create_label(self.body_frame, "Nombre de Usuario (Login):")
        self.ent_user = self._create_entry(self.body_frame)

        self._create_label(self.body_frame, "Nombre Completo:")
        self.ent_name = self._create_entry(self.body_frame)

        self._create_label(self.body_frame, "Rol de Sistema:")
        self.cmb_role = ttk.Combobox(
            self.body_frame,
            values=["Operador", "Administrador"],
            state="readonly",
            font=Theme.FONT_BODY
        )
        self.cmb_role.set("Operador")
        self.cmb_role.pack(fill="x", ipady=3)

        self._create_label(self.body_frame, "Contraseña Temporal (mínimo 6 car.):")
        self.ent_pass = tk.Entry(
            self.body_frame,
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
        self.ent_pass.pack(fill="x", ipady=4)

        self._create_label(self.body_frame, "Confirmar Contraseña:")
        self.ent_pass2 = tk.Entry(
            self.body_frame,
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
        self.ent_pass2.pack(fill="x", ipady=4)

        # Botón Guardar
        self.btn_save = tk.Button(
            self.footer_frame,
            text="Crear Cuenta",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self._save
        )
        self.btn_save.pack(side="right", pady=12)

    def _save(self) -> None:
        user = self.ent_user.get().strip()
        name = self.ent_name.get().strip()
        role = self.cmb_role.get()
        p1 = self.ent_pass.get()
        p2 = self.ent_pass2.get()

        if p1 != p2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=self)
            return

        try:
            self.auth_service.register_user(
                username=user,
                password=p1,
                full_name=name,
                role=role,
                requester=self.current_admin
            )
            messagebox.showinfo("Éxito", f"Usuario '{user}' creado correctamente con rol '{role}'.", parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error al crear usuario", str(e), parent=self)


class PasswordResetModal(BaseModal):
    """Modal para que el Administrador restablezca la contraseña de una cuenta."""

    def __init__(
        self,
        parent: tk.Widget,
        auth_service: AuthService,
        target_user: User,
        current_admin: User,
        on_success: Optional[Callable[[], None]] = None
    ):
        self.auth_service = auth_service
        self.target_user = target_user
        self.current_admin = current_admin
        self.on_success = on_success

        super().__init__(parent, f"Restablecer Contraseña: {target_user.username}", width=440, height=330)

        lbl_info = tk.Label(
            self.body_frame,
            text=f"Asignando nueva contraseña a:\n{target_user.full_name} ({target_user.role})",
            font=Theme.FONT_BODY_BOLD,
            fg=Theme.ACCENT_CYAN,
            bg=Theme.BG_MODAL,
            justify="left"
        )
        lbl_info.pack(anchor="w", pady=(0, 10))

        self._create_label(self.body_frame, "Nueva Contraseña (mínimo 6 caracteres):")
        self.ent_p1 = tk.Entry(
            self.body_frame,
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
        self.ent_p1.pack(fill="x", ipady=4)

        self._create_label(self.body_frame, "Confirmar Nueva Contraseña:")
        self.ent_p2 = tk.Entry(
            self.body_frame,
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
        self.ent_p2.pack(fill="x", ipady=4)

        self.btn_save = tk.Button(
            self.footer_frame,
            text="Actualizar Contraseña",
            font=Theme.FONT_BODY_BOLD,
            bg=Theme.PRIMARY_BLUE,
            fg="#ffffff",
            activebackground=Theme.PRIMARY_HOVER,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self._save
        )
        self.btn_save.pack(side="right", pady=12)

    def _save(self) -> None:
        p1 = self.ent_p1.get()
        p2 = self.ent_p2.get()

        if p1 != p2:
            messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=self)
            return

        try:
            self.auth_service.admin_reset_password(
                user_id=self.target_user.id,
                new_password=p1,
                requester=self.current_admin
            )
            messagebox.showinfo("Éxito", f"Contraseña actualizada para {self.target_user.username}.", parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
