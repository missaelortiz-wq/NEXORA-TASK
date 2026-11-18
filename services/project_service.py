"""
Servicio de Gestión de Proyectos
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional, Tuple

from models.project import Project
from models.ticket import Ticket
from repositories.project_repository import ProjectRepository
from repositories.ticket_repository import TicketRepository


class ProjectService:
    """
    Gestiona las reglas de negocio para la administración de proyectos.
    Implementa controles de integridad de negocio como la prohibición de eliminar
    proyectos con tickets pendientes o en progreso.
    """

    def __init__(
        self,
        project_repo: Optional[ProjectRepository] = None,
        ticket_repo: Optional[TicketRepository] = None
    ):
        """Inicializa el servicio inyectando los repositorios de proyectos y tickets."""
        self.project_repo = project_repo or ProjectRepository()
        self.ticket_repo = ticket_repo or TicketRepository()

    def create_project(
        self,
        code: str,
        name: str,
        start_date: str,
        status: str = "Planificación",
        description: Optional[str] = None
    ) -> Project:
        """Valida y crea un nuevo proyecto con clave única."""
        code_clean = code.strip().upper()
        if not code_clean:
            raise ValueError("El código del proyecto es obligatorio.")
        if not name or not name.strip():
            raise ValueError("El nombre del proyecto es obligatorio.")
        if status not in Project.VALID_STATUSES:
            raise ValueError(f"Estado inválido. Opciones permitidas: {Project.VALID_STATUSES}")

        existing = self.project_repo.find_by_code(code_clean)
        if existing:
            raise ValueError(f"Ya existe un proyecto registrado con la clave '{code_clean}'.")

        project = Project(
            code=code_clean,
            name=name.strip(),
            start_date=start_date.strip(),
            status=status,
            description=description.strip() if description else None
        )
        self.project_repo.create(project)
        return project

    def get_all_projects(self, status: Optional[str] = None) -> List[Project]:
        """Obtiene la lista de proyectos, opcionalmente filtrada por estado."""
        return self.project_repo.find_all(status=status)

    def get_project_by_code(self, code: str) -> Optional[Project]:
        """Busca un proyecto por clave única."""
        return self.project_repo.find_by_code(code)

    def get_project_by_id(self, project_id: int) -> Optional[Project]:
        """Busca un proyecto por su ID."""
        return self.project_repo.find_by_id(project_id)

    def update_project_status(self, project_id: int, new_status: str) -> bool:
        """Actualiza el estado de avance de un proyecto."""
        if new_status not in Project.VALID_STATUSES:
            raise ValueError(f"Estado '{new_status}' no válido.")
        return self.project_repo.update_status(project_id, new_status)

    def update_project(
        self,
        project_id: int,
        code: str,
        name: str,
        start_date: str,
        status: str,
        description: Optional[str] = None
    ) -> Project:
        """
        Actualiza los datos de un proyecto validando clave única y formato de fecha.
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"No existe ningún proyecto con ID {project_id}.")

        code_clean = code.strip().upper()
        if not code_clean:
            raise ValueError("El código del proyecto es obligatorio.")
        if not name or not name.strip():
            raise ValueError("El nombre del proyecto es obligatorio.")
        if status not in Project.VALID_STATUSES:
            raise ValueError(f"Estado inválido. Opciones permitidas: {Project.VALID_STATUSES}")

        # Validar fecha
        try:
            from datetime import datetime
            datetime.strptime(start_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: '{start_date}'. Use AAAA-MM-DD.")

        # Si el código cambió, validar unicidad
        if code_clean != project.code:
            existing = self.project_repo.find_by_code(code_clean)
            if existing and existing.id != project_id:
                raise ValueError(f"Ya existe otro proyecto registrado con la clave '{code_clean}'.")

        project.code = code_clean
        project.name = name.strip()
        project.start_date = start_date.strip()
        project.status = status
        project.description = description.strip() if description else None

        self.project_repo.update(project)
        return project

    def get_active_tickets_for_project(self, project_id: int) -> List[Ticket]:
        """
        Retorna los tickets en estados activos ('Pendiente', 'En Progreso', 'En Revisión')
        vinculados al proyecto.
        """
        return self.ticket_repo.find_active_by_project(project_id)

    def can_delete_project(self, project_id: int) -> Tuple[bool, str, List[Ticket]]:
        """
        Evalúa si un proyecto es apto para ser eliminado según las reglas del negocio:
        - No debe tener tickets activos (pendientes, en progreso o en revisión).
        
        Returns:
            Tuple[bool, str, List[Ticket]]: (es_eliminable, motivo_o_mensaje, lista_tickets_activos)
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            return False, f"El proyecto con ID {project_id} no existe.", []

        active_tickets = self.get_active_tickets_for_project(project_id)
        if active_tickets:
            count = len(active_tickets)
            codes = ", ".join(t.ticket_code for t in active_tickets)
            return False, (
                f"No se puede eliminar el proyecto '{project.name}' ({project.code}): "
                f"posee {count} ticket(s) activo(s) en estado pendiente o en progreso ({codes}). "
                f"Debe concluirlos o reasignarlos antes de poder eliminar el proyecto."
            ), active_tickets

        return True, (
            f"El proyecto '{project.name}' no tiene tickets activos y puede eliminarse previa confirmación."
        ), []

    def delete_project(self, project_id: int, confirmed: bool = False) -> bool:
        """
        Elimina un proyecto del sistema bajo estricto cumplimiento de reglas de negocio:
        
        1. Comprueba si el proyecto existe en el repositorio.
        2. Comprueba si existen tickets pendientes o en progreso (activos).
           Si existen, emite una excepción clara y conserva el proyecto intacto.
        3. Si no existen tickets activos, exige el parámetro `confirmed=True` (confirmación
           explícita del usuario desde la interfaz gráfica).
        4. Si se confirma, elimina los tickets residuales (resueltos/cerrados) y el proyecto.
        
        Args:
            project_id: Identificador primario del proyecto.
            confirmed: Booleano que certifica la confirmación del usuario.
            
        Raises:
            ValueError: Si el proyecto no existe.
            ValueError: Si existen tickets pendientes o en progreso (regla de negocio).
            ValueError: Si no se proporciona confirmación explícita (confirmed=False).
            
        Returns:
            bool: True si la eliminación concluyó con éxito.
        """
        project = self.project_repo.find_by_id(project_id)
        if not project:
            raise ValueError(f"No existe ningún proyecto con ID {project_id}.")

        can_delete, reason, active_tickets = self.can_delete_project(project_id)
        if not can_delete:
            # Regla de negocio: El proyecto NO se elimina y se conserva intacto
            raise ValueError(reason)

        if not confirmed:
            raise ValueError(
                f"Confirmación requerida: Para eliminar el proyecto '{project.name}' ({project.code}), "
                f"debe confirmar la acción explícitamente desde la interfaz."
            )

        # En caso de contar con tickets históricos ya resueltos o cerrados,
        # se remueven de forma explícita para cumplir con ON DELETE RESTRICT a nivel BD
        self.ticket_repo.delete_by_project(project_id)

        # Proceder con la eliminación del proyecto
        return self.project_repo.delete(project_id)
