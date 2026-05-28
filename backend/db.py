import sqlite3
from pathlib import Path

# Buscamos la ruta de la base de datos que crea tu init_db.py
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "gestor_de_turnos.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # Esto sirve para que los resultados parezcan diccionarios de Python
    conn.row_factory = sqlite3.Row 
    return conn