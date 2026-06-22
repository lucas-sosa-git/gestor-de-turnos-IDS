from flask import Blueprint, render_template
from db import get_db_connection

cancelacion_bp = Blueprint('cancelacion', __name__)

@cancelacion_bp.route('/cancelar/<int:id_cita>', methods=['GET'])
def cancelar_desde_mail(id_cita):

    conn = get_db_connection()
    cursor = conn.cursor()
  
    cursor.execute(
        '''
        UPDATE citas
        SET estado = "cancelada",
            fecha_cancelacion = CURRENT_TIMESTAMP
        WHERE id_cita = %s
        ''',
        (id_cita,)
    )

    conn.commit()
    conn.close()

    return render_template(
        'cancelacion_exitosa.html',
        ok=True,
        mensaje="Tu reserva fue cancelada correctamente."
    )
