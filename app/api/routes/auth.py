"""Endpoints limpios de autenticación ciudadana respaldados en la tabla users de Supabase."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, AuthResponse, UserData
from app.core.security import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    status_code=status.HTTP_200_OK,
    summary="Registro de usuario ciudadano",
    description="Registra un nuevo usuario en la tabla users de Supabase."
)
@router.post(
    "/register/",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    """Consulta si el email ya existe; si no, inserta y retorna el usuario registrado."""
    # 1. Consulta si el email ya existe en users
    clean_email = user_in.email.strip().lower()
    existing_user = db.query(User).filter(User.email.ilike(clean_email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )

    # 2. Insertar nuevo registro en la tabla limpia users
    new_user = User(
        email=clean_email,
        full_name=user_in.full_name.strip(),
        password_hash=user_in.password,
        role="citizen"
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar usuario en Supabase: {str(exc)}"
        )

    return {
        "status": "success",
        "user": {
            "email": new_user.email,
            "full_name": new_user.full_name
        }
    }


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión de usuario",
    description="Verifica credenciales contra la tabla users de Supabase."
)
@router.post(
    "/login/",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def login(
    user_in: UserLogin,
    db: Session = Depends(get_db)
):
    """Consulta en users donde email y password_hash coincidan."""
    clean_email = user_in.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(clean_email)).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    # Comparación directa o mediante hash para máxima tolerancia
    password_matches = (user.password_hash == user_in.password)
    if not password_matches:
        try:
            password_matches = verify_password(user_in.password, user.password_hash)
        except Exception:
            password_matches = False

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    return {
        "status": "success",
        "user": {
            "email": user.email,
            "full_name": user.full_name
        }
    }
