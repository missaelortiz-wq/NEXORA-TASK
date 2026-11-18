"""
Módulo de Gestión de Base de Datos SQLite (SQLite3)
NEXORA TASKS - Tópicos Avanzados de Programación

Gestiona la conexión a SQLite, activación obligatoria de claves foráneas (PRAGMA foreign_keys = ON),
creación automática del esquema relacional y carga de datos iniciales (Seed Data).
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional



class DatabaseManager:
    """
    Gestor centralizado de la base de datos relacional SQLite.
    Aplica el patrón Context Manager para garantizar la apertura y cierre
    seguro de conexiones, confirmación de transacciones (COMMIT) y reversión (ROLLBACK).
    """

    DEFAULT_DB_NAME = "nexora_tasks.db"

    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el gestor de base de datos.
        
        Args:
            db_path: Ruta del archivo SQLite. Si no se especifica, se ubica en la raíz del proyecto.
        """
        if db_path is None:
            # Ubica el archivo .db en el directorio raíz del proyecto
            project_root = Path(__file__).resolve().parent.parent
            self.db_path = str(project_root / self.DEFAULT_DB_NAME)
        else:
            self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Crea y retorna una nueva conexión SQLite configurada.
        Activa claves foráneas y habilita row_factory para acceder a columnas por nombre.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # IMPORTANTE: En SQLite las claves foráneas están deshabilitadas por defecto.
        # Debe ejecutarse este PRAGMA en cada conexión establecida.
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    @contextmanager
    def connection_scope(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager que gestiona transacciones completas.
        Realiza commit si la operación concluye con éxito, o rollback si surge un error.
        """
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def cursor_scope(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager conveniente para obtener directamente un cursor con transacción."""
        with self.connection_scope() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def check_foreign_keys_enabled(self) -> bool:
        """Verifica que el soporte para claves foráneas esté efectivamente activo en el motor."""
        with self.connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys;")
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def create_tables(self) -> None:
        """
        Crea las tablas del sistema relacional si aún no existen.
        Tablas: users_system, members, projects, tickets e índices de optimización.
        """
        ddl_statements = [
            # 1. Tabla de Usuarios del Sistema (Cuentas de Acceso, Hashes y Roles)
            """
            CREATE TABLE IF NOT EXISTS users_system (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('Administrador', 'Operador')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
            """,

            # 2. Tabla de Integrantes del Equipo (Responsables de Tickets)
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role_title TEXT NOT NULL,
                department TEXT NOT NULL,
                phone TEXT,
                is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
            """,

            # 3. Tabla de Proyectos (Clave única, Fechas y Estados)
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                start_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Planificación', 'En Progreso', 'Pausado', 'Completado', 'Cancelado')),
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
            """,

            # 4. Tabla de Tickets / Tareas (Relacionada con Projects y Members mediante FK)
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                project_id INTEGER NOT NULL,
                assigned_member_id INTEGER,
                priority TEXT NOT NULL CHECK (priority IN ('Baja', 'Media', 'Alta', 'Crítica')),
                due_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Pendiente', 'En Progreso', 'En Revisión', 'Resuelto', 'Cancelado', 'Cerrado')),
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE RESTRICT,
                FOREIGN KEY (assigned_member_id) REFERENCES members(id) ON DELETE SET NULL
            );
            """,

            # Índices para mejorar rendimiento de búsquedas y uniones (JOINs)
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users_system(username);",
            "CREATE INDEX IF NOT EXISTS idx_members_email ON members(email);",
            "CREATE INDEX IF NOT EXISTS idx_projects_code ON projects(code);",
            "CREATE INDEX IF NOT EXISTS idx_tickets_project ON tickets(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets(assigned_member_id);",
            "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);"
        ]

        with self.connection_scope() as conn:
            cursor = conn.cursor()
            for statement in ddl_statements:
                cursor.execute(statement)

    def seed_initial_data(self) -> dict[str, int]:
        """
        Puebla la base de datos con los registros iniciales de prueba si se encuentra vacía.
        Garantiza que todas las contraseñas se almacenen cifradas mediante hash PBKDF2 y sal.
        
        Returns:
            dict[str, int]: Cantidad de registros insertados por entidad.
        """
        from services.security import SecurityService

        counts = {"users": 0, "members": 0, "projects": 0, "tickets": 0}

        with self.connection_scope() as conn:
            cursor = conn.cursor()

            # 1. Sembrado de Usuarios (Solo si la tabla users_system no tiene registros)
            cursor.execute("SELECT COUNT(*) FROM users_system;")
            if cursor.fetchone()[0] == 0:
                # Generar hashes y sales criptográficas para los usuarios
                admin_hash, admin_salt = SecurityService.hash_password("admin123")
                operador_hash, operador_salt = SecurityService.hash_password("operador123")

                users_to_insert = [
                    (
                        "admin",
                        admin_hash,
                        admin_salt,
                        "Administrador General del Sistema",
                        "Administrador",
                        1
                    ),
                    (
                        "operador",
                        operador_hash,
                        operador_salt,
                        "Operador de Mesa de Control",
                        "Operador",
                        1
                    )
                ]

                cursor.executemany(
                    """
                    INSERT INTO users_system (username, password_hash, salt, full_name, role, is_active)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    users_to_insert
                )
                counts["users"] = len(users_to_insert)

            # 2. Sembrado de Miembros (Mínimo 8 miembros)
            cursor.execute("SELECT COUNT(*) FROM members;")
            if cursor.fetchone()[0] == 0:
                members_to_insert = [
                    ("Carlos Mendoza", "carlos.mendoza@nexora.com", "Líder Técnico de Software", "Ingeniería", "+52 55 1122 3344"),
                    ("Sofía Morales", "sofia.morales@nexora.com", "Diseñadora UI/UX", "Diseño de Producto", "+52 55 2233 4455"),
                    ("Alejandro Cruz", "alejandro.cruz@nexora.com", "Desarrollador Backend Senior", "Ingeniería", "+52 55 3344 5566"),
                    ("Valeria Ríos", "valeria.rios@nexora.com", "Desarrolladora Frontend", "Ingeniería", "+52 55 4455 6677"),
                    ("Diego Herrera", "diego.herrera@nexora.com", "Especialista QA & Automatización", "Aseguramiento de Calidad", "+52 55 5566 7788"),
                    ("Mariana Sánchez", "mariana.sanchez@nexora.com", "Ingeniera DevOps & Cloud", "Infraestructura", "+52 55 6677 8899"),
                    ("Fernando Gutiérrez", "fernando.gutierrez@nexora.com", "Administrador de Base de Datos (DBA)", "Gestión de Datos", "+52 55 7788 9900"),
                    ("Andrea López", "andrea.lopez@nexora.com", "Product Owner & Agile Coach", "Gestión de Proyectos", "+52 55 8899 0011")
                ]

                cursor.executemany(
                    """
                    INSERT INTO members (full_name, email, role_title, department, phone, is_active)
                    VALUES (?, ?, ?, ?, ?, 1);
                    """,
                    members_to_insert
                )
                counts["members"] = len(members_to_insert)

            # 3. Sembrado de Proyectos (Mínimo 5 proyectos con clave única y estados diversos)
            cursor.execute("SELECT COUNT(*) FROM projects;")
            if cursor.fetchone()[0] == 0:
                projects_to_insert = [
                    (
                        "NEX-CORE",
                        "NEXORA Tasks - Core System",
                        "Desarrollo de la arquitectura base, motor de persistencia y modelos relacionales.",
                        "2026-10-01",
                        "En Progreso"
                    ),
                    (
                        "NEX-AUTH",
                        "Módulo de Seguridad y Criptografía",
                        "Autenticación basada en PBKDF2-SHA256, roles de acceso y auditoría de sesiones.",
                        "2026-10-15",
                        "En Progreso"
                    ),
                    (
                        "NEX-DESK",
                        "Interfaz Gráfica de Escritorio Tkinter",
                        "Construcción de vistas en Tkinter y ttk con navegación orientada a componentes.",
                        "2026-11-01",
                        "Planificación"
                    ),
                    (
                        "NEX-REPORT",
                        "Módulo de Reportería y Métricas",
                        "Generación de reportes de desempeño, métricas por responsable y exportación.",
                        "2026-09-01",
                        "Pausado"
                    ),
                    (
                        "NEX-API",
                        "Servicios Web e Integración Externa",
                        "Capa de interoperabilidad para sincronización de tickets con servicios en la nube.",
                        "2026-08-15",
                        "Completado"
                    )
                ]

                cursor.executemany(
                    """
                    INSERT INTO projects (code, name, description, start_date, status)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    projects_to_insert
                )
                counts["projects"] = len(projects_to_insert)

            # 4. Sembrado de Tickets (Mínimo 3 tickets con estados y prioridades diferentes)
            cursor.execute("SELECT COUNT(*) FROM tickets;")
            if cursor.fetchone()[0] == 0:
                # Obtenemos los IDs reales de proyectos y miembros insertados para mantener integridad referencial
                cursor.execute("SELECT id, code FROM projects;")
                proj_map = {row["code"]: row["id"] for row in cursor.fetchall()}

                cursor.execute("SELECT id, email FROM members;")
                member_map = {row["email"]: row["id"] for row in cursor.fetchall()}

                tickets_to_insert = [
                    (
                        "TCK-001",
                        "Modelado del esquema relacional y llaves foráneas en SQLite",
                        "Definir el DDL con restricciones de integridad referencial, ON DELETE CASCADE y CHECKs.",
                        proj_map.get("NEX-CORE", 1),
                        member_map.get("fernando.gutierrez@nexora.com", 7),
                        "Alta",
                        "2026-11-20",
                        "Resuelto"
                    ),
                    (
                        "TCK-002",
                        "Implementación de hashing PBKDF2 y verificación con sal",
                        "Desarrollar el servicio criptográfico para evitar almacenamiento de contraseñas en texto plano.",
                        proj_map.get("NEX-AUTH", 2),
                        member_map.get("alejandro.cruz@nexora.com", 3),
                        "Crítica",
                        "2026-11-25",
                        "En Progreso"
                    ),
                    (
                        "TCK-003",
                        "Diseño de prototipos de interfaz en Figma para el gestor de tickets",
                        "Definir layout para formulario de tickets, tablas paginadas y selector de estados.",
                        proj_map.get("NEX-DESK", 3),
                        member_map.get("sofia.morales@nexora.com", 2),
                        "Media",
                        "2026-11-30",
                        "Pendiente"
                    ),
                    (
                        "TCK-004",
                        "Pruebas de estrés y validación de reglas de negocio en repositorios",
                        "Elaborar casos de prueba para inserción, consulta y actualización de entidades.",
                        proj_map.get("NEX-CORE", 1),
                        member_map.get("diego.herrera@nexora.com", 5),
                        "Media",
                        "2026-12-05",
                        "En Revisión"
                    )
                ]

                cursor.executemany(
                    """
                    INSERT INTO tickets (ticket_code, title, description, project_id, assigned_member_id, priority, due_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    tickets_to_insert
                )
                counts["tickets"] = len(tickets_to_insert)

        return counts

    def initialize_database(self) -> dict[str, int]:
        """
        Punto de entrada principal para inicializar la base de datos completa:
        Crea las tablas si no existen y puebla los datos iniciales de prueba.
        
        Returns:
            dict[str, int]: Resumen de registros sembrados.
        """
        self.create_tables()
        return self.seed_initial_data()


# Instancia singleton predeterminada para uso en repositorios y servicios
default_db_manager = DatabaseManager()
