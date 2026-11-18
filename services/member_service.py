"""
Servicio de Gestión de Miembros del Equipo
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional

from models.member import Member
from repositories.member_repository import MemberRepository


class MemberService:
    """
    Gestiona la lógica de negocio asociada a los integrantes del equipo de trabajo.
    """

    def __init__(self, member_repo: Optional[MemberRepository] = None):
        """Inicializa el servicio inyectando el repositorio de miembros."""
        self.member_repo = member_repo or MemberRepository()

    def register_member(
        self,
        full_name: str,
        email: str,
        role_title: str,
        department: str,
        phone: Optional[str] = None
    ) -> Member:
        """Valida y registra un nuevo miembro del equipo."""
        if not full_name or not full_name.strip():
            raise ValueError("El nombre del miembro es obligatorio.")
        if not email or "@" not in email:
            raise ValueError("El correo electrónico proporcionado no es válido.")

        existing = self.member_repo.find_by_email(email.strip().lower())
        if existing:
            raise ValueError(f"Ya existe un miembro registrado con el correo '{email}'.")

        member = Member(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            role_title=role_title.strip(),
            department=department.strip(),
            phone=phone.strip() if phone else None,
            is_active=True
        )
        self.member_repo.create(member)
        return member

    def get_all_members(self, active_only: bool = False) -> List[Member]:
        """Obtiene la lista de miembros."""
        return self.member_repo.find_all(active_only=active_only)

    def get_member_by_id(self, member_id: int) -> Optional[Member]:
        """Recupera un miembro por ID."""
        return self.member_repo.find_by_id(member_id)

    def update_member(self, member: Member) -> bool:
        """Actualiza la información de un miembro."""
        return self.member_repo.update(member)

    def update_member_details(
        self,
        member_id: int,
        full_name: str,
        email: str,
        role_title: str,
        department: str,
        phone: Optional[str] = None,
        is_active: bool = True
    ) -> Member:
        """
        Actualiza los datos de un miembro validando correo único y campos requeridos.
        """
        member = self.member_repo.find_by_id(member_id)
        if not member:
            raise ValueError(f"No existe ningún miembro con ID {member_id}.")

        if not full_name or not full_name.strip():
            raise ValueError("El nombre del miembro es obligatorio.")
        if not email or "@" not in email:
            raise ValueError("El correo electrónico proporcionado no es válido.")

        email_clean = email.strip().lower()
        if email_clean != member.email:
            existing = self.member_repo.find_by_email(email_clean)
            if existing and existing.id != member_id:
                raise ValueError(f"Ya existe otro integrante registrado con el correo '{email_clean}'.")

        member.full_name = full_name.strip()
        member.email = email_clean
        member.role_title = role_title.strip()
        member.department = department.strip()
        member.phone = phone.strip() if phone else None
        member.is_active = is_active

        self.member_repo.update(member)
        return member

    def set_active_status(self, member_id: int, is_active: bool) -> bool:
        """Activa o desactiva a un integrante del equipo."""
        member = self.member_repo.find_by_id(member_id)
        if not member:
            raise ValueError(f"No existe ningún miembro con ID {member_id}.")
        member.is_active = is_active
        return self.member_repo.update(member)

    def delete_member(self, member_id: int) -> bool:
        """Elimina un miembro del sistema."""
        return self.member_repo.delete(member_id)
