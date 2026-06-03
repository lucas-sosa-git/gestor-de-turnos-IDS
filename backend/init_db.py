import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "gestor_de_turnos.db"
SQL_PATH = BASE_DIR / "init_db.sql"
SEED_PATH = BASE_DIR / "seed_peluqueria.sql"

conn = sqlite3.connect(DB_PATH)

with open(SQL_PATH, "r", encoding="utf-8") as archivo:
    conn.executescript(archivo.read())

with open(SEED_PATH, "r", encoding="utf-8") as archivo:
    conn.executescript(archivo.read())

conn.commit()
conn.close()

print("Base creada correctamente")