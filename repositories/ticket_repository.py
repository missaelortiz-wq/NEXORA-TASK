
"""
Repositorio de Tickets / Tareas (tickets)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional

from models.ticket import Ticket
from repositories.base_repository import BaseRepository


class TicketRepository(BaseRepository):
    """
    Repositorio de persistencia para tickets y tareas.
    Incluye consultas relacionales con JOIN sobre projects y members.
    """

    BASE_JOIN_SELECT = """
        SELECT
            t.*,
            p.name AS project_name,
            m.full_name AS assigned_member_name
        FROM tickets t
        INNER JOIN projects p ON p.id = t.project_id
        LEFT JOIN members m ON m.id = t.assigned_member_id
    """

    def find_by_id(self, ticket_id: int) -> Optional[Ticket]:
        query = self.BASE_JOIN_SELECT + " WHERE t.id = ?"
        row = self._execute_query_one(query, (ticket_id,))
        return Ticket.from_row(row) if row else None

    def find_by_code(self, ticket_code: str) -> Optional[Ticket]:
        query = self.BASE_JOIN_SELECT + " WHERE t.ticket_code = ?"
        row = self._execute_query_one(query, (ticket_code,))
        return Ticket.from_row(row) if row else None

    def find_all(
        self,
        status: Optional[str] = None,
        project_id: Optional[int] = None,
        assigned_member_id: Optional[int] = None,
        priority: Optional[str] = None
    ) -> List[Ticket]:

        query = self.BASE_JOIN_SELECT
        conditions = []
        params = []

        if status:
            conditions.append("t.status = ?")
            params.append(status)

        if project_id is not None:
            conditions.append("t.project_id = ?")
            params.append(project_id)

        if assigned_member_id is not None:
            conditions.append("t.assigned_member_id = ?")
            params.append(assigned_member_id)

        if priority:
            conditions.append("t.priority = ?")
            params.append(priority)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY t.created_at DESC"

        rows = self._execute_query_all(query, tuple(params))
        return [Ticket.from_row(row) for row in rows]

    def create(self, ticket: Ticket) -> int:
        query = """
            INSERT INTO tickets (
                ticket_code,
                title,
                description,
                project_id,
                assigned_member_id,
                priority,
                due_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            ticket.ticket_code,
            ticket.title,
            ticket.description,
            ticket.project_id,
            ticket.assigned_member_id,
            ticket.priority,
            ticket.due_date,
            ticket.status
        )

        ticket.id = self._execute_insert(query, params)
        return ticket.id

    def update(self, ticket: Ticket) -> bool:
        query = """
            UPDATE tickets
            SET
                ticket_code = ?,
                title = ?,
                description = ?,
                project_id = ?,
                assigned_member_id = ?,
                priority = ?,
                due_date = ?,
                status = ?,
                updated_at = datetime('now', 'localtime')
            WHERE id = ?
        """

        params = (
            ticket.ticket_code,
            ticket.title,
            ticket.description,
            ticket.project_id,
            ticket.assigned_member_id,
            ticket.priority,
            ticket.due_date,
            ticket.status,
            ticket.id
        )

        return self._execute_non_query(query, params) > 0

    def update_status(self, ticket_id: int, new_status: str) -> bool:
        query = """
            UPDATE tickets
            SET status = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
        """
        return self._execute_non_query(
            query, (new_status, ticket_id)
        ) > 0

    def delete(self, ticket_id: int) -> bool:
        return self._execute_non_query(
            "DELETE FROM tickets WHERE id = ?",
            (ticket_id,)
        ) > 0

    def count_active_by_project(self, project_id: int) -> int:
        query = """
            SELECT COUNT(*) AS total
            FROM tickets
            WHERE project_id = ?
              AND status IN ('Pendiente', 'En Progreso', 'En Revisión')
        """
        row = self._execute_query_one(query, (project_id,))
        return row["total"] if row else 0

    def find_by_project(self, project_id: int) -> List[Ticket]:
        return self.find_all(project_id=project_id)

    def find_active_by_project(self, project_id: int) -> List[Ticket]:
        query = self.BASE_JOIN_SELECT + """
            WHERE t.project_id = ?
              AND t.status IN ('Pendiente', 'En Progreso', 'En Revisión')
            ORDER BY t.due_date ASC
        """
        rows = self._execute_query_all(query, (project_id,))
        return [Ticket.from_row(row) for row in rows]

    def delete_by_project(self, project_id: int) -> int:
        return self._execute_non_query(
            "DELETE FROM tickets WHERE project_id = ?",
            (project_id,)
        )

    def find_overdue(
        self,
        priority: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Ticket]:

        query = self.BASE_JOIN_SELECT + """
            WHERE date(t.due_date) < date('now', 'localtime')
              AND t.status NOT IN ('Resuelto', 'Cancelado', 'Cerrado')
        """

        params = []

        if priority:
            query += " AND t.priority = ?"
            params.append(priority)

        if status:
            query += " AND t.status = ?"
            params.append(status)

        query += " ORDER BY t.due_date ASC"

        rows = self._execute_query_all(query, tuple(params))
        return [Ticket.from_row(row) for row in rows]
