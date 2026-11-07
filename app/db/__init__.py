"""Módulo de persistencia y base de datos para CarnavalIA."""
from app.db.supabase import (
    supabase,
    supabase_client,
    get_supabase_client,
    ResilientSupabaseClient,
)

__all__ = [
    "supabase",
    "supabase_client",
    "get_supabase_client",
    "ResilientSupabaseClient",
]
