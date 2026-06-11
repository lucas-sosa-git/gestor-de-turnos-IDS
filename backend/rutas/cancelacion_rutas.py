from flask import Blueprint
from db import get_db_connection

cancelacion_bp = Blueprint('cancelacion', _name_)

@cancelacion_bp.route('/cancelar/<int:id_cita>', methods=['GET'])
def cancelar_desde_mail(id_cita):

    conn = get_db_connection()
    cursor = conn.cursor()
  
    cursor.execute(
        '''
        UPDATE citas
        SET estado = "cancelada",
            fecha_cancelacion = CURRENT_TIMESTAMP
        WHERE id_cita = ?
        ''',
        (id_cita,)
    )

    conn.commit()
    conn.close()

    return """
    <h2>Turno cancelado correctamente</h2>
    <p>Tu reserva fue cancelada con éxito.</p>
    """
