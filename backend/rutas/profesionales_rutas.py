from flask import Blueprint, jsonify, request
from db import get_db_connection

profesionales_bp = Blueprint("profesionales", __name__)


def obtener_barbero_por_usuario(cursor, id_usuario):
    cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_usuario = %s AND activo = 1',
        (id_usuario,)
    )
    return cursor.fetchone()


def finalizar_cita(cursor, cita):
    if cita["estado"] == "pendiente":
        return "Este turno todavia no fue confirmado por el cliente", 409

    if cita["estado"] == "cancelada":
        return "Este turno fue cancelado", 409

    if cita["estado"] == "completada":
        return "Este turno ya fue completado", 409

    cursor.execute(
        """
        UPDATE citas
        SET estado = 'completada'
        WHERE id_cita = %s
        """,
        (cita["id_cita"],)
    )
    return None, None


@profesionales_bp.route('/peluqueros/<int:id_usuario>', methods=['GET'])
def agenda_peluquero(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT nombre, id_usuario FROM usuarios WHERE id_usuario = %s',
        (id_usuario,)
    )
    usuario = cursor.fetchone()

    cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_usuario = %s',
        (id_usuario,)
    )
    barbero_reg = cursor.fetchone()
    id_barbero_destino = barbero_reg['id_barbero'] if barbero_reg else id_usuario

    cursor.execute('''
        SELECT c.id_cita, c.fecha, c.hora_inicio, c.estado,
               uc.nombre AS cliente_nombre,
               uc.email AS cliente_email,
               s.nombre AS servicio_nombre
        FROM citas c
        JOIN usuarios uc ON c.id_usuario = uc.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_barbero = %s
          AND c.estado IN ('confirmada', 'completada')
        ORDER BY c.fecha ASC, c.hora_inicio ASC
    ''', (id_barbero_destino,))
    turnos = cursor.fetchall()

    conn.close()

    return jsonify({
        "usuario": dict(usuario) if usuario else {"nombre": "Profesional"},
        "id_usuario": id_usuario,
        "id_barbero": id_barbero_destino,
        "turnos": [dict(turno) for turno in turnos]
    }), 200


@profesionales_bp.route("/check_in", methods=["POST"])
def check_in():
    data = request.get_json() or {}
    qr_token = data.get("qr_token")
    id_usuario_barbero = data.get("id_usuario_barbero")

    if not qr_token or not id_usuario_barbero:
        return jsonify({"error": "Faltan qr_token y el barbero autenticado"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    barbero = obtener_barbero_por_usuario(cursor, id_usuario_barbero)
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    cursor.execute(
        'SELECT * FROM citas WHERE qr_token = %s',
        (qr_token,)
    )
    cita = cursor.fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Codigo QR no valido"}), 404

    if cita["id_barbero"] != barbero["id_barbero"]:
        conn.close()
        return jsonify({"error": "Este codigo QR no corresponde a un turno de este barbero"}), 403

    error, status = finalizar_cita(cursor, cita)
    if error:
        conn.close()
        return jsonify({"error": error}), status

    conn.commit()

    cursor.execute('''
        SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
               u.nombre AS cliente,
               s.nombre AS servicio
        FROM citas c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.qr_token = %s
    ''', (qr_token,))
    cita_actualizada = cursor.fetchone()
    conn.close()

    return jsonify({"mensaje": "Turno completado", "cita": dict(cita_actualizada)}), 200


@profesionales_bp.route("/turnos/<int:id_cita>/finalizar", methods=["PATCH"])
def finalizar_turno(id_cita):
    data = request.get_json() or {}
    id_usuario_barbero = data.get("id_usuario_barbero")

    if not id_usuario_barbero:
        return jsonify({"error": "Falta el barbero autenticado"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    barbero = obtener_barbero_por_usuario(cursor, id_usuario_barbero)
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    cursor.execute(
        "SELECT * FROM citas WHERE id_cita = %s",
        (id_cita,)
    )
    cita = cursor.fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Turno no encontrado"}), 404

    if cita["id_barbero"] != barbero["id_barbero"]:
        conn.close()
        return jsonify({"error": "Este turno no pertenece a este barbero"}), 403

    error, status = finalizar_cita(cursor, cita)
    if error:
        conn.close()
        return jsonify({"error": error}), status

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Turno finalizado correctamente"}), 200
