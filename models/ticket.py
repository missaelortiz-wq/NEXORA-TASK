"""
Modelo de Dominio: Ticket / Tarea (tickets)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


@dataclass
class Ticket:
    """
    Representa una tarea o incidencia vinculada a un proyecto (FK)
    y opcionalmente a un miembro responsable (FK), con prioridad,
    fecha límite y estado de resolución.
    """
    ticket_code: str
    title: str
    project_id: int
    priority: str
    due_date: str
    status: str
    id: Optional[int] = None
    description: Optional[str] = None
    assigned_member_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # Campos complementarios útiles en consultas JOIN para la UI
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    member_name: Optional[str] = None
    member_email: Optional[str] = None

    VALID_PRIORITIES = ('Baja', 'Media', 'Alta', 'Crítica')
    VALID_STATUSES = ('Pendiente', 'En Progreso', 'En Revisión', 'Resuelto', 'Cancelado', 'Cerrado')
    ACTIVE_STATUSES = ('Pendiente', 'En Progreso', 'En Revisión')

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Ticket":
        """Instancia un objeto Ticket a partir de una fila obtenida de SQLite."""
        keys = row.keys()
        return cls(
            id=row["id"],
            ticket_code=row["ticket_code"],
            title=row["title"],
            description=row["description"] if "description" in keys else None,
            project_id=row["project_id"],
            assigned_member_id=row["assigned_member_id"] if "assigned_member_id" in keys else None,
            priority=row["priority"],
            due_date=row["due_date"],
            status=row["status"],
            created_at=row["created_at"] if "created_at" in keys else None,
            updated_at=row["updated_at"] if "updated_at" in keys else None,
            project_code=row["project_code"] if "project_code" in keys else None,
            project_name=row["project_name"] if "project_name" in keys else None,
            member_name=row["member_name"] if "member_name" in keys else None,
            member_email=row["member_email"] if "member_email" in keys else None
        )

    def to_dict(self) -> dict[str, Any]:
        """Convierte la entidad en un diccionario serializable."""
        return {
            "id": self.id,
            "ticket_code": self.ticket_code,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "assigned_member_id": self.assigned_member_id,
            "priority": self.priority,
            "due_date": self.due_date,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "member_name": self.member_name,
            "member_email": self.member_email
        }
