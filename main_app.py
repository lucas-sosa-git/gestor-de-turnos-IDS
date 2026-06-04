import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent

BACKEND_APP = ROOT_DIR / "backend" / "app_back.py"
FRONTEND_APP = ROOT_DIR / "frontend" / "app_front.py"


def levantar_servidor(nombre, archivo):
    print(f"Levantando {nombre}...")
    return subprocess.Popen(
        [sys.executable, str(archivo)],
        cwd=ROOT_DIR
    )


def main():
    procesos = []

    try:
        backend = levantar_servidor("backend", BACKEND_APP)
        procesos.append(backend)

        time.sleep(1)

        frontend = levantar_servidor("frontend", FRONTEND_APP)
        procesos.append(frontend)

        print("\nServidores levantados:")
        print("Backend:  http://127.0.0.1:5000")
        print("Frontend: http://127.0.0.1:5001")

        print("Presioná CTRL + C para cerrar todo.\n")

        for proceso in procesos:
            proceso.wait()

    except KeyboardInterrupt:
        print("\nCerrando servidores...")

        for proceso in procesos:
            if proceso.poll() is None:
                proceso.terminate()

        print("Listo.")


if __name__ == "__main__":
    main()