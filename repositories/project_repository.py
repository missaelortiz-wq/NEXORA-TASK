"""
Repositorio de Proyectos (projects)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional

from models.project import Project
from repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository):
    """
    Repositorio para gestionar las operaciones de persistencia sobre proyectos.
    """

    def find_by_id(self, project_id: int) -> Optional[Project]:
        """Recupera un proyecto por su identificador primario."""
        sql = "SELECT * FROM projects WHERE id = ?;"
        row = self._execute_query_one(sql, (project_id,))
        return Project.from_row(row) if row else None

    def find_by_code(self, code: str) -> Optional[Project]:
        """Recupera un proyecto por su código o clave única (ej. NEX-CORE)."""
        sql = "SELECT * FROM projects WHERE code = ?;"
        row = self._execute_query_one(sql, (code.strip().upper(),))
        return Project.from_row(row) if row else None

    def find_all(self, status: Optional[str] = None) -> List[Project]:
        """
        Retorna todos los proyectos registrados, con filtro opcional por estado.
        """
        if status:
            sql = "SELECT * FROM projects WHERE status = ? ORDER BY start_date DESC;"
            rows = self._execute_query_all(sql, (status,))
        else:
            sql = "SELECT * FROM projects ORDER BY start_date DESC;"
            rows = self._execute_query_all(sql)
        return [Project.from_row(r) for r in rows]

    def create(self, project: Project) -> int:
        """Inserta un nuevo proyecto y retorna su ID."""
        sql = """
            INSERT INTO projects (code, name, description, start_date, status)
            VALUES (?, ?, ?, ?, ?);
        """
        params = (
            project.code.strip().upper(),
            project.name.strip(),
            project.description.strip() if project.description else None,
            project.start_date.strip(),
            project.status.strip()
        )
        new_id = self._execute_insert(sql, params)
        project.id = new_id
        return new_id

    def update(self, project: Project) -> bool:
        """Actualiza los datos de un proyecto."""
        if project.id is None:
            raise ValueError("El proyecto debe contar con un ID para ser actualizado.")
        sql = """
            UPDATE projects
            SET code = ?, name = ?, description = ?, start_date = ?, status = ?
            WHERE id = ?;
        """
        params = (
            project.code.strip().upper(),
            project.name.strip(),
            project.description.strip() if project.description else None,
            project.start_date.strip(),
            project.status.strip(),
            project.id
        )
        return self._execute_non_query(sql, params) > 0

    def update_status(self, project_id: int, new_status: str) -> bool:
        """Modifica el estado de un proyecto."""
        sql = "UPDATE projects SET status = ? WHERE id = ?;"
        return self._execute_non_query(sql, (new_status.strip(), project_id)) > 0

    def delete(self, project_id: int) -> bool:
        """
        Elimina un proyecto del sistema.
        Nota: Gracias a ON DELETE CASCADE, los tickets asociados se eliminan en cascada.
        """
        sql = "DELETE FROM projects WHERE id = ?;"
        return self._execute_non_query(sql, (project_id,)) > 0
