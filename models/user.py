"""
Modelo de Dominio: Usuario del Sistema (users_system)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class User:
    """
    Representa una cuenta de acceso al software.
    Gestiona roles ('Administrador' u 'Operador') y seguridad con contraseñas hasheadas.
    """
    username: str
    password_hash: str
    salt: str
    full_name: str
    role: str
    id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[str] = None

    def is_admin(self) -> bool:
        """Verifica si el usuario cuenta con privilegios administrativos."""
        return self.role.strip().lower() == "administrador"

    def is_operator(self) -> bool:
        """Verifica si el usuario cuenta con rol de operador técnico."""
        return self.role.strip().lower() == "operador"

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "User":
        """Instancia un objeto User a partir de una fila obtenida de SQLite (sqlite3.Row)."""
        return cls(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la entidad a un diccionario (omitiendo contraseñas sensibles si fuera necesario)."""
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
