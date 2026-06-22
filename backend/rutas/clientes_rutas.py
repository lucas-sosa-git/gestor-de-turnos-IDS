from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import hashlib
import time

from flask import Blueprint, jsonify, request

from db import get_db_connection
from mail_service import enviar_mail

clientes_bp = Blueprint('clientes', __name__)

try:
    ARGENTINA_TZ = ZoneInfo("America/Argentina/Buenos_Aires")
except ZoneInfoNotFoundError:
    ARGENTINA_TZ = timezone(timedelta(hours=-3))


def normalizar_hora(valor):
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(valor, formato).time()
        except (TypeError, ValueError):
            continue

    return None


def hora_texto(valor):
    hora = normalizar_hora(valor)
    return hora.strftime("%H:%M:%S") if hora else None


def dia_semana_bd(fecha):
    return (fecha.weekday() + 1) % 7


@clientes_bp.route('/', methods=['POST'])
def registrar_cliente():
    nuevo_cliente = request.get_json() or {}
    nombre = nuevo_cliente.get('nombre')
    email = nuevo_cliente.get('email')
    clave = nuevo_cliente.get('clave')

    if not nombre or not email or not clave:
        return jsonify({"error": "nombre, email y clave son obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_usuario FROM usuarios WHERE email = %s',
        (email,)
    )
    existe = cursor.fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "Ya existe un usuario con ese email"}), 409

    try:
        cursor.execute(
            'INSERT INTO usuarios (nombre, email, clave, rol) VALUES (%s, %s, %s, %s)',
            (nombre, email, hashlib.sha256(clave.encode()).hexdigest(), "cliente")
        )
        id_usuario = cursor.lastrowid
        conn.commit()

        cursor.execute(
            'SELECT id_usuario, nombre, email, rol FROM usuarios WHERE id_usuario = %s',
            (id_usuario,)
        )
        cliente = cursor.fetchone()
        return jsonify(dict(cliente)), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    finally:
        conn.close()


@clientes_bp.route('/servicios/<int:id_usuario>', methods=['GET'])
def mostrar_servicios_cliente(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM usuarios WHERE id_usuario = %s',
        (id_usuario,)
    )
    usuario = cursor.fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    cursor.execute('''
        SELECT id_cita
        FROM citas
        WHERE id_usuario = %s
          AND estado NOT IN ('cancelada', 'completada')
    ''', (id_usuario,))
    turnos = cursor.fetchall()
    cursor.execute('''
        SELECT id_servicio, nombre, descripcion, duracion, precio, img_servicio
        FROM servicios
        ORDER BY nombre ASC
    ''')
    servicios = cursor.fetchall()
    conn.close()

    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "servicios": [dict(servicio) for servicio in servicios],
        "turnos": [dict(turno) for turno in turnos]
    }), 200


@clientes_bp.route('/barberos/<int:id_usuario>', methods=['GET'])
def mostrar_barberos(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM usuarios WHERE id_usuario = %s',
        (id_usuario,)
    )
    usuario = cursor.fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    cursor.execute('''
        SELECT b.id_barbero, u.nombre, u.email, b.activo, b.img_barbero
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        WHERE b.activo = 1
    ''')
    barberos = cursor.fetchall()
    cursor.execute('''
        SELECT id_cita
        FROM citas
        WHERE id_usuario = %s
          AND estado NOT IN ('cancelada', 'completada')
    ''', (id_usuario,))
    turnos = cursor.fetchall()
    conn.close()

    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "barberos": [dict(barbero) for barbero in barberos],
        "turnos": [dict(turno) for turno in turnos]
    }), 200


@clientes_bp.route('/panel/<int:id_usuario>', methods=['GET'])
def panel_cliente(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT nombre, id_usuario FROM usuarios WHERE id_usuario = %s',
        (id_usuario,)
    )
    usuario = cursor.fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    cursor.execute('''
        SELECT c.id_cita, c.id_barbero, c.fecha, c.hora_inicio, c.estado,
               ub.nombre AS barbero_nombre,
               s.nombre AS servicio_nombre
        FROM citas c
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_usuario = %s
          AND c.estado != 'cancelada'
        ORDER BY
          CASE WHEN c.estado = 'completada' THEN 1 ELSE 0 END,
          c.fecha ASC,
          c.hora_inicio ASC
    ''', (id_usuario,))
    turnos = cursor.fetchall()
    conn.close()

    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "turnos": [dict(turno) for turno in turnos]
    }), 200


@clientes_bp.route('/acerca-de/<int:id_usuario>', methods=['GET'])
def acerca_de(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM usuarios WHERE id_usuario = %s',
        (id_usuario,)
    )
    usuario = cursor.fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    cursor.execute('''
        SELECT id_cita
        FROM citas
        WHERE id_usuario = %s
          AND estado NOT IN ('cancelada', 'completada')
    ''', (id_usuario,))
    turnos = cursor.fetchall()
    conn.close()

    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "turnos": [dict(turno) for turno in turnos]
    }), 200


@clientes_bp.route('/barberos/<int:id_barbero>/horarios', methods=['GET'])
def mostrar_horarios_barbero(id_barbero):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = %s AND activo = 1',
        (id_barbero,)
    )
    barbero = cursor.fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    cursor.execute(
        'SELECT * FROM disponibilidad_barberos WHERE id_barbero = %s',
        (id_barbero,)
    )
    disponibilidad = cursor.fetchall()

    cursor.execute('''
        SELECT fecha, hora_inicio, hora_fin, estado
        FROM citas
        WHERE id_barbero = %s
          AND fecha >= CURRENT_DATE
          AND estado NOT IN ('cancelada', 'completada')
        ORDER BY fecha, hora_inicio
    ''', (id_barbero,))
    citas_ocupadas = cursor.fetchall()

    conn.close()
    return jsonify({
        "disponibilidad": [dict(d) for d in disponibilidad],
        "citas_ocupadas": [dict(c) for c in citas_ocupadas]
    }), 200


@clientes_bp.route('/turnos/<int:id_cita>', methods=['DELETE'])
def cancelar_turno(id_cita):
    data = request.get_json() or {}
    id_usuario = data.get('id_usuario')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT estado FROM citas WHERE id_cita = %s AND id_usuario = %s',
        (id_cita, id_usuario)
    )
    cita = cursor.fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Turno no encontrado o no pertenece al cliente"}), 404

    if cita['estado'] in ('cancelada', 'completada'):
        conn.close()
        return jsonify({"error": "Este turno no se puede cancelar"}), 409

    cursor.execute('''
        UPDATE citas
        SET estado = 'cancelada', fecha_cancelacion = CURRENT_TIMESTAMP
        WHERE id_cita = %s AND id_usuario = %s
    ''', (id_cita, id_usuario))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Turno cancelado correctamente"}), 200


@clientes_bp.route('/turnos', methods=['POST'])
def reservar_turno():
    data = request.get_json() or {}
    id_usuario = data.get('id_usuario')
    id_barbero = data.get('id_barbero')
    id_servicio = data.get('id_servicio')
    fecha = str(data.get('fecha', '')).strip()
    hora_inicio = str(data.get('hora_inicio', '')).strip()
    frontend_url = str(data.get('frontend_url') or '').strip().rstrip("/")
    if frontend_url and not frontend_url.startswith(("http://", "https://")):
        frontend_url = ""

    if not id_usuario or not id_barbero or not id_servicio or not fecha or not hora_inicio:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    try:
        fecha_turno = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "La fecha debe tener formato AAAA-MM-DD"}), 400

    hora_inicio_obj = normalizar_hora(hora_inicio)
    if not hora_inicio_obj:
        return jsonify({"error": "La hora debe tener formato HH:MM"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_usuario FROM usuarios WHERE id_usuario = %s AND rol = "cliente"',
        (id_usuario,)
    )
    cliente = cursor.fetchone()
    if not cliente:
        conn.close()
        return jsonify({"error": "Cliente no encontrado"}), 404

    cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = %s AND activo = 1',
        (id_barbero,)
    )
    barbero = cursor.fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado o inactivo"}), 404

    cursor.execute(
        'SELECT id_servicio, duracion FROM servicios WHERE id_servicio = %s',
        (id_servicio,)
    )
    servicio = cursor.fetchone()
    if not servicio:
        conn.close()
        return jsonify({"error": "Servicio no encontrado"}), 404

    inicio_dt = datetime.combine(fecha_turno, hora_inicio_obj)
    hora_fin = (inicio_dt + timedelta(minutes=servicio['duracion'])).strftime("%H:%M:%S")
    hora_inicio = hora_inicio_obj.strftime("%H:%M:%S")

    ahora_argentina = datetime.now(ARGENTINA_TZ)
    inicio_argentina = datetime.combine(
        fecha_turno,
        hora_inicio_obj,
        tzinfo=ARGENTINA_TZ
    )

    if fecha_turno < ahora_argentina.date():
        conn.close()
        return jsonify({"error": "No se puede reservar en una fecha pasada"}), 400

    if inicio_argentina <= ahora_argentina:
        conn.close()
        return jsonify({"error": "No se puede reservar en un horario que ya paso"}), 400

    cursor.execute('''
        SELECT hora_inicio, hora_fin
        FROM disponibilidad_barberos
        WHERE id_barbero = %s
          AND dia_semana = %s
    ''', (id_barbero, dia_semana_bd(fecha_turno)))
    disponibilidad = cursor.fetchall()

    turno_en_horario = any(
        hora_texto(d['hora_inicio']) <= hora_inicio and hora_fin <= hora_texto(d['hora_fin'])
        for d in disponibilidad
        if hora_texto(d['hora_inicio']) and hora_texto(d['hora_fin'])
    )
    if not turno_en_horario:
        conn.close()
        return jsonify({"error": "El barbero no atiende en ese dia u horario"}), 400

    cursor.execute('''
        SELECT id_cita
        FROM citas
        WHERE id_barbero = %s
          AND fecha = %s
          AND estado NOT IN ('cancelada', 'completada')
          AND time(hora_inicio) < time(%s)
          AND time(hora_fin) > time(%s)
    ''', (id_barbero, fecha, hora_fin, hora_inicio))
    conflicto = cursor.fetchone()
    if conflicto:
        conn.close()
        return jsonify({"error": "Ese horario ya esta ocupado para el barbero"}), 409

    qr_token = hashlib.sha256(
        f"{id_usuario}{id_barbero}{fecha}{hora_inicio}{time.time()}".encode()
    ).hexdigest()

    cursor.execute('''
        INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', %s)
    ''', (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, qr_token))
    id_cita = cursor.lastrowid
    conn.commit()

    cursor.execute('''
        SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
               u.nombre AS cliente,
               u.email AS cliente_email,
               ub.nombre AS barbero,
               s.nombre AS servicio
        FROM citas c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_cita = %s
    ''', (id_cita,))
    cita = cursor.fetchone()
    conn.close()

    mail_enviado = enviar_mail(
        destinatario=cita['cliente_email'],
        nombre=cita['cliente'],
        fecha=cita['fecha'],
        hora=cita['hora_inicio'],
        barbero=cita['barbero'],
        servicio=cita['servicio'],
        qr_token=qr_token,
        id_cita=id_cita,
        frontend_url=frontend_url
    )

    respuesta = dict(cita)
    respuesta["mail_enviado"] = mail_enviado

    return jsonify(respuesta), 201


@clientes_bp.route('/resenias', methods=['POST'])
def dejar_resenia():
    data = request.get_json() or {}
    id_usuario = data.get('id_usuario')
    id_barbero = data.get('id_barbero')
    id_cita = data.get('id_cita')
    calificacion = data.get('calificacion')
    comentario = data.get('comentario')

    if not id_usuario or not id_barbero or not id_cita or not calificacion:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_usuario FROM usuarios WHERE id_usuario = %s AND rol = "cliente"',
        (id_usuario,)
    )
    cliente = cursor.fetchone()
    if not cliente:
        conn.close()
        return jsonify({"error": "Cliente no encontrado"}), 404

    cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = %s AND activo = 1',
        (id_barbero,)
    )
    barbero = cursor.fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    try:
        calificacion = int(calificacion)
    except (TypeError, ValueError):
        conn.close()
        return jsonify({"error": "La calificacion debe ser un numero entero entre 1 y 5"}), 400

    if calificacion < 1 or calificacion > 5:
        conn.close()
        return jsonify({"error": "La calificacion debe ser un numero entero entre 1 y 5"}), 400

    cursor.execute('''
        SELECT id_cita
        FROM citas
        WHERE id_cita = %s
          AND id_usuario = %s
          AND id_barbero = %s
          AND estado = 'completada'
    ''', (id_cita, id_usuario, id_barbero))
    cita = cursor.fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Cita no encontrada, no pertenece al cliente o no esta completada"}), 404

    cursor.execute(
        'SELECT id_resenia FROM resenias WHERE id_usuario = %s AND id_cita = %s',
        (id_usuario, id_cita)
    )
    resenia_existente = cursor.fetchone()
    if resenia_existente:
        conn.close()
        return jsonify({"error": "Ya has dejado una resenia para esta cita"}), 409

    cursor.execute(
        'INSERT INTO resenias (id_usuario, id_cita, calificacion, comentario) VALUES (%s, %s, %s, %s)',
        (id_usuario, id_cita, calificacion, comentario)
    )
    id_resenia = cursor.lastrowid
    conn.commit()

    cursor.execute(
        'SELECT * FROM resenias WHERE id_resenia = %s',
        (id_resenia,)
    )
    resenia = cursor.fetchone()
    conn.close()

    return jsonify({"message": "Resenia subida correctamente", "resenia": dict(resenia)}), 201


@clientes_bp.route('/turnos/confirmar/<qr_token>', methods=['GET', 'PATCH'])
def confirmar_turno(qr_token):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_cita, estado FROM citas WHERE qr_token = %s',
        (qr_token,)
    )
    cita = cursor.fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Turno no encontrado"}), 404

    if cita["estado"] == "cancelada":
        conn.close()
        return jsonify({"error": "Este turno fue cancelado"}), 409

    if cita["estado"] == "completada":
        conn.close()
        return jsonify({"error": "Este turno ya fue completado"}), 409

    if cita["estado"] == "confirmada":
        cursor.execute('''
            SELECT c.id_cita, c.id_usuario, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
                   u.nombre AS cliente,
                   ub.nombre AS barbero,
                   s.nombre AS servicio
            FROM citas c
            JOIN usuarios u ON c.id_usuario = u.id_usuario
            JOIN barberos b ON c.id_barbero = b.id_barbero
            JOIN usuarios ub ON b.id_usuario = ub.id_usuario
            JOIN servicios s ON c.id_servicio = s.id_servicio
            WHERE c.id_cita = %s
        ''', (cita["id_cita"],))
        cita_confirmada = cursor.fetchone()
        conn.close()
        return jsonify({
            "mensaje": "El turno ya estaba confirmado",
            "cita": dict(cita_confirmada)
        }), 200

    cursor.execute(
        "UPDATE citas SET estado = 'confirmada' WHERE qr_token = %s",
        (qr_token,)
    )
    conn.commit()

    cursor.execute('''
        SELECT c.id_cita, c.id_usuario, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
               u.nombre AS cliente,
               ub.nombre AS barbero,
               s.nombre AS servicio
        FROM citas c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.qr_token = %s
    ''', (qr_token,))
    cita_confirmada = cursor.fetchone()
    conn.close()

    return jsonify({
        "mensaje": "Turno confirmado correctamente",
        "cita": dict(cita_confirmada)
    }), 200
