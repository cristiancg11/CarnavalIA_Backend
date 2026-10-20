"""Endpoints de autenticación (Registro y Login con JWT)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de nuevo usuario",
    description="Registra un nuevo usuario en la plataforma, hashea la contraseña y retorna un token JWT de acceso."
)
@router.post(
    "/register/",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    """Registra un nuevo usuario validando unicidad de correo y hasheando contraseña."""
    user_name = (user_in.name or user_in.full_name or "").strip()
    if not user_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre es obligatorio."
        )

    normalized_email = user_in.email.strip().lower()

    # 1. Validar si el email ya existe
    existing_user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado."
        )

    # 2. Hashear la contraseña con pwdlib
    hashed_pwd = get_password_hash(user_in.password)

    # 3. Guardar el usuario en la BD de Supabase vía SQLAlchemy
    new_user = User(
        name=user_name,
        email=normalized_email,
        password_hash=hashed_pwd,
        role="ciudadano"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Generar JWT y retornar TokenResponse con status 201
    access_token = create_access_token(subject=str(new_user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión",
    description="Valida las credenciales del usuario y genera un token JWT de acceso."
)
@router.post(
    "/login/",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Valida credenciales contra password_hash y retorna TokenResponse con su JWT."""
    normalized_email = credentials.email.strip().lower()
    # 1. Buscar usuario por email
    user = db.execute(
        select(User).where(User.email == normalized_email)
    ).scalar_one_or_none()

    # 2. Validar credenciales contra password_hash
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifique su correo y contraseña.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generar token JWT
    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )
