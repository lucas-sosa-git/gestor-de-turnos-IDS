from flask import Blueprint, request, jsonify
from db import get_db_connection
import hashlib
from fpdf import FPDF

admin_bp = Blueprint('admin', __name__)

# --- CRUD BARBEROS ---

@admin_bp.route('/barberos', methods=['POST'])
def crear_barbero():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    clave = data.get('clave')

    if not nombre or not email or not clave:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    #validar email que sea unico
    existe = cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "Email ya registrado"}), 400

    clave_hash = hashlib.sha256(clave.encode()).hexdigest()
    cursor.execute('INSERT INTO usuarios (nombre, email, clave, rol) VALUES (?, ?, ?, ?)', (nombre, email, clave_hash, "barbero"))
    id_usuario = cursor.lastrowid
    
    #crear barbero asociado
    
    cursor.execute('INSERT INTO barberos (id_usuario) values (?)', (id_usuario,))
    id_barbero = cursor.lastrowid
    conn.commit()

    barbero = cursor.execute('''
        SELECT b.id_barbero, u.nombre, u.email, b.activo
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        WHERE b.id_barbero = ?
    ''', (id_barbero,)).fetchone()
    conn.close()
    return jsonify({"mensaje": "Barbero creado", "barbero": dict(barbero)}), 201

@admin_bp.route('/barberos/<int:id_barbero>', methods=['PUT'])
def editar_barbero(id_barbero):
    data = request.get_json()
    nuevo_nombre = data.get('nombre')

    if not nuevo_nombre:
        return jsonify({"error": "El campo nombre es obligatorio"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    barbero = cursor.execute('SELECT id_usuario FROM barberos WHERE id_barbero = ?', (id_barbero,)).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    cursor.execute('''
        UPDATE usuarios
        SET nombre = ?
        WHERE id_usuario = (
            SELECT id_usuario
            FROM barberos
            WHERE id_barbero = ?
        )
        ''', (nuevo_nombre, id_barbero))
    conn.commit()

    actualizado = cursor.execute('''
        SELECT b.id_barbero, u.nombre, u.email, b.activo
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        WHERE b.id_barbero = ?
    ''', (id_barbero,)).fetchone()
    conn.close()
    return jsonify({"mensaje": "Barbero actualizado", "barbero": dict(actualizado)}), 200


@admin_bp.route('/barberos/<int:id_barbero>', methods=['DELETE'])
def eliminar_barbero(id_barbero):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Obtener id_usuario asociado
    usuario = cursor.execute('''
        SELECT id_usuario
        FROM barberos
        WHERE id_barbero = ?
        ''',(id_barbero,)).fetchone()
    if usuario is None:
        conn.close()
        return jsonify({
            "error": "Barbero no encontrado"
        }), 404
    # Eliminar barbero
    cursor.execute('DELETE FROM barberos WHERE id_barbero = ?', (id_barbero,))
    # Eliminar usuario
    cursor.execute('''
        DELETE FROM usuarios
        WHERE id_usuario = ?
        ''',(usuario['id_usuario'],))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Barbero eliminado"})

# --- CRUD SERVICIOS ---

@admin_bp.route('/servicios', methods=['POST'])
def crear_servicio():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO servicios (nombre, descripcion, duracion, precio) VALUES (?, ?, ?, ?)''',
        (data['nombre'], data['descripcion'], data['duracion'], data['precio'])
    )
    id_servicio = cursor.lastrowid
    conn.commit()

    #devolver el servicio creado
    servicio = cursor.execute('SELECT * FROM servicios WHERE id_servicio = ?', (id_servicio,)).fetchone()

    conn.close()

    return jsonify({"mensaje": "Servicio creado", "servicio": dict(servicio)}), 201

# CONFIGURAR HORARIOS (Update de un barbero específico)
@admin_bp.route('/barberos/<int:id_barbero>/horarios', methods=['PATCH'])
def configurar_horario(id_barbero):
    data = request.get_json()

    dia_semana = data.get('dia_semana')
    hora_inicio = data.get('hora_inicio')
    hora_fin = data.get('hora_fin')

    if dia_semana is None or not hora_inicio or not hora_fin:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    barbero = cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = ?', (id_barbero,)
    ).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404
    
    cursor.execute('''INSERT INTO disponibilidad_barberos (id_barbero, dia_semana, hora_inicio, hora_fin) VALUES (?, ?, ?, ?)''', (id_barbero, dia_semana, hora_inicio, hora_fin))
    id_disp = cursor.lastrowid
    conn.commit()
    horario = cursor.execute(
        'SELECT * FROM disponibilidad_barberos WHERE id_disp = ?', (id_disp,)
    ).fetchone()

    conn.close()
    return jsonify({"mensaje": "Horario actualizado", "horario": dict(horario)})



@admin_bp.route('/dashboard', methods=['GET'])
def estadisticas():
    conn = get_db_connection()
    cursor = conn.cursor()
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    #esto podria ser mas flexible si no se pone hasta sea hasta la fecha actual por ejemplo
    if not desde or not hasta: 
        return jsonify({"error": "Faltan los parametros de fecha"}) , 400
    
    citas = cursor.execute('''
    SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
           u.nombre AS cliente,
           s.nombre AS servicio,
           b.id_barbero
    FROM citas c
    JOIN usuarios u  ON c.id_usuario  = u.id_usuario
    JOIN servicios s ON c.id_servicio = s.id_servicio
    JOIN barberos b  ON c.id_barbero  = b.id_barbero
    WHERE DATE(c.fecha) BETWEEN DATE(?) AND DATE(?)
    ORDER BY c.fecha ASC, c.hora_inicio ASC
''', (desde, hasta)).fetchall()
    
    confirmadas = cursor.execute('''
    SELECT COUNT(*) AS total FROM citas
    WHERE estado = 'confirmada'
    AND fecha BETWEEN ? AND ?''', (desde, hasta)).fetchone()

    canceladas = cursor.execute('''
    SELECT COUNT(*) AS total FROM citas
    WHERE estado = 'cancelada'
    AND fecha BETWEEN ? AND ?''', (desde, hasta)).fetchone()

    tops_servicios = cursor.execute('''
    SELECT s.nombre, COUNT(c.id_cita) AS total FROM citas c
    JOIN servicios s ON c.id_servicio = s.id_servicio
    WHERE c.fecha BETWEEN ? AND ?
    GROUP BY c.id_servicio
    ORDER BY total DESC
    ''', (desde, hasta)).fetchall()

    top_cancelados = cursor.execute('''
    SELECT s.nombre, COUNT(c.id_cita) AS total FROM citas c
    JOIN servicios s ON c.id_servicio = s.id_servicio
    WHERE c.fecha BETWEEN ? AND ?
    AND c.estado = 'cancelada'
    GROUP BY c.id_servicio
    ORDER BY total DESC
    ''', (desde, hasta)).fetchall()

    estadisticas_barbero = cursor.execute('''
    SELECT u.nombre, COUNT(c.id_cita) AS turnos, SUM(s.precio) AS ingresos, AVG(r.calificacion) AS calif_promedio
    FROM barberos b
    JOIN usuarios u ON b.id_usuario = u.id_usuario
    LEFT JOIN citas c ON b.id_barbero = c.id_barbero AND c.fecha BETWEEN ? AND ? AND c.estado = 'confirmada'
    LEFT JOIN servicios s ON c.id_servicio = s.id_servicio
    LEFT JOIN resenias r ON c.id_cita = r.id_cita
    GROUP BY b.id_barbero
    ORDER BY ingresos DESC
    ''', (desde, hasta)).fetchall()

    conn.close()
    

    return jsonify({
        "citas": [dict(cita) for cita in citas],
        "total_confirmadas": confirmadas['total'] if confirmadas else 0,
        "total_canceladas": canceladas['total'] if canceladas else 0,
        "top_servicios": [dict(serv) for serv in tops_servicios],
        "top_cancelados": [dict(serv) for serv in top_cancelados],
        "estadisticas_barbero": [dict(est) for est in estadisticas_barbero]})

    