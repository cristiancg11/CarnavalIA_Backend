"""Esquemas Pydantic para autenticación y gestión limpia de usuarios."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class UserRegister(BaseModel):
    """Esquema para registro de un nuevo usuario."""
    email: str
    password: str
    full_name: str


class UserLogin(BaseModel):
    """Esquema para inicio de sesión."""
    email: str
    password: str


class UserData(BaseModel):
    """Datos públicos básicos del usuario."""
    email: str
    full_name: str


class AuthResponse(BaseModel):
    """Respuesta estándar para operaciones de autenticación."""
    status: str = "success"
    user: UserData


class UserResponse(BaseModel):
    """Esquema extendido de usuario."""
    id: Optional[int] = None
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = "citizen"

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Esquema de token para compatibilidad."""
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
