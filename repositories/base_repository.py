"""
Módulo Base de Repositorios (Patrón Repository)
NEXORA TASKS - Tópicos Avanzados de Programación

Proporciona la clase abstracta o base con métodos reutilizables para la ejecución
de consultas y comandos contra la base de datos SQLite.
"""

from typing import Any, List, Optional
import sqlite3

from database.database import DatabaseManager, default_db_manager


class BaseRepository:
    """
    Clase base para todos los repositorios del sistema.
    Encapsula el acceso a DatabaseManager y estandariza la interacción con SQLite.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Inicializa el repositorio.
        
        Args:
            db_manager: Instancia de DatabaseManager. Si es None, utiliza default_db_manager.
        """
        self.db = db_manager or default_db_manager

    def _execute_query_one(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Ejecuta una consulta SELECT y retorna una única fila o None."""
        with self.db.connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()

    def _execute_query_all(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Ejecuta una consulta SELECT y retorna una lista de filas (sqlite3.Row)."""
        with self.db.connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()

    def _execute_non_query(self, sql: str, params: tuple = ()) -> int:
        """
        Ejecuta un comando DML (INSERT, UPDATE, DELETE).
        Retorna la cantidad de filas afectadas o el último ID insertado si aplica.
        """
        with self.db.connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.rowcount

    def _execute_insert(self, sql: str, params: tuple = ()) -> int:
        """Ejecuta un INSERT y retorna el ID generado automáticamente (lastrowid)."""
        with self.db.connection_scope() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.lastrowid or 0
