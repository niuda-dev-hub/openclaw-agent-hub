import os

def get_repo():
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    if backend == "supabase":
        from . import supabase_repo
        return supabase_repo
    else:
        from . import sqlite_repo
        return sqlite_repo
