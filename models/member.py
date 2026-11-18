"""
Modelo de Dominio: Miembro del Equipo (members)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class Member:
    """
    Representa a un integrante del equipo técnico u operativo
    susceptible de ser asignado como responsable de tickets y tareas.
    """
    full_name: str
    email: str
    role_title: str
    department: str
    id: Optional[int] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Member":
        """Instancia un objeto Member a partir de una fila obtenida de SQLite."""
        return cls(
            id=row["id"],
            full_name=row["full_name"],
            email=row["email"],
            role_title=row["role_title"],
            department=row["department"],
            phone=row["phone"] if "phone" in row.keys() else None,
            is_active=bool(row["is_active"]),
            created_at=row["created_at"]
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la entidad en un diccionario serializable."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role_title": self.role_title,
            "department": self.department,
            "phone": self.phone,
            "is_active": self.is_active,
            "created_at": self.created_at
        }
