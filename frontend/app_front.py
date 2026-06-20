import json
import os
import requests
import jwt
from datetime import datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from flask import Flask, g, redirect, render_template, request, session, url_for, jsonify

try:
    from jwt import ExpiredSignatureError, InvalidTokenError
except ImportError:
    from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


app = Flask(__name__, template_folder="templates", static_folder="statics")
app.secret_key = "clave_front_tp_barberia"

JWT_SECRET = os.environ.get("JWT_SECRET", "clave_secreta_tp_barberia")
JWT_ALGORITHM = "HS256"

ROLES_ADMIN = {"admin", "administrador"}
ROLES_CLIENTE = {"cliente"}
ROLES_BARBERO = {"barbero", "peluquero", "profesional"}


def validar_token_session():
    token = session.get("token")
    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        usuario_id = int(payload["usuario_id"])
        rol = str(payload["rol"]).lower()
    except (ExpiredSignatureError, InvalidTokenError, KeyError, TypeError, ValueError):
        session.clear()
        return None

    session["id_usuario"] = usuario_id
    session["rol"] = rol

    return {
        "id_usuario": usuario_id,
        "rol": rol,
        "usuario": session.get("usuario", {})
    }


def redirigir_por_rol(usuario_actual):
    rol = usuario_actual.get("rol")
    id_usuario = usuario_actual.get("id_usuario")

    if rol in ROLES_ADMIN:
        return redirect("/admin")

    if rol in ROLES_CLIENTE:
        return redirect(f"/clientes/{id_usuario}")

    if rol in ROLES_BARBERO:
        return redirect(f"/panel_peluquero/{id_usuario}")

    session.clear()
    return redirect("/login")


def es_redireccion_local(destino):
    if not destino:
        return False

    partes = urlparse(destino)
    return not partes.netloc and partes.path.startswith("/")


def redirect_login_actual():
    destino = request.full_path if request.query_string else request.path
    return redirect(url_for("login", next=destino))


def obtener_id_desde_path(indice):
    partes = request.path.strip("/").split("/")

    try:
        return int(partes[indice])
    except (IndexError, TypeError, ValueError):
        return None


@app.before_request
def proteger_vistas_privadas():
    if request.endpoint == "static":
        return None

    if request.path in {"/", "/login"}:
        usuario_actual = validar_token_session()
        if usuario_actual:
            g.usuario_actual = usuario_actual
            destino = request.args.get("next")
            if request.path == "/login" and es_redireccion_local(destino):
                return redirect(destino)
            return redirigir_por_rol(usuario_actual)
        return None

    if (
        request.path in {"/register", "/logout"}
        or request.path.startswith("/confirmar/")
        or request.path.startswith("/cancelar/")
    ):
        return None

    usuario_actual = validar_token_session()
    if not usuario_actual:
        return redirect_login_actual()

    g.usuario_actual = usuario_actual
    path = request.path
    rol = usuario_actual["rol"]
    id_usuario_token = usuario_actual["id_usuario"]

    if path.startswith("/admin"):
        if rol not in ROLES_ADMIN:
            return redirigir_por_rol(usuario_actual)
        return None

    if path.startswith("/clientes/"):
        id_usuario_url = obtener_id_desde_path(1)
        if rol not in ROLES_CLIENTE or id_usuario_url != id_usuario_token:
            return redirigir_por_rol(usuario_actual)
        return None

    if path.startswith("/panel_peluquero/"):
        id_usuario_url = obtener_id_desde_path(1)
        if rol not in ROLES_BARBERO or id_usuario_url != id_usuario_token:
            return redirigir_por_rol(usuario_actual)
        return None

    if path.startswith("/qr/"):
        if rol not in ROLES_BARBERO:
            return redirigir_por_rol(usuario_actual)
        return None

    return None


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


def obtener_servicios_cliente(id_usuario):
    return obtener_json_backend(
        f"/clientes/servicios/{id_usuario}",
        "No se pudieron cargar los servicios"
    )


def obtener_horarios_barbero(id_barbero):
    return obtener_json_backend(
        f"/clientes/barberos/{id_barbero}/horarios",
        "No se pudieron cargar los horarios del barbero"
    )


def obtener_info_cliente(id_usuario):
    return obtener_json_backend(
        f"/clientes/acerca-de/{id_usuario}",
        "No se pudo cargar la informacion del cliente"
    )


def obtener_mensaje_turno():
    if request.args.get("turno") == "cancelado":
        return "Turno cancelado correctamente."

    return None

@app.route("/")
def inicio():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "GET":
        exito = None

        if request.args.get("registro") == "ok":
            exito = "Cuenta creada correctamente. Ya podés iniciar sesión."

        return render_template("login.html", exito=exito, next_url=next_url)

    email = request.form.get("email", "").strip()
    clave = request.form.get("clave", "").strip()

    if not email or not clave:
        return render_template(
            "login.html",
            error="Complete email y contraseña.",
            next_url=next_url
        )

    ok, usuario, token, error = login_en_backend(email, clave)

    if not ok:
        return render_template(
            "login.html",
            error=error,
            email=email,
            next_url=next_url
        )

    session["token"] = token
    session["usuario"] = usuario
    session["id_usuario"] = usuario.get("id_usuario")
    session["rol"] = usuario.get("rol")

    rol = usuario.get("rol", "").lower()

    if es_redireccion_local(next_url):
        return redirect(next_url)

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
        error=f"Rol no reconocido: {rol}",
        next_url=next_url
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/clientes/<int:id_usuario>")
def clientes_panel(id_usuario):
    usuario = session.get("usuario")

    data, error = obtener_panel_cliente(id_usuario)
    if data:
        usuario = data.get("usuario", usuario)

    return render_template(
        "feature_clientes/clientes.html",
        usuario=usuario,
        id_usuario=id_usuario,
        turnos=data.get("turnos", []) if data else [],
        error=error or request.args.get("error"),
        exito=obtener_mensaje_turno()
    )


@app.route("/clientes/<int:id_usuario>/barberos")
def clientes_barberos(id_usuario):
    usuario = session.get("usuario")

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


@app.route("/clientes/<int:id_usuario>/servicios")
def clientes_servicios(id_usuario):
    usuario = session.get("usuario")

    data, error = obtener_servicios_cliente(id_usuario)
    if data:
        usuario = data.get("usuario", usuario)

    return render_template(
        "feature_clientes/servicios.html",
        usuario=usuario,
        id_usuario=id_usuario,
        servicios=data.get("servicios", []) if data else [],
        turnos=data.get("turnos", []) if data else [],
        error=error
    )


@app.route("/clientes/<int:id_usuario>/info")
def clientes_info(id_usuario):
    usuario = session.get("usuario")

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
@app.route("/clientes/<int:id_usuario>/reservar/<int:id_barbero>", methods=["GET", "POST"])
def reservar_turno_form(id_usuario, id_barbero):
    usuario = session.get("usuario")

    if request.method == "GET":
        data, error = obtener_servicios_cliente(id_usuario)
        horarios_data, horarios_error = obtener_horarios_barbero(id_barbero)
        servicios = data.get("servicios", []) if data else []

        return render_template(
            "feature_clientes/reservar_turno.html",
            usuario=usuario,
            id_usuario=id_usuario,
            id_barbero=id_barbero,
            servicios=servicios,
            disponibilidad=horarios_data.get("disponibilidad", []) if horarios_data else [],
            citas_ocupadas=horarios_data.get("citas_ocupadas", []) if horarios_data else [],
            fecha_min=datetime.now().strftime("%Y-%m-%d"),
            error=error or horarios_error
        )

    payload = {
        "id_usuario": id_usuario,
        "id_barbero": id_barbero,
        "id_servicio": request.form.get("id_servicio"),
        "fecha": request.form.get("fecha"),
        "hora_inicio": request.form.get("hora_inicio"),
        "frontend_url": request.host_url.rstrip("/"),
    }

    try:
        respuesta = requests.post(
            f"{get_backend_url()}/clientes/turnos",
            json=payload,
            timeout=10
        )
        data = respuesta.json()
    except requests.RequestException:
        servicios_data, _ = obtener_servicios_cliente(id_usuario)
        horarios_data, _ = obtener_horarios_barbero(id_barbero)
        return render_template(
            "feature_clientes/reservar_turno.html",
            usuario=usuario,
            id_usuario=id_usuario,
            id_barbero=id_barbero,
            servicios=servicios_data.get("servicios", []) if servicios_data else [],
            disponibilidad=horarios_data.get("disponibilidad", []) if horarios_data else [],
            citas_ocupadas=horarios_data.get("citas_ocupadas", []) if horarios_data else [],
            fecha_min=datetime.now().strftime("%Y-%m-%d"),
            error="No se pudo conectar con el backend."
        )
    except ValueError:
        servicios_data, _ = obtener_servicios_cliente(id_usuario)
        horarios_data, _ = obtener_horarios_barbero(id_barbero)
        return render_template(
            "feature_clientes/reservar_turno.html",
            usuario=usuario,
            id_usuario=id_usuario,
            id_barbero=id_barbero,
            servicios=servicios_data.get("servicios", []) if servicios_data else [],
            disponibilidad=horarios_data.get("disponibilidad", []) if horarios_data else [],
            citas_ocupadas=horarios_data.get("citas_ocupadas", []) if horarios_data else [],
            fecha_min=datetime.now().strftime("%Y-%m-%d"),
            error="El backend devolvio una respuesta invalida."
        )

    if respuesta.status_code >= 400:
        servicios_data, _ = obtener_servicios_cliente(id_usuario)
        horarios_data, _ = obtener_horarios_barbero(id_barbero)
        return render_template(
            "feature_clientes/reservar_turno.html",
            usuario=usuario,
            id_usuario=id_usuario,
            id_barbero=id_barbero,
            servicios=servicios_data.get("servicios", []) if servicios_data else [],
            disponibilidad=horarios_data.get("disponibilidad", []) if horarios_data else [],
            citas_ocupadas=horarios_data.get("citas_ocupadas", []) if horarios_data else [],
            fecha_min=datetime.now().strftime("%Y-%m-%d"),
            error=data.get("error") or "No se pudo reservar el turno."
        )

    return render_template(
        "feature_clientes/reserva_confirmada.html",
        usuario=usuario,
        id_usuario=id_usuario,
        reserva=data,
        mail_enviado=data.get("mail_enviado")
    )
@app.route("/procesar_reserva_frontend", methods=['POST'])
def crear_reserva_proxy():
    data = request.get_json()
    url_backend = "http://127.0.0.1:5000/clientes/turnos" 
    try:
        print("\n" + "="*50)
        print(">>> 1. ENVIANDO DATOS AL BACKEND:", data)
        
        respuesta_backend = requests.post(url_backend, json=data)
        
        print(f">>> 2. EL BACKEND RESPONDIÓ CON CÓDIGO: {respuesta_backend.status_code}")
        
        try:
            json_response = respuesta_backend.json()
            print(">>> 3. LECTURA EXITOSA. Devolviendo al navegador...")
            print("="*50 + "\n")
            return jsonify(json_response), respuesta_backend.status_code
            
        except ValueError:
            print(">>> ¡ALERTA ROJA! El backend no devolvió JSON. Devolvió este código de error:")
            print(respuesta_backend.text)
            print("="*50 + "\n")
            return jsonify({
                "error": f"Falla en el backend (Código {respuesta_backend.status_code}). Revisá la consola negra del Frontend para leer el problema real."
            }), 500
    except requests.exceptions.RequestException as e:
        print(">>> ERROR CRÍTICO DE CONEXIÓN:", e)
        return jsonify({"error": "El servidor Backend (puerto 5000) está apagado o no responde."}), 500


# ─── RUTA PARA MOSTRAR LA PANTALLA DE RESEÑA ───
@app.route("/clientes/<int:id_usuario>/resenia/<int:id_cita>/<int:id_barbero>")
def dejar_resenia_form(id_usuario, id_cita, id_barbero):
    return render_template(
        "feature_clientes/dejar_resenia.html",
        id_usuario=id_usuario,
        id_cita=id_cita,
        id_barbero=id_barbero
    )
@app.route("/procesar_resenia_frontend", methods=['POST'])
def crear_resenia_proxy():
    data = request.get_json()
    url_backend = "http://127.0.0.1:5000/clientes/resenias" 
    
    try:
        respuesta_backend = requests.post(url_backend, json=data)
        
        try:
            return jsonify(respuesta_backend.json()), respuesta_backend.status_code
        except ValueError:
            print(">>> ERROR: El backend devolvió HTML en vez de JSON.")
            return jsonify({
                "error": f"Falla en el backend (Código {respuesta_backend.status_code}). Revisá la consola."
            }), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "El servidor Backend (puerto 5000) no responde."}), 500
    


@app.route("/clientes/<int:id_usuario>/turnos/<int:id_cita>/cancelar", methods=["POST"])
def cancelar_turno_front(id_usuario, id_cita):
    try:
        respuesta = requests.delete(
            f"{get_backend_url()}/clientes/turnos/{id_cita}",
            json={"id_usuario": id_usuario},
            timeout=10
        )
        data = respuesta.json()
    except requests.RequestException:
        return redirect(url_for(
            "clientes_panel",
            id_usuario=id_usuario,
            error="No se pudo conectar con el backend."
        ))
    except ValueError:
        return redirect(url_for(
            "clientes_panel",
            id_usuario=id_usuario,
            error="El backend devolvio una respuesta invalida."
        ))

    if respuesta.status_code >= 400:
        return redirect(url_for(
            "clientes_panel",
            id_usuario=id_usuario,
            error=data.get("error") or "No se pudo cancelar el turno."
        ))

    return redirect(url_for("clientes_panel", id_usuario=id_usuario, turno="cancelado"))

def obtener_panel_peluqueros(id_usuario):
    return obtener_json_backend(
        f"/profesionales/peluqueros/{id_usuario}",
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


def formatear_hora(hora):
    if not hora:
        return ""

    return str(hora).split(".")[0][:5]


def formatear_horas_turnos(turnos):
    for turno in turnos:
        turno["hora_inicio_label"] = formatear_hora(turno.get("hora_inicio"))

    return turnos


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
    lista_total_citas = formatear_horas_turnos(lista_total_citas)
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
        error = error or request.args.get("error"),
        exito = "Turno completado correctamente." if request.args.get("turno") == "completado" else None,
        vista = vista_actual,
        fecha_str = fecha_str_actual,
        fecha_anterior = fecha_anterior,
        fecha_siguiente = fecha_siguiente,
        fecha_label = fecha_label,
        semana_inicio_label = semana_inicio_label,
        semana_fin_label = semana_fin_label
    )


@app.route("/panel_peluquero/<int:id_usuario>/turnos/<int:id_cita>/finalizar", methods=["POST"])
def finalizar_turno_front(id_usuario, id_cita):
    try:
        respuesta = requests.patch(
            f"{get_backend_url()}/profesionales/turnos/{id_cita}/finalizar",
            json={"id_usuario_barbero": id_usuario},
            timeout=10
        )
        data = respuesta.json()
    except requests.RequestException:
        return redirect(url_for(
            "panel_peluquero",
            id_usuario=id_usuario,
            error="No se pudo conectar con el backend."
        ))
    except ValueError:
        return redirect(url_for(
            "panel_peluquero",
            id_usuario=id_usuario,
            error="El backend devolvio una respuesta invalida."
        ))

    if respuesta.status_code >= 400:
        return redirect(url_for(
            "panel_peluquero",
            id_usuario=id_usuario,
            error=data.get("error") or "No se pudo finalizar el turno."
        ))

    return redirect(url_for(
        "panel_peluquero",
        id_usuario=id_usuario,
        turno="completado"
    ))


@app.route("/qr/<qr_token>")
def validar_qr(qr_token):
    id_usuario = session.get("id_usuario")

    try:
        respuesta = requests.post(
            f"{get_backend_url()}/profesionales/check_in",
            json={
                "qr_token": qr_token,
                "id_usuario_barbero": id_usuario
            },
            timeout=10
        )
        data = respuesta.json()
    except requests.RequestException:
        return render_template(
            "qr_resultado.html",
            ok=False,
            mensaje="No se pudo conectar con el backend."
        )
    except ValueError:
        return render_template(
            "qr_resultado.html",
            ok=False,
            mensaje="El backend devolvio una respuesta invalida."
        )

    if respuesta.status_code >= 400:
        return render_template(
            "qr_resultado.html",
            ok=False,
            mensaje=data.get("error") or "No se pudo validar el QR."
        )

    cita = data.get("cita", {})
    cita["hora_inicio_label"] = formatear_hora(cita.get("hora_inicio"))

    return render_template(
        "qr_resultado.html",
        ok=True,
        mensaje=data.get("mensaje") or "Turno completado",
        cita=cita,
        id_usuario=id_usuario
    )


@app.route("/confirmar/<qr_token>")
def confirmar_turno_mail(qr_token):
    try:
        respuesta = requests.get(
            f"{get_backend_url()}/clientes/turnos/confirmar/{qr_token}",
            timeout=10
        )
        data = respuesta.json()
    except requests.RequestException:
        return render_template(
            "confirmacion_turno.html",
            ok=False,
            mensaje="No se pudo conectar con el backend."
        )
    except ValueError:
        return render_template(
            "confirmacion_turno.html",
            ok=False,
            mensaje="El backend devolvio una respuesta invalida."
        )

    if respuesta.status_code >= 400:
        return render_template(
            "confirmacion_turno.html",
            ok=False,
            mensaje=data.get("error") or "No se pudo confirmar el turno."
        )

    cita = data.get("cita", {})
    cita["hora_inicio_label"] = formatear_hora(cita.get("hora_inicio"))

    return render_template(
        "confirmacion_turno.html",
        ok=True,
        mensaje=data.get("mensaje") or "Turno confirmado correctamente",
        cita=cita,
        id_usuario=cita.get("id_usuario")
    )


@app.route("/cancelar/<int:id_cita>")
def cancelar_turno_mail(id_cita):
    try:
        respuesta = requests.get(
            f"{get_backend_url()}/cancelar/{id_cita}",
            timeout=10
        )
    except requests.RequestException:
        return render_template(
            "cancelacion_exitosa.html",
            ok=False,
            mensaje="No se pudo conectar con el backend."
        )

    if respuesta.status_code >= 400:
        return render_template(
            "cancelacion_exitosa.html",
            ok=False,
            mensaje="No se pudo cancelar el turno."
        )

    return render_template(
        "cancelacion_exitosa.html",
        ok=True,
        mensaje="Turno cancelado correctamente."
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
    "crear_barbero": "No se pudo crear el barbero.",
    "editar_barbero": "No se pudo editar el barbero",
    "eliminar_barbero": "No se pudo eliminar el barbero.",
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

# ABM BARBERO

@app.route("/admin/barberos/crear", methods=["POST"])
def crear_barbero_front():
    nombre = request.form.get("nombre", "").strip()
    email  = request.form.get("email", "").strip()
    clave  = request.form.get("clave", "").strip()
    imagen = request.files.get("imagen")

    data = {
        "nombre": nombre,
        "email":  email,
        "clave":  clave
    }

    files = None
    if imagen and imagen.filename:
        files = {
            "imagen": (imagen.filename, imagen.stream, imagen.mimetype)
        }

    try:
        response = requests.post(
            f"{get_backend_url()}/admin/barberos",
            data=data,
            files=files,
            timeout=10
        )

        if response.status_code >= 400:
            mensaje = mensaje_error_backend(response, "No se pudo crear el barbero.")
            return redirect_admin_error(mensaje)

    except requests.RequestException:
        return redirect_admin_error("backend")

    return redirect("/admin")


@app.route("/admin/barberos/<int:id_barbero>/editar", methods=["POST"])
def editar_barbero_front(id_barbero):
    nombre = request.form.get("nombre", "").strip()
    imagen = request.files.get("imagen")

    data = {"nombre": nombre}

    files = None
    if imagen and imagen.filename:
        files = {
            "imagen": (imagen.filename, imagen.stream, imagen.mimetype)
        }

    try:
        response = requests.patch(
            f"{get_backend_url()}/admin/barberos/{id_barbero}",
            data=data,
            files=files,
            timeout=10
        )

        if response.status_code >= 400:
            mensaje = mensaje_error_backend(response, "No se pudo editar el barbero.")
            return redirect_admin_error(mensaje)

    except requests.RequestException:
        return redirect_admin_error("backend")

    return redirect("/admin")


@app.route("/admin/barberos/<int:id_barbero>/eliminar", methods=["POST"])
def eliminar_barbero_front(id_barbero):
    try:
        response = requests.delete(
            f"{get_backend_url()}/admin/barberos/{id_barbero}",
            timeout=10
        )

        if response.status_code >= 400:
            mensaje = mensaje_error_backend(response, "No se pudo eliminar el barbero.")
            return redirect_admin_error(mensaje)

    except requests.RequestException:
        return redirect_admin_error("backend")

    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
