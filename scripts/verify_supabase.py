#!/usr/bin/env python3
"""Script CLI automatizado para verificación de integridad de Supabase.

Verifica la conectividad, autenticación y respuesta de las tablas clave
('reports', 'events') usando las credenciales configuradas en el entorno (.env).
"""
import os
import sys
from pathlib import Path

# Garantizar que la raíz del proyecto esté en el sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.db.supabase import supabase_client
from app.core.database import engine
from sqlalchemy import text, inspect


def verify_supabase() -> bool:
    print("=" * 70)
    print("CARNAVALIA BACKEND - VERIFICACIÓN CLI DE SUPABASE")
    print("=" * 70)

    print(f"\n[1] Cargando credenciales desde .env:")
    print(f"    - SUPABASE_URL: {settings.SUPABASE_URL}")
    print(f"    - SUPABASE_KEY: {settings.SUPABASE_KEY[:10]}...{settings.SUPABASE_KEY[-5:] if len(settings.SUPABASE_KEY) > 15 else ''}")
    print(f"    - DATABASE_URL: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Configurada'}")

    # 1. Probar conectividad general del cliente Supabase
    print("\n[2] Comprobando salud y disponibilidad del servicio...")
    health = supabase_client.check_connection()
    if health.get("status") != "ok":
        print(f"    [ERROR] No se pudo conectar a Supabase: {health.get('message', 'Error desconocido')}")
        return False
    print(f"    [EXITO] Conexión establecida ({health.get('provider')}, protocolo: {health.get('protocol', 'activo')}).")

    # 2. Verificar existencia y respuesta de tablas clave ('reports', 'events')
    required_tables = ["reports", "events"]
    print(f"\n[3] Verificando existencia y sondeo de tablas clave: {required_tables}...")

    verified_tables = []
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        for table in required_tables:
            if table not in existing_tables:
                print(f"    [ERROR] La tabla obligatoria '{table}' no existe en el esquema público de Supabase.")
                return False

            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table};")).scalar()
                print(f"    - Tabla '{table}': [OK] Respondiendo activamente ({count} registros)")
                verified_tables.append(table)
            except Exception as query_err:
                print(f"    [ERROR] Error al consultar la tabla '{table}': {query_err}")
                return False

    print("\n" + "-" * 70)
    print(f"Tablas verificadas exitosamente: {', '.join(verified_tables)}")
    print("[OK] Supabase conectado y operando al 100%")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = verify_supabase()
    sys.exit(0 if success else 1)

