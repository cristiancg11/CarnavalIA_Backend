import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, engine
from app.core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from app.models.user import User
from sqlalchemy import select, text
import jwt

def test_auth_system():
    print("=" * 60)
    print("INICIANDO PRUEBAS DEL MÓDULO DE AUTENTICACIÓN")
    print("=" * 60)

    # 1. Probar funciones de seguridad
    print("\n[1] Probando app.core.security...")
    test_pwd = "CarnavalPasto2026#Secure"
    hashed = get_password_hash(test_pwd)
    assert hashed != test_pwd, "El hash no debe ser igual a la contraseña en plano"
    assert verify_password(test_pwd, hashed) is True, "La verificación debe ser True para la clave correcta"
    assert verify_password("ClaveErronea123", hashed) is False, "La verificación debe ser False para clave incorrecta"

    token = create_access_token(subject="42")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "42", "El subject del JWT debe ser '42'"
    assert "exp" in payload, "El JWT debe tener fecha de expiración"
    print("    [EXITO] Hash, verificación y generación de JWT funcionan correctamente.")

    # 2. Probar endpoints con TestClient
    client = TestClient(app)
    test_email = "ciudadano_test_carnaval@carnavalia.co"
    test_name = "Guaneña Test"
    test_password = "PasswordCarnaval2026!"

    # Limpiar usuario previo si quedó de alguna corrida anterior
    with SessionLocal() as db:
        old_user = db.execute(select(User).where(User.email == test_email)).scalar_one_or_none()
        if old_user:
            db.delete(old_user)
            db.commit()

    print("\n[2] Probando endpoint POST /api/v1/auth/register...")
    reg_payload = {
        "name": test_name,
        "email": test_email,
        "password": test_password
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    print(f"    - Status: {res_reg.status_code}")
    print(f"    - Response: {res_reg.json()}")
    assert res_reg.status_code == 201, f"Registro falló: {res_reg.text}"
    reg_data = res_reg.json()
    assert "access_token" in reg_data
    assert reg_data["token_type"] == "bearer"
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["name"] == test_name
    print("    [EXITO] Registro de usuario completado y guardado en Supabase con status 201.")

    print("\n[3] Probando validación de email duplicado en /register...")
    res_dup = client.post("/api/v1/auth/register", json=reg_payload)
    print(f"    - Status: {res_dup.status_code}")
    print(f"    - Detalle: {res_dup.json().get('detail')}")
    assert res_dup.status_code == 400, "Debe rechazar email duplicado con 400"
    print("    [EXITO] Rechazo correcto de correo ya registrado (HTTP 400).")

    print("\n[4] Probando endpoint POST /api/v1/auth/login con credenciales erróneas...")
    res_bad_pwd = client.post("/api/v1/auth/login", json={"email": test_email, "password": "WrongPassword"})
    assert res_bad_pwd.status_code == 401, "Debe retornar 401 con contraseña incorrecta"
    res_bad_user = client.post("/api/v1/auth/login", json={"email": "no_existe@carnavalia.co", "password": "123"})
    assert res_bad_user.status_code == 401, "Debe retornar 401 con usuario inexistente"
    print("    [EXITO] Rechazo correcto de credenciales inválidas (HTTP 401).")

    print("\n[5] Probando endpoint POST /api/v1/auth/login con credenciales correctas...")
    res_login = client.post("/api/v1/auth/login", json={"email": test_email, "password": test_password})
    print(f"    - Status: {res_login.status_code}")
    login_data = res_login.json()
    print(f"    - Access Token (primeros 25 chars): {login_data['access_token'][:25]}...")
    print(f"    - Usuario: {login_data['user']}")
    assert res_login.status_code == 200, f"Login falló: {res_login.text}"
    assert "access_token" in login_data
    assert login_data["user"]["email"] == test_email
    print("    [EXITO] Login exitoso con credenciales correctas (HTTP 200).")

    # Limpieza del usuario de prueba
    with SessionLocal() as db:
        user_to_delete = db.execute(select(User).where(User.email == test_email)).scalar_one_or_none()
        if user_to_delete:
            db.delete(user_to_delete)
            db.commit()
    print("\n    [INFO] Usuario de prueba eliminado limpiamente de la BD.")

    print("\n" + "=" * 60)
    print("¡TODAS LAS PRUEBAS DE AUTENTICACIÓN PASARON CON ÉXITO!")
    print("=" * 60)

if __name__ == "__main__":
    test_auth_system()
