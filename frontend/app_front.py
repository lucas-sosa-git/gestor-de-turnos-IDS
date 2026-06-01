import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__, template_folder="templates", static_folder="statics")


def get_backend_url():
    return os.environ.get("BACKEND_URL", "http://127.0.0.1:5000").rstrip("/")


def login_en_backend(email, clave):
    login_url = f"{get_backend_url()}/api/auth/login"
    payload = json.dumps({"email": email, "clave": clave}).encode("utf-8")

    login_request = Request(
        login_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(login_request, timeout=5) as response:
            return response.status < 400, None
    except HTTPError as error:
        mensaje = "Email o contrasena incorrectos."

        try:
            data = json.loads(error.read().decode("utf-8"))
            mensaje = data.get("mensaje") or data.get("error") or mensaje
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return False, mensaje
    except (URLError, TimeoutError):
        return False, "No se pudo conectar con el backend. Verifica que este levantado."


@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        clave = request.form.get("clave", "")

        if not email or not clave:
            error = "Ingresa email y contrasena."
        else:
            login_ok, error = login_en_backend(email, clave)
            if login_ok:
                return redirect(url_for("admin_panel"))

    return render_template("login.html", error=error)

@app.route("/admin")
def admin_panel():
    # Datos de ejemplo
    stats = {
        'ingresos_mes': 15000,
        'delta_ingresos': 15,
        'citas_completadas': 45,
        'delta_citas': 10,
        'clientes_activos': 120,
        'delta_clientes': 8,
        'calificacion_promedio': 4.8,
        'delta_rating': 0.3,
        'semanas': [
            {'label': 'Sem 1', 'monto': 10000},
            {'label': 'Sem 2', 'monto': 15000},
            {'label': 'Sem 3', 'monto': 20000},
            {'label': 'Sem 4', 'monto': 25000},
        ]
    }
    
    citas = [
        {'cliente': 'Juan Pérez', 'barbero': 'Carlos', 'servicio': 'Corte', 'hora': '10:00', 'estado': 'Completada'},
        {'cliente': 'María López', 'barbero': 'Ana', 'servicio': 'Tinte', 'hora': '11:30', 'estado': 'Pendiente'},
    ]
    
    barberos = [
        {'nombre': 'Carlos', 'citas': 50, 'rating': 4.8, 'ingresos': 50000, 'activo': True},
        {'nombre': 'Ana', 'citas': 45, 'rating': 4.9, 'ingresos': 48000, 'activo': True},
    ]
    
    servicios = [
        {'nombre': 'Corte', 'duracion_min': 30, 'precio': 10000, 'veces_solicitado': 45},
        {'nombre': 'Barba', 'duracion_min': 20, 'precio': 5000, 'veces_solicitado': 30},
    ]
    
    return render_template("admin/dashboard.html", 
                         stats=stats, 
                         citas=citas, 
                         barberos=barberos,
                         barberos_top=barberos,
                         servicios=servicios,
                         servicios_top=servicios)

@app.template_filter('format_miles')
def format_miles(value):
    try:
        
        num = int(float(value))
        return f"{num:,}".replace(",", ".")
    except (ValueError, TypeError):
        return value

if __name__ == "__main__":
    app.run(debug=True, port=5001)
