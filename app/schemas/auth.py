"""Esquemas Pydantic para autenticación y gestión de usuarios."""
from pydantic import BaseModel, EmailStr, ConfigDict


class UserRegister(BaseModel):
    """Esquema para registro de un nuevo usuario."""
    name: str | None = None
    full_name: str | None = None
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Esquema para inicio de sesión."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Esquema de respuesta de datos públicos de usuario."""
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Esquema de respuesta con token JWT de acceso."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
