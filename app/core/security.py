"""Módulo de seguridad para hashing de contraseñas y generación de tokens JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import jwt
from pwdlib import PasswordHash

# Clave secreta y algoritmo para firma de JWT
SECRET_KEY = "carnavalia_super_secret_jwt_key_pasto_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Instancia de hasher recomendada por pwdlib (Argon2 / Bcrypt)
password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """Genera un hash seguro para la contraseña proporcionada."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Crea un token JWT de acceso firmado con expiración configurada."""
    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
