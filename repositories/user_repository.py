"""
Repositorio de Usuarios (users_system)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional

from models.user import User
from repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """
    Repositorio de persistencia para la entidad User.
    Gestiona la recuperación y almacenamiento seguro de cuentas de acceso.
    """

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca un usuario por su identificador primario."""
        sql = "SELECT * FROM users_system WHERE id = ?;"
        row = self._execute_query_one(sql, (user_id,))
        return User.from_row(row) if row else None

    def find_by_username(self, username: str) -> Optional[User]:
        """Busca un usuario por su nombre de usuario único."""
        sql = "SELECT * FROM users_system WHERE username = ?;"
        row = self._execute_query_one(sql, (username.strip(),))
        return User.from_row(row) if row else None

    def find_all(self, active_only: bool = False) -> List[User]:
        """Obtiene la lista de todos los usuarios registrados."""
        if active_only:
            sql = "SELECT * FROM users_system WHERE is_active = 1 ORDER BY username ASC;"
        else:
            sql = "SELECT * FROM users_system ORDER BY username ASC;"
        rows = self._execute_query_all(sql)
        return [User.from_row(r) for r in rows]

    def create(self, user: User) -> int:
        """
        Inserta un nuevo usuario en la base de datos con contraseña ya hasheada.
        Retorna el ID asignado.
        """
        sql = """
            INSERT INTO users_system (username, password_hash, salt, full_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (
            user.username.strip(),
            user.password_hash,
            user.salt,
            user.full_name.strip(),
            user.role.strip(),
            1 if user.is_active else 0
        )
        new_id = self._execute_insert(sql, params)
        user.id = new_id
        return new_id

    def update_password(self, user_id: int, new_hash: str, new_salt: str) -> bool:
        """Actualiza el hash y la sal de contraseña para un usuario específico."""
        sql = "UPDATE users_system SET password_hash = ?, salt = ? WHERE id = ?;"
        affected = self._execute_non_query(sql, (new_hash, new_salt, user_id))
        return affected > 0

    def set_active_status(self, user_id: int, is_active: bool) -> bool:
        """Habilita o deshabilita la cuenta de un usuario."""
        sql = "UPDATE users_system SET is_active = ? WHERE id = ?;"
        affected = self._execute_non_query(sql, (1 if is_active else 0, user_id))
        return affected > 0
