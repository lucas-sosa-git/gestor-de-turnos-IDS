from flask import Blueprint, request, jsonify
from db import get_db_connection

admin_bp = Blueprint('admin', __name__)

# --- CRUD BARBEROS ---

@admin_bp.route('/barberos', methods=['POST'])
def crear_barbero():
    data = request.get_json()
    nombre = data.get('nombre')
    email = data.get('email')
    contraseña = data.get('contraseña')

    if not nombre or not email or not contraseña:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    #validar email que sea unico
    existe = cursor.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "Email ya registrado"}), 400

    cursor.execute('INSERT INTO usuarios (nombre, email, contraseña, rol) VALUES (?, ?, ?, ?)', (nombre, email, contraseña, "barbero"))
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
    conn = get_db_connection()
    conn.execute('''
        UPDATE usuarios
        SET nombre = ?
        WHERE id_usuario = (
            SELECT id_usuario
            FROM barberos
            WHERE id_barbero = ?
        )
        ''', (nuevo_nombre, id_barbero))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Barbero actualizado"})

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

# MOSTRAR ESTADÍSTICAS (El cerebro del negocio)
@admin_bp.route('/estadisticas', methods=['GET'])
def mostrar_estadisticas():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Barbero con más citas
    top_barbero = cursor.execute('''SELECT u.nombre,COUNT(c.id_cita) AS total FROM citas c JOIN barberos b ON c.id_barbero = b.id_barbero JOIN usuarios u ON b.id_usuario = u.id_usuario GROUP BY c.id_barbero ORDER BY total DESC LIMIT 1''').fetchone()

    # Servicio más pedido
    top_servicio = cursor.execute('''SELECT s.nombre, COUNT(c.id_cita) AS total FROM citas c JOIN servicios s ON c.id_servicio = s.id_servicio GROUP BY c.id_servicio ORDER BY total DESC LIMIT 1 ''').fetchone()

    conn.close()
    
    return jsonify({
        "barbero_estrella": dict(top_barbero) if top_barbero else None,
        "servicio_popular": dict(top_servicio) if top_servicio else None
    })