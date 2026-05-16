from flask import Blueprint, jsonify, request
from db import get_db_connection

profesionales_bp = Blueprint("profesionales", __name__)


# GET /profesionales/1/turnos?desde=2026-05-01&hasta=2026-05-31
@profesionales_bp.route("/profesionales/<int:id_peluquero>/turnos", methods=["GET"])
def ver_turnos_periodo(id_peluquero):
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
        FROM turnos
        WHERE id_peluquero = ?
        AND date(fecha_hora) BETWEEN date(?) AND date(?)
        ORDER BY fecha_hora ASC
        """,
        (id_peluquero, desde, hasta)
    ).fetchall()

    conn.close()

    return jsonify([dict(turno) for turno in turnos]), 200


# GET /profesionales/1/turnos/5/cliente
@profesionales_bp.route("/profesionales/<int:id_peluquero>/turnos/<int:id_turno>/cliente", methods=["GET"])
def ver_cliente(id_peluquero, id_turno):
    conn = get_db_connection()

    cliente = conn.execute(
        """
        SELECT 
            c.id,
            c.nombre,
            c.email,
            c.telefono
        FROM turnos t
        JOIN clientes c ON t.id_cliente = c.id
        WHERE t.id = ?
        AND t.id_peluquero = ?
        """,
        (id_turno, id_peluquero)
    ).fetchone()

    conn.close()

    if cliente is None:
        return jsonify({
            "error": "Cliente no encontrado o el turno no pertenece a este peluquero"
        }), 404

    return jsonify(dict(cliente)), 200