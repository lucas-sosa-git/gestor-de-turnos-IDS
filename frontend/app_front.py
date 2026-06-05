import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, redirect, render_template, request, session, url_for


app = Flask(__name__, template_folder="templates", static_folder="statics")
app.secret_key = "clave_front_tp_barberia"


def get_backend_url():
    return os.environ.get("BACKEND_URL", "http://127.0.0.1:5000").rstrip("/")


def login_en_backend(email, clave):
    login_url = f"{get_backend_url()}/api/auth/login"

    payload = json.dumps({
        "email": email,
        "clave": clave
    }).encode("utf-8")

    login_request = Request(
        login_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(login_request, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            token = data.get("token")
            usuario = data.get("usuario")

            if not token or not usuario:
                return False, None, None, "El backend no devolvió token o datos del usuario."

            return True, usuario, token, None

    except HTTPError as error:
        mensaje = "Email o contraseña incorrectos."

        try:
            data = json.loads(error.read().decode("utf-8"))
            mensaje = data.get("error") or data.get("mensaje") or mensaje
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return False, None, None, mensaje

    except (URLError, TimeoutError):
        return False, None, None, "No se pudo conectar con el backend. Verificá que esté levantado en el puerto 5000."


def registrar_en_backend(nombre, email, clave):
    register_url = f"{get_backend_url()}/clientes/"

    payload = json.dumps({
        "nombre": nombre,
        "email": email,
        "clave": clave
    }).encode("utf-8")

    register_request = Request(
        register_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(register_request, timeout=5) as response:
            return response.status < 400, None

    except HTTPError as error:
        mensaje = "No se pudo crear la cuenta."

        try:
            data = json.loads(error.read().decode("utf-8"))
            mensaje = data.get("mensaje") or data.get("error") or mensaje
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return False, mensaje

    except (URLError, TimeoutError):
        return False, "No se pudo conectar con el backend. Verifica que este levantado."


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        exito = None

        if request.args.get("registro") == "ok":
            exito = "Cuenta creada correctamente. Ya podés iniciar sesión."

        return render_template("login.html", exito=exito)

    email = request.form.get("email", "").strip()
    clave = request.form.get("clave", "").strip()

    if not email or not clave:
        return render_template(
            "login.html",
            error="Completá email y contraseña."
        )

    ok, usuario, token, error = login_en_backend(email, clave)

    if not ok:
        return render_template("login.html", error=error, email=email)

    session["token"] = token
    session["usuario"] = usuario
    session["id_usuario"] = usuario.get("id_usuario")
    session["rol"] = usuario.get("rol")

    rol = usuario.get("rol", "").lower()

    if rol in ["admin", "administrador"]:
        return redirect("/admin")

    if rol == "cliente":
        return redirect("/detalle")

    if rol in ["barbero", "peluquero", "profesional"]:
        return redirect("/panel_peluquero")

    return render_template(
        "login.html",
        error=f"Rol no reconocido: {rol}"
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        clave = request.form.get("clave", "")

        if not nombre or not email or not clave:
            error = "Completá todos los campos."
        else:
            registro_ok, error = registrar_en_backend(nombre, email, clave)

            if registro_ok:
                return redirect(url_for("login", registro="ok"))

    return render_template("register.html", error=error)


@app.route("/admin")
def admin_panel():
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


if __name__ == "__main__":
    app.run(debug=True, port=5001)
