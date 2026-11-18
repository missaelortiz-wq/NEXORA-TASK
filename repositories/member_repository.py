"""
Repositorio de Miembros (members)
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional

from models.member import Member
from repositories.base_repository import BaseRepository


class MemberRepository(BaseRepository):
    """
    Repositorio para gestionar las operaciones de persistencia sobre integrantes del equipo.
    """

    def find_by_id(self, member_id: int) -> Optional[Member]:
        """Recupera un miembro por su identificador primario."""
        sql = "SELECT * FROM members WHERE id = ?;"
        row = self._execute_query_one(sql, (member_id,))
        return Member.from_row(row) if row else None

    def find_by_email(self, email: str) -> Optional[Member]:
        """Recupera un miembro por su correo electrónico único."""
        sql = "SELECT * FROM members WHERE email = ?;"
        row = self._execute_query_one(sql, (email.strip().lower(),))
        return Member.from_row(row) if row else None

    def find_all(self, active_only: bool = False) -> List[Member]:
        """
        Retorna la lista de miembros, con opción de filtrar solo los activos.
        """
        if active_only:
            sql = "SELECT * FROM members WHERE is_active = 1 ORDER BY full_name ASC;"
        else:
            sql = "SELECT * FROM members ORDER BY full_name ASC;"
        rows = self._execute_query_all(sql)
        return [Member.from_row(r) for r in rows]

    def create(self, member: Member) -> int:
        """Inserta un nuevo miembro y retorna su ID."""
        sql = """
            INSERT INTO members (full_name, email, role_title, department, phone, is_active)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        params = (
            member.full_name.strip(),
            member.email.strip().lower(),
            member.role_title.strip(),
            member.department.strip(),
            member.phone.strip() if member.phone else None,
            1 if member.is_active else 0
        )
        new_id = self._execute_insert(sql, params)
        member.id = new_id
        return new_id

    def update(self, member: Member) -> bool:
        """Actualiza los datos de un miembro existente."""
        if member.id is None:
            raise ValueError("El miembro debe contar con un ID para ser actualizado.")
        sql = """
            UPDATE members
            SET full_name = ?, email = ?, role_title = ?, department = ?, phone = ?, is_active = ?
            WHERE id = ?;
        """
        params = (
            member.full_name.strip(),
            member.email.strip().lower(),
            member.role_title.strip(),
            member.department.strip(),
            member.phone.strip() if member.phone else None,
            1 if member.is_active else 0,
            member.id
        )
        return self._execute_non_query(sql, params) > 0

    def delete(self, member_id: int) -> bool:
        """
        Elimina un integrante del equipo.
        Nota: Gracias a ON DELETE SET NULL, los tickets asignados no se borran,
        sino que su assigned_member_id pasa a ser NULL.
        """
        sql = "DELETE FROM members WHERE id = ?;"
        return self._execute_non_query(sql, (member_id,)) > 0
