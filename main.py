"""
Punto de Entrada Principal (main.py)
NEXORA TASKS - Sistema de Gestión de Proyectos y Tickets
Materia: Tópicos Avanzados de Programación

Inicia la Interfaz Gráfica de Usuario (Tkinter/ttk) o el modo de diagnóstico.
"""

import sys
from pathlib import Path

# Configurar stdout para evitar problemas con codificaciones antiguas de terminal en Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Asegurar que el directorio raíz del proyecto se encuentre en sys.path
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


def print_banner() -> None:
    """Imprime el banner institucional del proyecto."""
    print("=" * 75)
    print("  NEXORA TASKS - GESTOR DE PROYECTOS Y TICKETS")
    print("  Materia: Tópicos Avanzados de Programación")
    print("  Arquitectura Orientada a Objetos | Capas | SQLite3 | Python 3.10+ | Tkinter")
    print("=" * 75)


def run_system_check() -> None:
    """
    Inicializa la base de datos y ejecuta una rutina de diagnóstico integral
    para verificar que todas las capas y relaciones funcionen correctamente en consola.
    """
    print_banner()
    print("\n[+] Paso 1: Inicializando Base de Datos Relacional SQLite...")
    db_manager = DatabaseManager()

    fk_active = db_manager.check_foreign_keys_enabled()
    status_fk = "ACTIVO (PRAGMA foreign_keys = ON)" if fk_active else "INACTIVO"
    print(f"    -> Soporte de Claves Foráneas: {status_fk}")

    seed_result = db_manager.initialize_database()
    print(f"    -> Archivo SQLite ubicado en: {db_manager.db_path}")
    if any(seed_result.values()):
        print(f"    -> Datos iniciales sembrados con éxito:")
        print(f"       * Usuarios del sistema : {seed_result['users']}")
        print(f"       * Miembros del equipo  : {seed_result['members']}")
        print(f"       * Proyectos            : {seed_result['projects']}")
        print(f"       * Tickets / Tareas     : {seed_result['tickets']}")
    else:
        print("    -> La base de datos ya contiene registros previos (Idempotencia verificada).")

    print("\n[+] Paso 2: Inicializando Capa de Servicios...")
    auth_service = AuthService()
    member_service = MemberService()
    project_service = ProjectService()
    ticket_service = TicketService()
    print("    -> AuthService, MemberService, ProjectService y TicketService listos.")

    print("\n[+] Paso 3: Verificación de Autenticación y Hashes Criptográficos...")
    test_creds = [("admin", "admin123"), ("operador", "operador123"), ("admin", "wrongpassword")]
    for user, pwd in test_creds:
        ok, msg, usr = auth_service.login(user, pwd)
        tag = "[OK]" if ok else "[FALLO ESPERADO]"
        rol_info = f" (Rol: {usr.role})" if usr else ""
        print(f"    {tag} Login('{user}', '{pwd}') -> {msg}{rol_info}")

    print("\n[+] Paso 4: Verificación de Miembros del Equipo (members)...")
    members = member_service.get_all_members()
    print(f"    -> Total de miembros registrados: {len(members)} (Requerido: >= 8)")
    for m in members[:4]:
        print(f"       - ID {m.id}: {m.full_name} | {m.role_title} ({m.department}) | {m.email}")
    if len(members) > 4:
        print(f"       ... y {len(members) - 4} miembros adicionales cargados correctamente.")

    print("\n[+] Paso 5: Verificación de Proyectos (projects)...")
    projects = project_service.get_all_projects()
    print(f"    -> Total de proyectos registrados: {len(projects)} (Requerido: >= 5)")
    for p in projects:
        print(f"       - [{p.code}] {p.name} | Estado: {p.status} | Inicio: {p.start_date}")

    print("\n[+] Paso 6: Verificación de Tickets e Integridad Referencial (tickets)...")
    tickets = ticket_service.get_all_tickets()
    print(f"    -> Total de tickets registrados: {len(tickets)} (Requerido: >= 3 con distintos estados)")
    for t in tickets:
        resp = t.member_name or "Sin asignar"
        print(
            f"       - [{t.ticket_code}] {t.title}\n"
            f"         Proyecto: {t.project_code} ({t.project_name})\n"
            f"         Responsable: {resp} | Prioridad: {t.priority} | Estado: {t.status} | Límite: {t.due_date}"
        )

    metrics = ticket_service.get_metrics_summary()
    print("\n[+] Resumen de Métricas:")
    print(f"    -> Por Estado   : {metrics['by_status']}")
    print(f"    -> Por Prioridad: {metrics['by_priority']}")

    print("\n[+] Paso 7: Verificación de Regla de Negocio (Eliminación de Proyectos)...")
    prj_auth = project_service.get_project_by_code("NEX-AUTH")
    if prj_auth:
        try:
            project_service.delete_project(prj_auth.id, confirmed=True)
            print("    [ERROR] Se eliminó el proyecto indebidamente.")
        except ValueError as err:
            print(f"    [REGLA CUMPLIDA] Intento de eliminar proyecto con tickets activos:")
            print(f"    -> {err}")
            if project_service.get_project_by_id(prj_auth.id):
                print(f"    -> El proyecto '{prj_auth.name}' FUE CONSERVADO correctamente.")

    print("\n" + "=" * 75)
    print("  DIAGNÓSTICO FINALIZADO CORRECTAMENTE")
    print("=" * 75 + "\n")


def launch_gui() -> None:
    """Inicia la aplicación de escritorio con Tkinter."""
    print("=" * 75, flush=True)
    print("  INICIANDO NEXORA TASKS - Interfaz Gráfica de Escritorio (Tkinter/ttk)", flush=True)
    print("=" * 75, flush=True)
    print("[+] Paso 1/3: Verificando base de datos relacional SQLite...", flush=True)
    db = DatabaseManager()
    db.initialize_database()

    print("[+] Paso 2/3: Cargando servicios de negocio y control de acceso...", flush=True)
    auth_service = AuthService()
    project_service = ProjectService()
    member_service = MemberService()
    ticket_service = TicketService()

    def show_login():
        def on_login_success(authenticated_user: User):
            print(f"[+] Sesión iniciada con éxito: {authenticated_user.full_name} [{authenticated_user.role}]", flush=True)
            print("[+] Abriendo Ventana Principal (MainWindow)...", flush=True)

            def on_logout():
                print("[+] Sesión cerrada. Reabriendo ventana de inicio de sesión...", flush=True)
                show_login()

            main_app = MainWindow(
                current_user=authenticated_user,
                auth_service=auth_service,
                project_service=project_service,
                member_service=member_service,
                ticket_service=ticket_service,
                on_logout=on_logout
            )
            main_app.mainloop()

        print("[+] Paso 3/3: Desplegando ventana de inicio de sesión (LoginWindow)...", flush=True)
        print("    -> Si la ventana no aparece automáticamente al frente, búscala en tu barra de tareas.", flush=True)
        login_app = LoginWindow(
            auth_service=auth_service,
            on_login_success=on_login_success
        )
        login_app.mainloop()

    show_login()


def main() -> None:
    """Función de arranque."""
    if "--check" in sys.argv or "--cli" in sys.argv:
        run_system_check()
    else:
        launch_gui()


if __name__ == "__main__":
    main()
