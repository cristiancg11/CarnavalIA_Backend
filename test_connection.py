import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
import app.models  # noqa: F401
from app.db.seed import seed_points_of_interest
from sqlalchemy import inspect, text

def test_supabase_connection():
    print("=" * 60)
    print("VERIFICACIÓN DE CONEXIÓN A SUPABASE POSTGRESQL")
    print("=" * 60)
    
    # 1. Database URL check
    raw_url = settings.DATABASE_URL
    if "@" in raw_url:
        protocol_and_user, host_part = raw_url.split("@", 1)
        # Mask password
        if ":" in protocol_and_user:
            parts = protocol_and_user.split(":")
            # parts[0] is postgresql, parts[1] is //user, parts[2] is password
            masked_user_info = ":".join(parts[:-1]) + ":********"
        else:
            masked_user_info = protocol_and_user
        masked_url = f"{masked_user_info}@{host_part}"
    else:
        masked_url = raw_url
        
    print(f"[1] DATABASE_URL configurada: {masked_url}")
    print(f"    ¿Usa pooler de Supabase?: {'SI' if 'pooler.supabase.com' in raw_url else 'NO'}")
    
    # 2. Test direct connection and database info
    print("\n[2] Probando conexión directa a PostgreSQL...")
    try:
        with engine.connect() as conn:
            db_info = conn.execute(text("SELECT current_database(), version();")).fetchone()
            print("    [EXITO] Conexión establecida correctamente.")
            print(f"    - Base de datos actual: {db_info[0]}")
            print(f"    - Versión del motor: {db_info[1]}")
    except Exception as e:
        print(f"    [ERROR] Falló la conexión: {e}")
        return False

    # 3. Create tables if not exist
    print("\n[3] Verificando / creando tablas con SQLAlchemy Base.metadata.create_all()...")
    try:
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"    [EXITO] Tablas encontradas en la BD ({len(tables)}): {tables}")
    except Exception as e:
        print(f"    [ERROR] Error al crear/inspeccionar tablas: {e}")
        return False

    # 4. Check seed / records in tables
    print("\n[4] Verificando datos y ejecutando seeder...")
    try:
        with SessionLocal() as db:
            seed_points_of_interest(db)
            
        with engine.connect() as conn:
            for table in tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table};")).scalar()
                print(f"    - Tabla '{table}': {count} registros")
    except Exception as e:
        print(f"    [ERROR] Error al verificar datos: {e}")
        return False

    print("\n" + "=" * 60)
    print("RESULTADO: ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
