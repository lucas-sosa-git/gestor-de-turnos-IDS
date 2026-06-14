import json
import os
import requests
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from collections import defaultdict
from datetime import datetime,timedelta

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
                return False, None, None, "El backend no devolviÃ³ token o datos del usuario."

            return True, usuario, token, None

    except HTTPError as error:
        mensaje = "Email o contraseÃ±a incorrectos."

        try:
            data = json.loads(error.read().decode("utf-8"))
            mensaje = data.get("error") or data.get("mensaje") or mensaje
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

        return False, None, None, mensaje

    except (URLError, TimeoutError):
        return False, None, None, "No se pudo conectar con el backend. VerificÃ¡ que estÃ© levantado en el puerto 5000."


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


def obtener_json_backend(path, mensaje_error):
    url = f"{get_backend_url()}{path}"
    backend_request = Request(
        url,
        headers={"Content-Type": "application/json"},
        method="GET",
    )

    try:
        with urlopen(backend_request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8")), None

    except HTTPError as error:
        try:
            data = json.loads(error.read().decode("utf-8"))
            return None, data.get("error") or mensaje_error
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, mensaje_error

    except (URLError, TimeoutError):
        return None, mensaje_error


def obtener_panel_cliente(id_usuario):
    return obtener_json_backend(
        f"/clientes/panel/{id_usuario}",
        "No se pudieron cargar los datos del cliente"
    )


def obtener_barberos_cliente(id_usuario):
    return obtener_json_backend(
        f"/clientes/barberos/{id_usuario}",
        "No se pudieron cargar los barberos"
    )


def obtener_info_cliente(id_usuario):
    return obtener_json_backend(
        f"/clientes/acerca-de/{id_usuario}",
        "No se pudo cargar la informacion del cliente"
    )

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        exito = None

        if request.args.get("registro") == "ok":
            exito = "Cuenta creada correctamente. Ya podÃ©s iniciar sesiÃ³n."

        return render_template("login.html", exito=exito)

    email = request.form.get("email", "").strip()
    clave = request.form.get("clave", "").strip()

    if not email or not clave:
        return render_template(
            "login.html",
            error="CompletÃ¡ email y contraseÃ±a."
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
        id_usuario = usuario.get("id_usuario")
        return redirect(f"/clientes/{id_usuario}")

    if rol in ["barbero", "peluquero", "profesional"]:
        id_usuario = usuario.get("id_usuario")
        return redirect(f"/panel_peluquero/{id_usuario}")

    return render_template(
        "login.html",
        error=f"Rol no reconocido: {rol}"
    )

@app.route("/clientes/<int:id_usuario>")
def clientes_panel(id_usuario):
    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    data, error = obtener_panel_cliente(id_usuario)
    if data:
        usuario = data.get("usuario", usuario)

    return render_template(
        "feature_clientes/clientes.html",
        usuario=usuario,
        id_usuario=id_usuario,
        turnos=data.get("turnos", []) if data else [],
        error=error
    )


@app.route("/clientes/<int:id_usuario>/barberos")
def clientes_barberos(id_usuario):
    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    data, error = obtener_barberos_cliente(id_usuario)
    if data:
        usuario = data.get("usuario", usuario)

    return render_template(
        "feature_clientes/nuestros_barberos.html",
        usuario=usuario,
        id_usuario=id_usuario,
        barberos=data.get("barberos", []) if data else [],
        turnos=data.get("turnos", []) if data else [],
        error=error
    )


@app.route("/clientes/<int:id_usuario>/info")
def clientes_info(id_usuario):
    usuario = session.get("usuario")

    if not usuario:
        return redirect("/login")

    data, error = obtener_info_cliente(id_usuario)
    if data:
        usuario = data.get("usuario", usuario)

    return render_template(
        "feature_clientes/Info.html",
        usuario=usuario,
        id_usuario=id_usuario,
        turnos=data.get("turnos", []) if data else [],
        error=error
    )

def obtener_panel_peluqueros(id_usuario):
    return obtener_json_backend(
        f"/peluqueros/{id_usuario}",
        "No se pudieron cargar los datos del cliente"
    )
def normalizar_fecha(fecha_objeto_o_cadena):
    """Convierte cualquier variante de fecha de la DB a formato estándar string 'YYYY-MM-DD'"""
    if not fecha_objeto_o_cadena:
        return ""
    fecha_limpia = str(fecha_objeto_o_cadena).split(' ')[0].strip() # Quita horas sobrantes si existen
    for formato in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(fecha_limpia, formato).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return fecha_limpia
@app.route("/panel_peluquero/<int:id_usuario>")
def panel_peluquero(id_usuario):
    usuario = session.get("usuario")
    vista_actual = request.args.get('vista', 'dia') 
    fecha_str_actual = request.args.get('fecha')
    if not fecha_str_actual:
        fecha_str_actual = datetime.today().strftime('%Y-%m-%d')
    try:
        fecha_actual = datetime.strptime(fecha_str_actual, '%Y-%m-%d')
    except ValueError:
        fecha_actual = datetime.today()
        fecha_str_actual = fecha_actual.strftime('%Y-%m-%d')
    if vista_actual == 'semana':
        fecha_anterior = (fecha_actual - timedelta(days=7)).strftime('%Y-%m-%d')
        fecha_siguiente = (fecha_actual + timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        fecha_anterior = (fecha_actual - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_siguiente = (fecha_actual + timedelta(days=1)).strftime('%Y-%m-%d')
    fecha_label = fecha_actual.strftime('%d de %B de %Y')
    #Calculamos de lun a dom de la semana que se elige
    semana_inicio = fecha_actual - timedelta(days=fecha_actual.weekday())
    semana_inicio_label = semana_inicio.strftime('%d %b')
    semana_fin_label = (semana_inicio + timedelta(days=6)).strftime('%d %b')
    data, error= obtener_panel_peluqueros(id_usuario)

    lista_total_citas = data.get("turnos", []) if data else []
    usuario_datos = data.get("usuario", usuario) if data else usuario
    turnos_dia = []
    dias_semana = []
    fecha_hoy_normalizada = normalizar_fecha(fecha_str_actual)
    if vista_actual == 'semana':
        nombres_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dias_dict = {}
        for i in range(7):
            dia_fecha = semana_inicio + timedelta(days=i)
            dia_str = dia_fecha.strftime('%Y-%m-%d')
            dias_dict[dia_str] = {
                'nombre_dia': nombres_dias[i],
                'fecha_label': dia_fecha.strftime('%d %b'),
                'fecha_str': dia_str,
                'citas': []
            }
        for turno in lista_total_citas:
            fecha_turno_normalizada = normalizar_fecha(turno.get('fecha'))
            if fecha_turno_normalizada in dias_dict:
                dias_dict[fecha_turno_normalizada]['citas'].append(turno)
        dias_semana = list(dias_dict.values())
    else:
        for turno in lista_total_citas:
            fecha_turno_normalizada = normalizar_fecha(turno.get('fecha'))
            if fecha_turno_normalizada == fecha_hoy_normalizada:
                turnos_dia.append(turno)

    return render_template(
        "panel_barberos.html",
        usuario=usuario_datos,
        id_usuario = id_usuario,
        turnos = turnos_dia,
        dias_semana= dias_semana,
        error = error,
        vista = vista_actual,
        fecha_str = fecha_str_actual,
        fecha_anterior = fecha_anterior,
        fecha_siguiente = fecha_siguiente,
        fecha_label = fecha_label,
        semana_inicio_label = semana_inicio_label,
        semana_fin_label = semana_fin_label
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        clave = request.form.get("clave", "")

        if not nombre or not email or not clave:
            error = "CompletÃ¡ todos los campos."
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
            return None, data.get("error") or "Error al obtener estadÃ­sticas."
        except Exception:
            return None, "Error al obtener estadÃ­sticas."

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
        response = requests.patch(
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

#  AGENDA BARBERO


def parsear_fecha(fecha_str):
    """Convierte 'YYYY-MM-DD' a date. Si falla, devuelve hoy."""
    try:
        return date.fromisoformat(fecha_str)
    except (ValueError, TypeError):
        return date.today()


def inicio_de_semana(d):
    """Devuelve el lunes de la semana que contiene d."""
    return d - timedelta(days=d.weekday())


DIAS_ES   = ["Lunes","Martes","MiÃ©rcoles","Jueves","Viernes","SÃ¡bado","Domingo"]
DIAS_CORTOS = ["Lun","Mar","MiÃ©","Jue","Vie","SÃ¡b","Dom"]
MESES_ES  = ["","enero","febrero","marzo","abril","mayo","junio",
             "julio","agosto","septiembre","octubre","noviembre","diciembre"]


def formatear_fecha_larga(d):
    """ej: 'domingo, 7 de junio de 2026'"""
    nombre_dia = DIAS_ES[d.weekday()]
    return f"{nombre_dia}, {d.day} de {MESES_ES[d.month]} de {d.year}"


def formatear_fecha_corta(d):
    """ej: '7 jun 2026'  o  '7 jun' (sin aÃ±o si es el mismo aÃ±o)"""
    anio = f" {d.year}" if d.year != date.today().year else ""
    return f"{d.day} {MESES_ES[d.month][:3]}{anio}"

def hacer_request(url, method="GET", payload=None, token=None):
    """
    Wrapper genÃ©rico para llamadas al backend.
    Devuelve (data_dict_or_list, error_str_or_None).
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = json.dumps(payload).encode("utf-8") if payload else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8")), None

    except HTTPError as error:
        mensaje = "Error en el servidor."
        try:
            body = json.loads(error.read().decode("utf-8"))
            mensaje = body.get("error") or body.get("mensaje") or mensaje
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        return None, mensaje

    except (URLError, TimeoutError):
        return None, "No se pudo conectar con el backend."

# Llamadas al backend

def obtener_citas_dia(id_barbero, fecha_str, token):
    """
    GET /barberos/<id>/agenda?fecha=YYYY-MM-DD
    Espera lista de citas:
      [{ cliente_nombre, cliente_email, hora, servicio }, ...]
    """
    url = f"{get_backend_url()}/barberos/{id_barbero}/agenda?fecha={fecha_str}"
    data, error = hacer_request(url, token=token)
    if error or not isinstance(data, list):
        return []
    return data


def obtener_citas_semana(id_barbero, lunes_str, token):
    """
    GET /barberos/<id>/agenda/semana?inicio=YYYY-MM-DD
    Espera dict: { "YYYY-MM-DD": [ {cita}, ... ], ... }
    """
    url = f"{get_backend_url()}/barberos/{id_barbero}/agenda/semana?inicio={lunes_str}"
    data, error = hacer_request(url, token=token)
    if error or not isinstance(data, dict):
        return {}
    return data

@app.route("/agenda")
def agenda():
    # Verificar sesiÃ³n
    if not session.get("token"):
        return redirect(url_for("login"))

    id_barbero    = session.get("id_usuario")
    barbero_nombre = session.get("usuario", {}).get("nombre", "Barbero")
    token         = session.get("token")

    # ParÃ¡metros de la URL
    vista     = request.args.get("vista", "dia")          # 'dia' | 'semana'
    fecha_str = request.args.get("fecha", date.today().isoformat())
    fecha_actual = parsear_fecha(fecha_str)

    # â”€â”€ VISTA DÃA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    if vista == "dia":
        fecha_anterior  = (fecha_actual - timedelta(days=1)).isoformat()
        fecha_siguiente = (fecha_actual + timedelta(days=1)).isoformat()
        fecha_label     = formatear_fecha_larga(fecha_actual)

        citas = obtener_citas_dia(id_barbero, fecha_str, token)

        return render_template(
            "peluqueros/agenda.html",
            barbero_nombre   = barbero_nombre,
            vista            = "dia",
            fecha_str        = fecha_str,
            fecha_anterior   = fecha_anterior,
            fecha_siguiente  = fecha_siguiente,
            fecha_label      = fecha_label,
            # semana (no usadas en vista dÃ­a pero evitan error de template)
            semana_inicio_label = "",
            semana_fin_label    = "",
            dias_semana         = [],
            citas               = citas,
        )

    # VISTA SEMANA
    lunes        = inicio_de_semana(fecha_actual)
    domingo      = lunes + timedelta(days=6)
    lunes_str    = lunes.isoformat()

    fecha_anterior  = (lunes - timedelta(weeks=1)).isoformat()
    fecha_siguiente = (lunes + timedelta(weeks=1)).isoformat()

    semana_inicio_label = formatear_fecha_corta(lunes)
    semana_fin_label    = formatear_fecha_corta(domingo)

    citas_por_dia = obtener_citas_semana(id_barbero, lunes_str, token)

    # Armar lista de 7 dÃ­as con sus citas
    dias_semana = []
    for i in range(7):
        dia = lunes + timedelta(days=i)
        dias_semana.append({
            "nombre_corto": DIAS_CORTOS[dia.weekday()],
            "fecha_label":  f"{dia.day} de {MESES_ES[dia.month]}",
            "citas":        citas_por_dia.get(dia.isoformat(), []),
        })

    return render_template(
        "peluqueros/agenda.html",
        barbero_nombre      = barbero_nombre,
        vista               = "semana",
        fecha_str           = lunes_str,
        fecha_anterior      = fecha_anterior,
        fecha_siguiente     = fecha_siguiente,
        semana_inicio_label = semana_inicio_label,
        semana_fin_label    = semana_fin_label,
        dias_semana         = dias_semana,
        fecha_label = "",
        citas       = [],
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
