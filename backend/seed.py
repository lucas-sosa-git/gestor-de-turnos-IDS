import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "gestor_de_turnos.db"
# Asegúrate de que el nombre del archivo .sql coincida exactamente aquí:
SQL_PATH = BASE_DIR / "seed_peluqueria.sql" 

try:
    conn = sqlite3.connect(DB_PATH)
    with open(SQL_PATH, "r", encoding="utf-8") as archivo:
        conn.executescript(archivo.read())
    conn.commit()
    print("¡Datos de prueba insertados con éxito!")
except Exception as e:
    print(f"Error al insertar datos: {e}")
finally:
    conn.close()