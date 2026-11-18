"""
Script de Prueba Automatizada de Interfaz Gráfica (UI Smoke Test)
NEXORA TASKS - Tópicos Avanzados de Programación

Verifica que todas las ventanas, vistas, modales y componentes de Tkinter/ttk
se inicialicen, rendericen y naveguen correctamente sin errores de sintaxis o ejecución.
"""

import sys
from pathlib import Path

# Configurar stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.database import DatabaseManager
from models.user import User
from services.auth_service import AuthService
from services.member_service import MemberService
from services.project_service import ProjectService
from services.ticket_service import TicketService
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.components.modals import (
    ProjectModal,
    MemberModal,
    TicketModal,
    UserModal,
    PasswordResetModal
)


def run_ui_tests():
    print(">>> Iniciando pruebas automatizadas de Interfaz Gráfica (Tkinter/ttk)...")

    # 1. Base de datos y servicios
    db = DatabaseManager("test_ui_sandbox.db")
    db.initialize_database()

    from repositories.user_repository import UserRepository
    from repositories.project_repository import ProjectRepository
    from repositories.member_repository import MemberRepository
    from repositories.ticket_repository import TicketRepository

    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)
    member_repo = MemberRepository(db)
    ticket_repo = TicketRepository(db)

    auth_service = AuthService(user_repo)
    project_service = ProjectService(project_repo, ticket_repo)
    member_service = MemberService(member_repo)
    ticket_service = TicketService(ticket_repo, project_repo, member_repo)

    # 2. Prueba de inicialización de LoginWindow
    print("  [+] Probando inicialización de LoginWindow...")
    logged_user = None

    def dummy_success(u: User):
        nonlocal logged_user
        logged_user = u

    login_win = LoginWindow(auth_service=auth_service, on_login_success=dummy_success)
    login_win.withdraw()  # Ocultar para prueba headless
    login_win.update()

    # Simular autocompletado y login
    login_win._prefill("admin", "admin123")
    login_win._handle_login()
    assert logged_user is not None, "El login de admin debió ser exitoso."
    assert logged_user.is_admin() is True
    print("  [OK] LoginWindow inicializada y validada exitosamente con AuthService.")

    # 3. Prueba de inicialización de MainWindow con perfil Administrador
    print("  [+] Probando MainWindow con perfil Administrador...")
    main_admin = MainWindow(
        current_user=logged_user,
        auth_service=auth_service,
        project_service=project_service,
        member_service=member_service,
        ticket_service=ticket_service
    )
    main_admin.withdraw()
    main_admin.update()

    # Verificar que el botón de usuarios esté presente para el Administrador
    assert "users" in main_admin.nav_buttons, "El botón 'users' debe estar presente para el Administrador."

    # Probar navegación a cada una de las 6 vistas
    vistas = ["dashboard", "projects", "members", "tickets", "reports", "users"]
    for v in vistas:
        main_admin.navigate_to(v)
        main_admin.update()
        assert v in main_admin.views, f"La vista '{v}' debió cargarse."
        print(f"      -> Vista '{v}' cargada y renderizada correctamente.")

    print("  [OK] MainWindow (Admin) navegó exitosamente por todos los 6 módulos.")

    # 4. Prueba de modales sobre MainWindow Admin
    print("  [+] Probando inicialización de ventanas modales...")
    # Modal Proyecto
    p_modal = ProjectModal(main_admin, project_service=project_service)
    p_modal.withdraw()
    p_modal.update()
    p_modal.destroy()
    print("      -> ProjectModal OK.")

    # Modal Miembro
    m_modal = MemberModal(main_admin, member_service=member_service)
    m_modal.withdraw()
    m_modal.update()
    m_modal.destroy()
    print("      -> MemberModal OK.")

    # Modal Ticket
    t_modal = TicketModal(
        main_admin,
        ticket_service=ticket_service,
        project_service=project_service,
        member_service=member_service
    )
    t_modal.withdraw()
    t_modal.update()
    t_modal.destroy()
    print("      -> TicketModal OK.")

    # Modal Usuario (Admin)
    u_modal = UserModal(main_admin, auth_service=auth_service, current_admin=logged_user)
    u_modal.withdraw()
    u_modal.update()
    u_modal.destroy()
    print("      -> UserModal OK.")

    # Modal Reset Password
    pw_modal = PasswordResetModal(
        main_admin,
        auth_service=auth_service,
        target_user=logged_user,
        current_admin=logged_user
    )
    pw_modal.withdraw()
    pw_modal.update()
    pw_modal.destroy()
    print("      -> PasswordResetModal OK.")

    main_admin.destroy()

    # 5. Prueba de MainWindow con perfil Operador (Permisos restringidos)
    print("  [+] Probando MainWindow con perfil Operador (Permisos restringidos)...")
    ok, _, oper_user = auth_service.login("operador", "operador123")
    assert ok and oper_user is not None and oper_user.is_operator()

    main_oper = MainWindow(
        current_user=oper_user,
        auth_service=auth_service,
        project_service=project_service,
        member_service=member_service,
        ticket_service=ticket_service
    )
    main_oper.withdraw()
    main_oper.update()

    # Verificar que el botón de usuarios NO esté en el menú del Operador
    assert "users" not in main_oper.nav_buttons, "El botón 'users' NO debe estar disponible para el Operador."

    # Navegar por los módulos permitidos para el Operador
    for v in ["dashboard", "projects", "members", "tickets", "reports"]:
        main_oper.navigate_to(v)
        main_oper.update()
        print(f"      -> Módulo '{v}' accesible para Operador.")

    main_oper.destroy()
    print("  [OK] Restricción de permisos para Operador verificada con éxito en la interfaz.")

    # 6. Limpieza de sandbox
    import os
    if os.path.exists("test_ui_sandbox.db"):
        os.remove("test_ui_sandbox.db")

    print("\n>>> ¡TODAS LAS PRUEBAS DE INTERFAZ GRÁFICA COMPLETADAS SATISFACTORIAMENTE!")


if __name__ == "__main__":
    run_ui_tests()
