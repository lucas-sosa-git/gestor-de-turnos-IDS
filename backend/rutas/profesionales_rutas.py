from flask import Blueprint, jsonify, request
from db import get_db_connection

profesionales_bp = Blueprint("profesionales", __name__)


# GET /profesionales/1/turnos?desde=2026-05-01&hasta=2026-05-31
@profesionales_bp.route("/profesionales/<int:id_barbero>/turnos", methods=["GET"])
def ver_turnos_periodo(id_barbero):
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    if not desde or not hasta:
        return jsonify({
            "error": "Tenés que enviar los parámetros 'desde' y 'hasta'. Ejemplo: /profesionales/1/turnos?desde=2026-05-01&hasta=2026-05-31"
        }), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    barbero = cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = ?', (id_barbero,)
    ).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    turnos = cursor.execute('''
        SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
               u.nombre AS cliente, s.nombre AS servicio
        FROM citas c
        JOIN usuarios u  ON c.id_usuario  = u.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_barbero = ?
          AND DATE(c.fecha) BETWEEN DATE(?) AND DATE(?)
        ORDER BY c.fecha ASC, c.hora_inicio ASC
    ''', (id_barbero, desde, hasta)).fetchall()

    conn.close()

    return jsonify([dict(turno) for turno in turnos]), 200


# GET /profesionales/1/turnos/5/cliente
@profesionales_bp.route("/profesionales/<int:id_barbero>/turnos/<int:id_cita>/cliente", methods=["GET"])
def ver_cliente(id_barbero, id_cita):
    conn = get_db_connection()
    cursor = conn.cursor()

    cliente = cursor.execute(
        """
        SELECT 
            u.id_usuario,
            u.nombre,
            u.email
        FROM citas c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        WHERE c.id_cita = ?
        AND c.id_barbero = ?
        """,
        (id_cita, id_barbero)
    ).fetchone()

    conn.close()

    if cliente is None:
        return jsonify({
            "error": "Cliente no encontrado o el turno no pertenece a este peluquero"
        }), 404

    return jsonify(dict(cliente)), 200


@profesionales_bp.route("/profesionales/check_in", methods=["POST"])
def check_in():
    data = request.get_json()
    qr_token = data.get("qr_token")
    id_barbero = data.get("id_barbero")

    if not qr_token or not id_barbero:
        return jsonify({"error": "Faltan los campos qr_token o id_barbero"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    barbero = cursor.execute('SELECT id_barbero FROM barberos WHERE id_barbero = ? AND activo = 1', (id_barbero,)).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404
    
    cita = cursor.execute('SELECT * FROM citas WHERE qr_token = ?', (qr_token,)).fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Código QR no válido"}), 404
    
    if cita["id_barbero"] != id_barbero:
        conn.close()
        return jsonify({"error": "Este código QR no corresponde a un turno de este barbero"}), 403
    
    if cita["estado"] == "cancelada":
        conn.close()
        return jsonify({"error": "Este turno fue cancelado"}), 400
    
    if cita["estado"] == "confirmada":
        conn.close()
        return jsonify({"error": "Este turno ya fue confirmado"}), 400
    
    cursor.execute('UPDATE citas SET estado = "completada" WHERE qr_token = ?', (qr_token,))
    conn.commit()

    cita_actualizada = cursor.execute('''
    SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado, u.nombre AS cliente, s.nombre AS servicio
    FROM citas c
    JOIN usuarios u ON c.id_usuario = u.id_usuario
    JOIN servicios s ON c.id_servicio = s.id_servicio
    WHERE c.qr_token = ?
''', (qr_token,)).fetchone()
    conn.close()

    return jsonify({"mensaje": "Asistencia confirmada", "cita": dict(cita_actualizada)}), 200