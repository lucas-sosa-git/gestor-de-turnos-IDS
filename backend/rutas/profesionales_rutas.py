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

    turnos = conn.execute(
        """
        SELECT *
        FROM citas
        WHERE id_barbero = ?
        AND date(fecha) BETWEEN date(?) AND date(?)
        ORDER BY fecha ASC, hora ASC
        """,
        (id_barbero, desde, hasta)
    ).fetchall()

    conn.close()

    return jsonify([dict(turno) for turno in turnos]), 200


# GET /profesionales/1/turnos/5/cliente
@profesionales_bp.route("/profesionales/<int:id_barbero>/turnos/<int:id_cita>/cliente", methods=["GET"])
def ver_cliente(id_barbero, id_cita):
    conn = get_db_connection()

    cliente = conn.execute(
        """
        SELECT 
            u.id_usuarios,
            u.nombre,
            u.email,
            u.telefono
        FROM citas c
        JOIN usuarios u ON c.id_cliente = u.id_usuario
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