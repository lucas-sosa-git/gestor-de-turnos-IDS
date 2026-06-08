import json
import os
import requests
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
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

def obtener_dashboard_admin():
    dashboard_url = f"{get_backend_url()}/admin/dashboard"

    dashboard_request = Request(
        dashboard_url,
        headers={"Content-Type": "application/json"},
        method="GET",
    )

    try:
        with urlopen(dashboard_request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8")), None

    except HTTPError as error:
        try:
            data = json.loads(error.read().decode("utf-8"))
            return None, data.get("error") or "Error al obtener estadísticas."
        except Exception:
            return None, "Error al obtener estadísticas."

    except (URLError, TimeoutError):
        return None, "No se pudo conectar con el backend."


def stats_admin_vacias():
    return {
        "ingresos_mes": 0,
        "delta_ingresos": 0,
        "citas_completadas": 0,
        "delta_citas": 0,
        "clientes_activos": 0,
        "delta_clientes": 0,
        "calificacion_promedio": 0,
        "delta_rating": 0,
        "semanas": []
    }


ADMIN_ERROR_MESSAGES = {
    "backend": "No se pudo conectar con el backend.",
    "crear_servicio": "No se pudo crear el servicio.",
    "editar_servicio": "No se pudo editar el servicio.",
    "eliminar_servicio": "No se pudo eliminar el servicio.",
}


def mensaje_error_admin():
    error = request.args.get("error")
    if not error:
        return None

    return ADMIN_ERROR_MESSAGES.get(error, error)


def mensaje_error_backend(response, mensaje_default):
    try:
        data = response.json()
        return data.get("error") or data.get("mensaje") or mensaje_default
    except ValueError:
        return mensaje_default


def redirect_admin_error(mensaje):
    return redirect("/admin?" + urlencode({"error": mensaje}))


@app.route("/admin")
def admin_panel():
    data, error = obtener_dashboard_admin()
    error_admin = mensaje_error_admin()

    if error:
        return render_template(
            "admin/dashboard.html",
            stats=stats_admin_vacias(),
            citas=[],
            barberos=[],
            barberos_top=[],
            servicios=[],
            servicios_top=[],
            error=error
        )

    return render_template(
        "admin/dashboard.html",
        stats=data.get("stats", stats_admin_vacias()),
        citas=data.get("citas", []),
        barberos=data.get("barberos", []),
        barberos_top=data.get("barberos_top", []),
        servicios=data.get("servicios", []),
        servicios_top=data.get("servicios_top", []),
        error=error_admin
    )

@app.route("/admin/servicios/crear", methods=["POST"])
def crear_servicio_front():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    duracion = request.form.get("duracion", "").strip()
    precio = request.form.get("precio", "").strip()
    imagen = request.files.get("imagen")

    data = {
        "nombre": nombre,
        "descripcion": descripcion,
        "duracion": duracion,
        "precio": precio
    }

    files = None

    if imagen and imagen.filename:
        files = {
            "imagen": (imagen.filename, imagen.stream, imagen.mimetype)
        }

    try:
        response = requests.post(
            f"{get_backend_url()}/admin/servicios",
            data=data,
            files=files,
            timeout=10
        )

        if response.status_code >= 400:
            mensaje = mensaje_error_backend(response, "No se pudo crear el servicio.")
            return redirect_admin_error(mensaje)

    except requests.RequestException:
        return redirect_admin_error("backend")

    return redirect("/admin")

@app.route("/admin/servicios/<int:id_servicio>/editar", methods=["POST"])
def editar_servicio_front(id_servicio):
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    duracion = request.form.get("duracion", "").strip()
    precio = request.form.get("precio", "").strip()
    imagen = request.files.get("imagen")

    data = {
        "nombre": nombre,
        "descripcion": descripcion,
        "duracion": duracion,
        "precio": precio
    }

    files = None

    if imagen and imagen.filename:
        files = {
            "imagen": (imagen.filename, imagen.stream, imagen.mimetype)
        }

    try:
        response = requests.put(
            f"{get_backend_url()}/admin/servicios/{id_servicio}",
            data=data,
            files=files,
            timeout=10
        )

        if response.status_code >= 400:
            mensaje = mensaje_error_backend(response, "No se pudo editar el servicio.")
            return redirect_admin_error(mensaje)

    except requests.RequestException:
        return redirect_admin_error("backend")

    return redirect("/admin")


@app.route("/admin/servicios/<int:id_servicio>/eliminar", methods=["POST"])
def eliminar_servicio_front(id_servicio):
    try:
        response = requests.delete(
            f"{get_backend_url()}/admin/servicios/{id_servicio}",
            timeout=10
        )

        if response.status_code >= 400:
            mensaje = mensaje_error_backend(response, "No se pudo eliminar el servicio.")
            return redirect_admin_error(mensaje)

    except requests.RequestException:
        return redirect_admin_error("backend")

    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
