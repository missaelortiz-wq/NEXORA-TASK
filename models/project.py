"""
Modelo de Dominio: Proyecto (projects)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class Project:
    """
    Representa un proyecto del sistema con clave única identificadora,
    nombre descriptivo, fecha de inicio y estado del ciclo de vida.
    """
    code: str
    name: str
    start_date: str
    status: str
    id: Optional[int] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

    # Estados permitidos según restricción de integridad de la base de datos
    VALID_STATUSES = ('Planificación', 'En Progreso', 'Pausado', 'Completado', 'Cancelado')

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Project":
        """Instancia un objeto Project a partir de una fila obtenida de SQLite."""
        return cls(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            description=row["description"] if "description" in row.keys() else None,
            start_date=row["start_date"],
            status=row["status"],
            created_at=row["created_at"]
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la entidad en un diccionario serializable."""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "status": self.status,
            "created_at": self.created_at
        }
