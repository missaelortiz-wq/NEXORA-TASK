"""
Servicio de Autenticación y Cuentas de Usuario
NEXORA TASKS - Tópicos Avanzados de Programación
"""

from typing import List, Optional, Tuple

from models.user import User
from repositories.user_repository import UserRepository
from services.security import SecurityService


class AuthService:
    """
    Gestiona la lógica de negocio para la autenticación, inicio de sesión,
    registro de nuevos operadores y cambio seguro de contraseñas.
    Aplica control estricto de roles (Administrador vs Operador).
    """

    def __init__(self, user_repo: Optional[UserRepository] = None):
        """Inicializa el servicio inyectando el repositorio de usuarios."""
        self.user_repo = user_repo or UserRepository()

    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Valida las credenciales de un usuario.
        
        Args:
            username: Nombre de usuario.
            password: Contraseña en texto plano ingresada.
            
        Returns:
            Tuple[bool, str, Optional[User]]: (éxito, mensaje descriptivo, entidad Usuario o None)
        """
        if not username or not password:
            return False, "Debe ingresar usuario y contraseña.", None

        user = self.user_repo.find_by_username(username.strip())
        if not user:
            return False, "Credenciales incorrectas.", None

        if not user.is_active:
            return False, "La cuenta de usuario se encuentra deshabilitada.", None

        is_valid = SecurityService.verify_password(password, user.password_hash, user.salt)
        if not is_valid:
            return False, "Credenciales incorrectas.", None

        return True, f"Bienvenido al sistema, {user.full_name}.", user

    def register_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str,
        requester: Optional[User] = None
    ) -> User:
        """
        Registra una nueva cuenta en el sistema aplicando salting y hashing criptográfico.
        Si se pasa requester, valida que cuente con permisos de Administrador.
        """
        if requester is not None and not requester.is_admin():
            raise PermissionError("Acceso denegado: Solo el Administrador puede registrar cuentas de usuario.")

        if not username or len(username.strip()) < 3:
            raise ValueError("El nombre de usuario debe contener al menos 3 caracteres.")
        if not password or len(password) < 6:
            raise ValueError("La contraseña debe tener una longitud mínima de 6 caracteres.")
        if role not in ("Administrador", "Operador"):
            raise ValueError("El rol debe ser 'Administrador' u 'Operador'.")

        existing = self.user_repo.find_by_username(username.strip())
        if existing:
            raise ValueError(f"El nombre de usuario '{username}' ya está registrado.")

        # Calcular hash seguro con sal aleatoria
        password_hash, salt = SecurityService.hash_password(password)

        new_user = User(
            username=username.strip(),
            password_hash=password_hash,
            salt=salt,
            full_name=full_name.strip(),
            role=role,
            is_active=True
        )

        self.user_repo.create(new_user)
        return new_user

    def change_password(self, user_id: int, current_pass: str, new_pass: str) -> Tuple[bool, str]:
        """Permite actualizar la contraseña verificando primero la contraseña actual."""
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return False, "Usuario no encontrado."

        if not SecurityService.verify_password(current_pass, user.password_hash, user.salt):
            return False, "La contraseña actual es incorrecta."

        if len(new_pass) < 6:
            return False, "La nueva contraseña debe tener al menos 6 caracteres."

        new_hash, new_salt = SecurityService.hash_password(new_pass)
        success = self.user_repo.update_password(user_id, new_hash, new_salt)
        return success, "Contraseña actualizada correctamente."

    def get_all_users(self, requester: User) -> List[User]:
        """
        Retorna la lista de todas las cuentas registradas.
        Solo accesible para usuarios con rol de Administrador.
        """
        if not requester.is_admin():
            raise PermissionError("Acceso denegado: Solo el Administrador puede consultar las cuentas del sistema.")
        return self.user_repo.find_all()

    def set_user_active_status(self, user_id: int, is_active: bool, requester: User) -> bool:
        """
        Habilita o deshabilita una cuenta de usuario.
        Regla: El Administrador no puede desactivar su propia cuenta activa.
        """
        if not requester.is_admin():
            raise PermissionError("Acceso denegado: Solo el Administrador puede modificar estados de cuenta.")

        if user_id == requester.id and not is_active:
            raise ValueError("No puedes deshabilitar tu propia cuenta activa de Administrador.")

        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ValueError(f"No existe ningún usuario con ID {user_id}.")

        return self.user_repo.set_active_status(user_id, is_active)

    def admin_reset_password(self, user_id: int, new_password: str, requester: User) -> bool:
        """
        Restablece la contraseña de cualquier usuario desde el panel administrativo.
        """
        if not requester.is_admin():
            raise PermissionError("Acceso denegado: Solo el Administrador puede restablecer contraseñas ajenas.")

        if len(new_password) < 6:
            raise ValueError("La nueva contraseña debe tener al menos 6 caracteres.")

        new_hash, new_salt = SecurityService.hash_password(new_password)
        return self.user_repo.update_password(user_id, new_hash, new_salt)
