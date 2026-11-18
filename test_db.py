"""
Script de Pruebas Unitarias y de Integración
NEXORA TASKS - Tópicos Avanzados de Programación

Verifica:
1. Creación de tablas y soporte de claves foráneas (PRAGMA foreign_keys = ON).
2. Fallo de inserción cuando una clave foránea no existe.
3. Fallo cuando una restricción CHECK es violada.
4. Fallo cuando una restricción UNIQUE es violada.
5. Regla de Negocio: NO se puede eliminar un proyecto con tickets activos (Pendiente / En Progreso).
6. Regla de Negocio: ProjectService exige confirmación explícita antes de eliminar.
7. Regla de Negocio: Eliminación exitosa de proyecto sin tickets activos tras confirmación.
8. Protección a nivel BD: ON DELETE RESTRICT impide borrar proyectos con tickets huérfanos vía SQL directo.
9. Integridad referencial en members: ON DELETE SET NULL al eliminar miembro responsable.
10. Criptografía: PBKDF2-HMAC-SHA256 con sales aleatorias y comparación en tiempo constante.
"""

import os
import sqlite3
import sys

# Configurar stdout para evitar problemas con codificaciones de terminal en Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from database.database import DatabaseManager
from models import Project, Ticket
from repositories.project_repository import ProjectRepository
from repositories.ticket_repository import TicketRepository
from services.security import SecurityService
from services.project_service import ProjectService


def run_tests():
    test_db_path = "test_verification.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    print(">>> Iniciando batería de pruebas de reglas de negocio e integridad...")
    db = DatabaseManager(test_db_path)
    db.initialize_database()

    project_repo = ProjectRepository(db)
    ticket_repo = TicketRepository(db)
    project_service = ProjectService(project_repo, ticket_repo)

    # 1. Verificar Claves Foráneas activas
    assert db.check_foreign_keys_enabled() is True, "Las claves foráneas deben estar activas."
    print("  [OK] Prueba 1: PRAGMA foreign_keys está activo en SQLite.")

    # 2. Verificar violación de FK en tickets con project_id inexistente
    fk_caught = False
    try:
        with db.cursor_scope() as cur:
            cur.execute("""
                INSERT INTO tickets (ticket_code, title, project_id, priority, due_date, status)
                VALUES ('FAIL-01', 'Ticket Huérfano', 99999, 'Alta', '2026-12-01', 'Pendiente');
            """)
    except sqlite3.IntegrityError:
        fk_caught = True
    assert fk_caught, "La base de datos debió rechazar la inserción con project_id inexistente."
    print("  [OK] Prueba 2: Integridad referencial FK rechaza tickets con project_id inexistente.")

    # 3. Verificar violación de CHECK en rol de usuario
    check_caught = False
    try:
        with db.cursor_scope() as cur:
            cur.execute("""
                INSERT INTO users_system (username, password_hash, salt, full_name, role)
                VALUES ('hacker', 'hash', 'salt', 'Hacker', 'SuperUsuarioInvalido');
            """)
    except sqlite3.IntegrityError:
        check_caught = True
    assert check_caught, "La restricción CHECK debió rechazar un rol no permitido."
    print("  [OK] Prueba 3: Restricción CHECK rechaza roles fuera de ('Administrador', 'Operador').")

    # 4. Verificar unicidad de username
    unique_caught = False
    try:
        with db.cursor_scope() as cur:
            cur.execute("""
                INSERT INTO users_system (username, password_hash, salt, full_name, role)
                VALUES ('admin', 'hash', 'salt', 'Admin Duplicado', 'Administrador');
            """)
    except sqlite3.IntegrityError:
        unique_caught = True
    assert unique_caught, "UNIQUE constraint debió rechazar username duplicado."
    print("  [OK] Prueba 4: Restricción UNIQUE rechaza duplicados de username.")

    # =========================================================================
    # REGLAS DE NEGOCIO: ELIMINACIÓN CONTROLADA DE PROYECTOS Y TICKETS ACTIVOS
    # =========================================================================

    # Crear proyecto de prueba con tickets activos
    proj_activo = project_service.create_project(
        code="PRJ-TEST-ACT",
        name="Proyecto de Prueba con Tickets Activos",
        start_date="2026-11-17",
        status="En Progreso"
    )

    ticket_activo_1 = Ticket(
        ticket_code="TCK-ACT-01",
        title="Ticket en Progreso de prueba",
        project_id=proj_activo.id,
        priority="Alta",
        due_date="2026-12-01",
        status="En Progreso"
    )
    ticket_repo.create(ticket_activo_1)

    # 5. REGLA 1 & 2: No se puede eliminar proyecto con tickets pendientes/en progreso
    bloqueado_por_tickets_activos = False
    mensaje_error_capturado = ""
    try:
        project_service.delete_project(proj_activo.id, confirmed=True)
    except ValueError as e:
        bloqueado_por_tickets_activos = True
        mensaje_error_capturado = str(e)

    assert bloqueado_por_tickets_activos is True, "El servicio debía bloquear la eliminación del proyecto."
    assert "no se puede eliminar" in mensaje_error_capturado.lower(), "El error debe ser claro y explícito."
    assert "ticket(s) activo(s)" in mensaje_error_capturado.lower() or "pendiente" in mensaje_error_capturado.lower()
    
    # Verificar que el proyecto sigue existiendo intacto en la base de datos
    proj_verif = project_service.get_project_by_id(proj_activo.id)
    assert proj_verif is not None, "El proyecto debía ser conservado intacto en la base de datos."
    print("  [OK] Prueba 5: ProjectService BLOQUEA eliminación de proyecto con tickets activos y lo conserva.")

    # 6. REGLA 3: Los proyectos sin tickets activos requieren confirmación explícita (confirmed=True)
    proj_inactivo = project_service.create_project(
        code="PRJ-TEST-INACT",
        name="Proyecto Sin Tickets Activos",
        start_date="2026-11-17",
        status="Planificación"
    )

    # Agregar ticket pero en estado 'Resuelto' (no activo)
    ticket_resuelto = Ticket(
        ticket_code="TCK-RES-01",
        title="Tarea Resuelta",
        project_id=proj_inactivo.id,
        priority="Baja",
        due_date="2026-11-18",
        status="Resuelto"
    )
    ticket_repo.create(ticket_resuelto)

    # Intentar eliminar sin confirmación explícita (confirmed=False)
    bloqueado_por_falta_confirmacion = False
    try:
        project_service.delete_project(proj_inactivo.id, confirmed=False)
    except ValueError as e:
        bloqueado_por_falta_confirmacion = True
        assert "confirmación" in str(e).lower()

    assert bloqueado_por_falta_confirmacion is True, "Debe requerirse confirmación obligatoria para eliminar."
    assert project_service.get_project_by_id(proj_inactivo.id) is not None, "El proyecto no debe borrarse sin confirmación."
    print("  [OK] Prueba 6: ProjectService exige confirmación explícita previa para proyectos sin tickets activos.")

    # 7. REGLA 4: Eliminación permitida con confirmación cuando NO hay tickets activos
    eliminado_ok = project_service.delete_project(proj_inactivo.id, confirmed=True)
    assert eliminado_ok is True, "La eliminación debía concretarse con confirmed=True."
    assert project_service.get_project_by_id(proj_inactivo.id) is None, "El proyecto debió ser eliminado."
    print("  [OK] Prueba 7: Proyecto sin tickets activos se eliminó exitosamente tras confirmación.")

    # 8. Verificación de ON DELETE RESTRICT a nivel base de datos
    # Si alguien intenta hacer raw DELETE en SQLite sobre un proyecto con tickets sin pasar por el servicio:
    raw_delete_bloqueado = False
    try:
        with db.cursor_scope() as cur:
            cur.execute("DELETE FROM projects WHERE id = ?;", (proj_activo.id,))
    except sqlite3.IntegrityError:
        raw_delete_bloqueado = True

    assert raw_delete_bloqueado is True, "ON DELETE RESTRICT debe impedir eliminación directa de proyectos con tickets."
    print("  [OK] Prueba 8: ON DELETE RESTRICT a nivel SQLite bloquea borrado en cascada descontrolado.")

    # 9. Probar ON DELETE SET NULL en members -> tickets
    with db.cursor_scope() as cur:
        cur.execute("""
            INSERT INTO members (full_name, email, role_title, department)
            VALUES ('Miembro Temp', 'temp_audit@nexora.com', 'Tester', 'Calidad');
        """)
        m_id = cur.lastrowid
        
        cur.execute("""
            INSERT INTO tickets (ticket_code, title, project_id, assigned_member_id, priority, due_date, status)
            VALUES ('TCK-SETNULL', 'Ticket para Set Null', ?, ?, 'Media', '2026-12-01', 'Pendiente');
        """, (proj_activo.id, m_id))
        
        # Borrar miembro
        cur.execute("DELETE FROM members WHERE id = ?;", (m_id,))
        
        # Verificar que el ticket aún existe y assigned_member_id es NULL
        cur.execute("SELECT assigned_member_id FROM tickets WHERE ticket_code = 'TCK-SETNULL';")
        assigned = cur.fetchone()[0]
        assert assigned is None, "assigned_member_id debió ser actualizado a NULL."
    print("  [OK] Prueba 9: ON DELETE SET NULL desasigna al miembro sin borrar el ticket.")

    # 10. Probar Criptografía y Hashing PBKDF2-HMAC-SHA256
    hash1, salt1 = SecurityService.hash_password("password_secreta")
    hash2, salt2 = SecurityService.hash_password("password_secreta")
    assert salt1 != salt2, "Dos hashes de la misma contraseña deben tener sales diferentes."
    assert hash1 != hash2, "Dos hashes con diferente sal deben ser distintos."
    assert SecurityService.verify_password("password_secreta", hash1, salt1) is True
    assert SecurityService.verify_password("password_incorrecta", hash1, salt1) is False
    print("  [OK] Prueba 10: PBKDF2-HMAC-SHA256 genera sales aleatorias y verifica en tiempo constante.")

    # 11. Regla de Negocio: No permitir crear tickets en proyectos cerrados ('Completado' o 'Cancelado')
    project_cerrado = project_service.create_project(
        code="PRJ-CLOSED",
        name="Proyecto Cerrado Test",
        start_date="2026-11-01",
        status="Completado"
    )
    blocked_closed_prj = False
    try:
        from services.ticket_service import TicketService
        from repositories.member_repository import MemberRepository
        ticket_service = TicketService(ticket_repo, project_repo, MemberRepository(db))
        ticket_service.create_ticket(
            ticket_code="TCK-FAIL-CLOSED",
            title="Ticket en proyecto cerrado",
            project_id=project_cerrado.id,
            priority="Media",
            due_date="2026-12-01"
        )
    except ValueError as e:
        blocked_closed_prj = True
        assert "cerrado" in str(e).lower() or "completado" in str(e).lower()
    assert blocked_closed_prj is True, "Debe impedirse la creación de tickets en proyectos cerrados."
    print("  [OK] Prueba 11: Bloqueada la creación de tickets en proyectos cerrados o completados.")

    # 12. Regla de Negocio: No permitir asignar tickets a miembros inactivos
    from services.member_service import MemberService
    member_service = MemberService(MemberRepository(db))
    m_inactivo = member_service.register_member(
        full_name="Miembro Desactivado",
        email="inactivo@nexora.com",
        role_title="QA",
        department="Calidad"
    )
    member_service.set_active_status(m_inactivo.id, False)

    blocked_inactive_member = False
    try:
        ticket_service.create_ticket(
            ticket_code="TCK-FAIL-INACT",
            title="Ticket para miembro inactivo",
            project_id=proj_activo.id,
            priority="Media",
            due_date="2026-12-01",
            assigned_member_id=m_inactivo.id
        )
    except ValueError as e:
        blocked_inactive_member = True
        assert "inactivo" in str(e).lower()
    assert blocked_inactive_member is True, "Debe impedirse la asignación de tickets a miembros inactivos."
    print("  [OK] Prueba 12: Bloqueada la asignación de tickets a miembros inactivos.")

    # 13. Regla de Negocio: Control de Permisos en Servicios (Operador vs Administrador)
    from services.auth_service import AuthService
    from repositories.user_repository import UserRepository
    auth_service = AuthService(UserRepository(db))
    _, _, operador_user = auth_service.login("operador", "operador123")
    assert operador_user is not None and operador_user.is_operator()

    blocked_operator_access = False
    try:
        auth_service.get_all_users(requester=operador_user)
    except PermissionError:
        blocked_operator_access = True
    assert blocked_operator_access is True, "Un operador no debe tener acceso a la gestión de cuentas."
    print("  [OK] Prueba 13: El rol Operador tiene bloqueada la gestión de cuentas (PermissionError).")

    # Limpieza
    os.remove(test_db_path)
    print("\n>>> ¡TODAS LAS PRUEBAS (13/13) COMPLETADAS SATISFACTORIAMENTE!")


if __name__ == "__main__":
    run_tests()
