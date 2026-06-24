from flask import Blueprint, jsonify
from db import get_db_connection

cancelacion_bp = Blueprint('cancelacion', __name__)


def cancelar_cita(cursor, id_cita, id_usuario=None):
    cursor.execute(
        '''
        SELECT id_cita, id_usuario, estado
        FROM citas
        WHERE id_cita = %s
        ''',
        (id_cita,)
    )
    cita = cursor.fetchone()

    if not cita:
        return {"error": "Turno no encontrado"}, 404

    if id_usuario is not None and cita["id_usuario"] != id_usuario:
        return {"error": "Turno no encontrado o no pertenece al cliente"}, 404

    if cita["estado"] == "cancelada":
        return {"mensaje": "El turno ya estaba cancelado", "estado": "cancelada"}, 200

    if cita["estado"] == "completada":
        return {"error": "Este turno ya fue completado y no se puede cancelar"}, 409

    cursor.execute(
        '''
        UPDATE citas
        SET estado = 'cancelada',
            fecha_cancelacion = CURRENT_TIMESTAMP
        WHERE id_cita = %s
        ''',
        (id_cita,)
    )
    return {"mensaje": "Turno cancelado correctamente", "estado": "cancelada"}, 200


@cancelacion_bp.route('/cancelar/<int:id_cita>', methods=['GET'])
def cancelar_desde_mail(id_cita):
    conn = get_db_connection()
    cursor = conn.cursor()

    respuesta, status = cancelar_cita(cursor, id_cita)
    if status < 400:
        conn.commit()

    conn.close()
    return jsonify(respuesta), status
