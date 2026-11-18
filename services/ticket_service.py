"""
Servicio de Gestión de Tickets y Tareas
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from models.ticket import Ticket
from repositories.ticket_repository import TicketRepository
from repositories.project_repository import ProjectRepository
from repositories.member_repository import MemberRepository


class TicketService:
    """
    Gestiona la lógica de negocio para la asignación, ciclo de vida
    y seguimiento de tickets y tareas técnicas.
    """

    def __init__(
        self,
        ticket_repo: Optional[TicketRepository] = None,
        project_repo: Optional[ProjectRepository] = None,
        member_repo: Optional[MemberRepository] = None
    ):
        """Inyecta los repositorios necesarios para coordinar operaciones entre entidades."""
        self.ticket_repo = ticket_repo or TicketRepository()
        self.project_repo = project_repo or ProjectRepository()
        self.member_repo = member_repo or MemberRepository()

    @staticmethod
    def validate_date_format(date_str: str) -> str:
        """Valida que la fecha tenga el formato ISO AAAA-MM-DD y sea un día de calendario real."""
        date_clean = date_str.strip()
        try:
            datetime.strptime(date_clean, "%Y-%m-%d")
            return date_clean
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: '{date_str}'. Se requiere AAAA-MM-DD (ej. 2026-12-31).")

    def create_ticket(
        self,
        ticket_code: str,
        title: str,
        project_id: int,
        priority: str,
        due_date: str,
        status: str = "Pendiente",
        description: Optional[str] = None,
        assigned_member_id: Optional[int] = None
    ) -> Ticket:
        """
        Valida reglas de negocio y crea un nuevo ticket.
        Reglas:
        - No permitir crear tickets en proyectos cerrados ('Completado' o 'Cancelado').
        - No permitir asignar tickets a miembros inactivos.
        - Validar fecha y unicidad de clave.
        """
        code_clean = ticket_code.strip().upper()
        if not code_clean:
            raise ValueError("El código del ticket es obligatorio.")
        if not title or not title.strip():
            raise ValueError("El título del ticket es obligatorio.")
        if priority not in Ticket.VALID_PRIORITIES:
            raise ValueError(f"Prioridad inválida. Debe ser una de: {Ticket.VALID_PRIORITIES}")
        if status not in Ticket.VALID_STATUSES:
            raise ValueError(f"Estado inválido. Debe ser uno de: {Ticket.VALID_STATUSES}")

        due_date_clean = self.validate_date_format(due_date)

        # Regla: Validar existencia del proyecto y que NO esté cerrado/cancelado
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"El proyecto con ID {project_id} no existe.")
        if project.status in ("Completado", "Cancelado"):
            raise ValueError(
                f"No se permite crear tickets en el proyecto '{project.name}' "
                f"porque se encuentra en estado '{project.status}'."
            )

        # Regla: Validar existencia y actividad del miembro asignado
        if assigned_member_id is not None:
            member = self.member_repo.find_by_id(assigned_member_id)
            if not member:
                raise ValueError(f"El miembro con ID {assigned_member_id} no existe.")
            if not member.is_active:
                raise ValueError(
                    f"No se puede asignar tickets al integrante '{member.full_name}' "
                    f"porque se encuentra inactivo."
                )

        existing = self.ticket_repo.find_by_code(code_clean)
        if existing:
            raise ValueError(f"Ya existe un ticket con el código '{code_clean}'.")

        ticket = Ticket(
            ticket_code=code_clean,
            title=title.strip(),
            description=description.strip() if description else None,
            project_id=project_id,
            assigned_member_id=assigned_member_id,
            priority=priority,
            due_date=due_date_clean,
            status=status
        )
        self.ticket_repo.create(ticket)
        return ticket

    def update_ticket(
        self,
        ticket_id: int,
        ticket_code: str,
        title: str,
        project_id: int,
        priority: str,
        due_date: str,
        status: str,
        description: Optional[str] = None,
        assigned_member_id: Optional[int] = None
    ) -> Ticket:
        """
        Actualiza los datos de un ticket existente validando reglas de negocio.
        """
        ticket = self.ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"No existe ningún ticket con ID {ticket_id}.")

        code_clean = ticket_code.strip().upper()
        if not code_clean:
            raise ValueError("El código del ticket es obligatorio.")
        if not title or not title.strip():
            raise ValueError("El título del ticket es obligatorio.")
        if priority not in Ticket.VALID_PRIORITIES:
            raise ValueError(f"Prioridad inválida. Debe ser: {Ticket.VALID_PRIORITIES}")
        if status not in Ticket.VALID_STATUSES:
            raise ValueError(f"Estado inválido. Debe ser: {Ticket.VALID_STATUSES}")

        due_date_clean = self.validate_date_format(due_date)

        # Validar proyecto
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"El proyecto con ID {project_id} no existe.")

        # Si el código cambió, validar que no choque con otro ticket
        if code_clean != ticket.ticket_code:
            existing = self.ticket_repo.find_by_code(code_clean)
            if existing and existing.id != ticket_id:
                raise ValueError(f"Ya existe otro ticket registrado con el código '{code_clean}'.")

        # Validar responsable activo si fue asignado
        if assigned_member_id is not None:
            member = self.member_repo.find_by_id(assigned_member_id)
            if not member:
                raise ValueError(f"El miembro con ID {assigned_member_id} no existe.")
            if not member.is_active:
                raise ValueError(
                    f"No se puede asignar tickets al integrante '{member.full_name}' "
                    f"porque se encuentra inactivo."
                )

        ticket.ticket_code = code_clean
        ticket.title = title.strip()
        ticket.project_id = project_id
        ticket.priority = priority
        ticket.due_date = due_date_clean
        ticket.status = status
        ticket.description = description.strip() if description else None
        ticket.assigned_member_id = assigned_member_id

        self.ticket_repo.update(ticket)
        return ticket

    def delete_ticket(self, ticket_id: int) -> bool:
        """Elimina un ticket del sistema."""
        ticket = self.ticket_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"El ticket con ID {ticket_id} no existe.")
        return self.ticket_repo.delete(ticket_id)

    def get_all_tickets(
        self,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        member_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[Ticket]:
        """Recupera la lista de tickets aplicando filtros dinámicos."""
        return self.ticket_repo.find_all(
            status=status,
            project_id=project_id,
            assigned_member_id=member_id,
            priority=priority
        )

    def get_ticket_by_code(self, ticket_code: str) -> Optional[Ticket]:
        """Busca un ticket por su código."""
        return self.ticket_repo.find_by_code(ticket_code)

    def get_ticket_by_id(self, ticket_id: int) -> Optional[Ticket]:
        """Busca un ticket por su identificador primario."""
        return self.ticket_repo.find_by_id(ticket_id)

    def change_ticket_status(self, ticket_id: int, new_status: str) -> bool:
        """Transiciona el estado de un ticket."""
        if new_status not in Ticket.VALID_STATUSES:
            raise ValueError(f"Estado inválido '{new_status}'.")
        return self.ticket_repo.update_status(ticket_id, new_status)

    def get_overdue_tickets(
        self,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Ticket]:
        """
        Retorna la lista de tickets cuya fecha límite ya venció y
        que aún no han sido resueltos ni cancelados.
        """
        return self.ticket_repo.find_overdue(priority=priority, status=status)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Calcula métricas clave para el panel de control o reportes."""
        all_tickets = self.ticket_repo.find_all()
        overdue_tickets = self.ticket_repo.find_overdue()
        total = len(all_tickets)

        by_status: Dict[str, int] = {
            "Pendiente": 0,
            "En Progreso": 0,
            "En Revisión": 0,
            "Resuelto": 0,
            "Cancelado": 0,
            "Cerrado": 0
        }
        by_priority: Dict[str, int] = {
            "Baja": 0,
            "Media": 0,
            "Alta": 0,
            "Crítica": 0
        }

        for t in all_tickets:
            by_status[t.status] = by_status.get(t.status, 0) + 1
            by_priority[t.priority] = by_priority.get(t.priority, 0) + 1

        return {
            "total_tickets": total,
            "overdue_count": len(overdue_tickets),
            "by_status": by_status,
            "by_priority": by_priority,
            "pending_count": by_status.get("Pendiente", 0),
            "in_progress_count": by_status.get("En Progreso", 0),
            "resolved_count": by_status.get("Resuelto", 0)
        }
