"""
Módulo de Seguridad y Criptografía
NEXORA TASKS - Tópicos Avanzados de Programación

Implementa funciones de hashing seguro de contraseñas utilizando PBKDF2-HMAC-SHA256
de la biblioteca estándar de Python (hashlib). Nunca almacena texto plano.
"""

import hashlib
import hmac
import os
import secrets
from typing import Tuple



class SecurityService:
    """
    Servicio encargado de la seguridad de credenciales en el sistema.
    Aplica técnicas de salting y funciones de derivación de claves para evitar
    ataques de diccionario y tablas arcoíris (Rainbow Tables).
    """

    ITERATIONS = 100_000  # Número de iteraciones para ralentizar ataques de fuerza bruta
    SALT_BYTES = 16       # 16 bytes (128 bits) de entropía aleatoria criptográfica
    ALGORITHM = 'sha256'

    @classmethod
    def generate_salt(cls) -> str:
        """Genera una sal criptográficamente segura en formato hexadecimal."""
        return secrets.token_hex(cls.SALT_BYTES)

    @classmethod
    def hash_password(cls, password: str, salt: str | None = None) -> Tuple[str, str]:
        """
        Calcula el hash de una contraseña utilizando PBKDF2 con sal.
        
        Args:
            password: La contraseña en texto plano ingresada por el usuario.
            salt: Sal opcional en formato hex. Si es None, se genera una nueva sal.
            
        Returns:
            Tuple[str, str]: (password_hash_hex, salt_hex)
        """
        if not password:
            raise ValueError("La contraseña no puede estar vacía.")

        if salt is None:
            salt = cls.generate_salt()

        salt_bytes = bytes.fromhex(salt)
        password_bytes = password.encode('utf-8')

        derived_key = hashlib.pbkdf2_hmac(
            hash_name=cls.ALGORITHM,
            password=password_bytes,
            salt=salt_bytes,
            iterations=cls.ITERATIONS
        )

        return derived_key.hex(), salt

    @classmethod
    def verify_password(cls, password: str, stored_hash: str, salt: str) -> bool:
        """
        Compara una contraseña en texto plano contra el hash y sal almacenados.
        Utiliza compare_digest para mitigar ataques de temporización (timing attacks).
        
        Args:
            password: La contraseña candidata enviada en el inicio de sesión.
            stored_hash: El hash guardado previamente en la base de datos.
            salt: La sal asociada al usuario guardada en la base de datos.
            
        Returns:
            bool: True si la contraseña es correcta, False en caso contrario.
        """
        if not password or not stored_hash or not salt:
            return False

        calculated_hash, _ = cls.hash_password(password, salt)
        return hmac.compare_digest(calculated_hash, stored_hash)
