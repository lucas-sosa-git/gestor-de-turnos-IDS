from flask import Blueprint, request, jsonify
from db import get_db_connection
from datetime import datetime, timedelta
import hashlib
import time
import qrcode
import io
from flask import send_file
from mail_service import enviar_mail

clientes_bp = Blueprint('clientes', __name__)

# 1. REGISTRAR CLIENTE
@clientes_bp.route('/', methods=['POST'])
def registrar_cliente():
    nuevo_cliente = request.get_json()
    nombre = nuevo_cliente.get('nombre')
    email = nuevo_cliente.get('email')
    clave = nuevo_cliente.get('clave')

    if not nombre or not email or not clave:
        return jsonify({"error": "nombre, email y clave son obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # validar email 
    existe = cursor.execute(
        'SELECT id_usuario FROM usuarios WHERE email = ?', (email,)
    ).fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "Ya existe un usuario con ese email"}), 409
    
    try:
        cursor.execute(
            'INSERT INTO usuarios (nombre, email, clave, rol) VALUES (?, ?, ?, ?)',
            (nombre, email, hashlib.sha256(clave.encode()).hexdigest(), "cliente")
        )
        id_usuario = cursor.lastrowid
        conn.commit()

        # Devolver el recurso creado
        cliente = cursor.execute(
            'SELECT id_usuario, nombre, email, rol FROM usuarios WHERE id_usuario = ?',
            (id_usuario,)
        ).fetchone()
        return jsonify(dict(cliente)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# 2. MOSTRAR SERVICIOS
@clientes_bp.route('/servicios', methods=['GET'])
def mostrar_servicios():
    conn = get_db_connection()
    servicios = conn.execute('SELECT * FROM servicios').fetchall()
    conn.close()
    
    # Convertimos los objetos Row a una lista de diccionarios para JSON
    return jsonify([dict(s) for s in servicios])


@clientes_bp.route('/servicios/<int:id_usuario>', methods=['GET'])
def mostrar_servicios_cliente(id_usuario):
    conn = get_db_connection()
    usuario = conn.execute('''SELECT * FROM usuarios WHERE id_usuario = ?''', (id_usuario,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    turnos = conn.execute('''SELECT id_cita FROM citas WHERE id_usuario = ?''', (id_usuario,)).fetchall()
    servicios = conn.execute('''
        SELECT
            id_servicio,
            nombre,
            descripcion,
            duracion,
            precio,
            img_servicio
        FROM servicios
        ORDER BY nombre ASC
    ''').fetchall()
    conn.close()

    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "servicios": [dict(servicio) for servicio in servicios],
        "turnos": [dict(turno) for turno in turnos]
    }), 200


# 3. MOSTRAR BARBEROS
@clientes_bp.route('/barberos/<int:id_usuario>', methods=['GET'])
def mostrar_barberos(id_usuario):
    conn = get_db_connection()
    usuario = conn.execute(''' select * from usuarios where id_usuario = ? ''', (id_usuario,)).fetchone()
    if not usuario:
        conn.close()
        return jsonify({"error": "Usuario no encontrado"}), 404

    barberos = conn.execute('''SELECT b.id_barbero, u.nombre, u.email, b.activo, b.img_barbero FROM barberos b JOIN usuarios u on b.id_usuario=u.id_usuario''').fetchall()
    turnos = conn.execute('''
        select id_cita from citas where id_usuario = ?
    ''', (id_usuario,)).fetchall()
    conn.close()
    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "barberos": [dict(barbero) for barbero in barberos],
        "turnos": [dict(turno) for turno in turnos]
    }), 200

# 4. VISTA HTML: PANEL DE RESERVAS DEL CLIENTE
@clientes_bp.route('/panel/<int:id_usuario>', methods=['GET'])
def panel_cliente(id_usuario):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Traer los datos del usuario logueado para personalizar el saludo
    usuario = cursor.execute(
        'SELECT nombre,id_usuario FROM usuarios WHERE id_usuario = ?', (id_usuario,)
    ).fetchone()

    # 2. Buscar solo sus turnos ACTIVOS (no cancelados) uniendo servicios y barberos
    query = '''
        SELECT 
            c.id_cita,
            c.fecha,
            c.hora_inicio,
            c.estado,
            ub.nombre AS barbero_nombre,
            s.nombre AS servicio_nombre
        FROM citas c
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_usuario = ? AND c.estado != 'cancelada'
        ORDER BY c.fecha ASC, c.hora_inicio ASC
    '''
    turnos = cursor.execute(query, (id_usuario,)).fetchall()
    conn.close()

    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Enviamos las variables 'usuario' y 'turnos' directamente al HTML
    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "turnos": [dict(turno) for turno in turnos]
    }), 200

@clientes_bp.route('/acerca-de/<int:id_usuario>', methods=['GET'])
def acerca_de(id_usuario):
    conn = get_db_connection()
    # 1. Buscamos el usuario actual (un solo registro con .fetchone())
    usuario = conn.execute(''' SELECT * FROM usuarios WHERE id_usuario = ? ''', (id_usuario,)).fetchone()
    # 2. Buscamos las citas del usuario para el contador de la barra de navegación
    turnos = conn.execute(''' SELECT id_cita FROM citas WHERE id_usuario = ? ''', (id_usuario,)).fetchall()
    # 3. Cerramos la conexión a la base de datos
    conn.close()
    # 4. Enviamos absolutamente todo al HTML
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    return jsonify({
        "usuario": dict(usuario),
        "id_usuario": id_usuario,
        "turnos": [dict(turno) for turno in turnos]
    }), 200

@clientes_bp.route('/barberos/<int:id_barbero>/horarios', methods=['GET'])
def mostrar_horarios_barbero(id_barbero):
    conn   = get_db_connection()
    cursor = conn.cursor()

    # Validar que el barbero exista
    barbero = cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = ? AND activo = 1', (id_barbero,)
    ).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    # Devuelve disponibilidad configurada + citas ocupadas
    disponibilidad = cursor.execute(
        'SELECT * FROM disponibilidad_barberos WHERE id_barbero = ?', (id_barbero,)
    ).fetchall()

    citas_ocupadas = cursor.execute('''
        SELECT fecha, hora_inicio, hora_fin, estado
        FROM citas
        WHERE id_barbero = ?
          AND fecha >= DATE('now')
          AND estado != 'cancelada'
        ORDER BY fecha, hora_inicio
    ''', (id_barbero,)).fetchall()

    conn.close()
    return jsonify({
        "disponibilidad": [dict(d) for d in disponibilidad],
        "citas_ocupadas": [dict(c) for c in citas_ocupadas]
    }), 200


# CANCELAR TURNO (DELETE)
@clientes_bp.route('/turnos/<int:id_cita>', methods=['DELETE'])
def cancelar_turno(id_cita):
    # En REST, el id_usuario suele venir del token de seguridad, 
    # pero por ahora podemos recibirlo en el JSON para probar
    id_usuario = request.json.get('id_usuario')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cita = cursor.execute('SELECT estado FROM citas WHERE id_cita = ? AND id_usuario = ?', (id_cita, id_usuario)).fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Turno no encontrado o no pertenece al cliente"}), 404
    if cita['estado'] in ('cancelada', 'completada'):
        conn.close()
        return jsonify({"error": "Este turno no se puede cancelar"}), 409

    # Borramos el turno solo si pertenece a ese cliente
    # en vez de borrarlo podriamos cambiar el estado a cancelada
    cursor.execute('UPDATE citas SET estado = "cancelada", fecha_cancelacion = CURRENT_TIMESTAMP WHERE id_cita = ? AND id_usuario = ?', (id_cita, id_usuario))
    conn.commit()

    conn.close()

    return jsonify({"mensaje": "Turno cancelado correctamente"}), 200


@clientes_bp.route('/turnos/<int:id_cita>/', methods=['PATCH'])
def reprogramar_turno(id_cita):
    data = request.get_json()
    nueva_fecha = data.get('nueva_fecha') 
    nueva_hora_inicio = data.get('nueva_hora_inicio') 
    id_usuario = data.get('id_usuario')   

    if not nueva_fecha or not nueva_hora_inicio:
        return jsonify({"error": "Falta la nueva fecha o hora de inicio"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cita = cursor.execute(
        'SELECT * FROM citas WHERE id_cita = ?', (id_cita,)
    ).fetchone()

    if not cita:
        conn.close()
        return jsonify({"error": "Turno no encontrado"}), 404

    if cita['id_usuario'] != id_usuario:
        conn.close()
        return jsonify({"error": "Este turno no pertenece al cliente"}), 403

    if cita['estado'] in ('cancelada', 'completada'):
        conn.close()
        return jsonify({"error": "No se puede reprogramar un turno cancelado o completado"}), 409

    # Validar que el nuevo horario no esté ocupado por ese barbero
    
    servicio = cursor.execute('SELECT duracion FROM servicios WHERE id_servicio = ?', (cita['id_servicio'],)).fetchone()

    nueva_hora_fin = (datetime.strptime(nueva_hora_inicio, "%H:%M") + timedelta(minutes=servicio['duracion'])).strftime("%H:%M")

    conflicto = cursor.execute('''
        SELECT id_cita FROM citas
        WHERE id_barbero = ?
          AND fecha = ?
          AND hora_inicio < ?
          AND hora_fin > ?
          AND estado != 'cancelada'
          AND id_cita != ?
    ''', (cita['id_barbero'], nueva_fecha, nueva_hora_inicio, nueva_hora_fin, id_cita)).fetchone()

    if conflicto:
        conn.close()
        return jsonify({"error": "Ese horario ya está ocupado para el barbero"}), 409

    cursor.execute(
        'UPDATE citas SET fecha = ?, hora_inicio = ?, hora_fin = ? WHERE id_cita = ?',
        (nueva_fecha, nueva_hora_inicio, nueva_hora_fin, id_cita)
    )
    conn.commit()

    actualizada = cursor.execute('SELECT * FROM citas WHERE id_cita = ?', (id_cita,)).fetchone()
    conn.close()
    return jsonify(dict(actualizada)), 200
    
        

# HISTORIAL DE TURNOS (GET)
@clientes_bp.route('/<int:id_usuario>/historial', methods=['GET'])
def historial_turnos(id_usuario):
    conn = get_db_connection()
    # Traemos los turnos uniendo tablas para que el cliente vea el nombre del barbero y servicio
    query = '''
        SELECT 
            c.id_cita,
            c.fecha,
            c.hora_inicio,
            ub.nombre AS barbero,
            s.nombre AS servicio,
            c.estado
        FROM citas c
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_usuario = ?
        ORDER BY c.fecha DESC, c.hora_inicio DESC
    '''

    turnos = conn.execute(query,(id_usuario,)).fetchall()
    conn.close()
    
    return jsonify([dict(t) for t in turnos])


@clientes_bp.route('/turnos', methods=['POST'])
def reservar_turno():
    data        = request.get_json()
    id_usuario  = data.get('id_usuario')
    id_barbero  = data.get('id_barbero')
    id_servicio = data.get('id_servicio')
    fecha       = data.get('fecha')
    hora_inicio = data.get('hora_inicio')

    if not id_usuario or not id_barbero or not id_servicio or not fecha or not hora_inicio:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    conn   = get_db_connection()
    cursor = conn.cursor()

    cliente = cursor.execute(
        'SELECT id_usuario FROM usuarios WHERE id_usuario = ? AND rol = "cliente"',
        (id_usuario,)
    ).fetchone()
    if not cliente:
        conn.close()
        return jsonify({"error": "Cliente no encontrado"}), 404

    barbero = cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = ? AND activo = 1',
        (id_barbero,)
    ).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado o inactivo"}), 404

    servicio = cursor.execute(
        'SELECT id_servicio, duracion FROM servicios WHERE id_servicio = ?',
        (id_servicio,)
    ).fetchone()
    if not servicio:
        conn.close()
        return jsonify({"error": "Servicio no encontrado"}), 404

    hora_fin = (
        datetime.strptime(hora_inicio, "%H:%M") +
        timedelta(minutes=servicio['duracion'])
    ).strftime("%H:%M")

    if fecha < datetime.now().strftime("%Y-%m-%d"):
        conn.close()
        return jsonify({"error": "No se puede reservar en una fecha pasada"}), 400

    conflicto = cursor.execute('''
        SELECT id_cita FROM citas
        WHERE id_barbero = ?
          AND fecha = ?
          AND estado != 'cancelada'
          AND hora_inicio < ?
          AND hora_fin > ?
    ''', (id_barbero, fecha, hora_fin, hora_inicio)).fetchone()
    if conflicto:
        conn.close()
        return jsonify({"error": "Ese horario ya está ocupado para el barbero"}), 409

    qr_token = hashlib.sha256(f"{id_usuario}{id_barbero}{fecha}{hora_inicio}{time.time()}".encode()).hexdigest()

    cursor.execute('''
        INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
        VALUES (?, ?, ?, ?, ?, ?, 'confirmada', ?)
    ''', (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, qr_token))
    id_cita = cursor.lastrowid
    conn.commit()

    cita = cursor.execute('''
        SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
               u.nombre  AS cliente,
               u.email   AS cliente_email,
               ub.nombre AS barbero,
               s.nombre  AS servicio
        FROM citas c
        JOIN usuarios u  ON c.id_usuario  = u.id_usuario
        JOIN barberos b  ON c.id_barbero  = b.id_barbero
        JOIN usuarios ub ON b.id_usuario  = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_cita = ?
    ''', (id_cita,)).fetchone()

    conn.close()

    enviar_mail(
        destinatario=cita['cliente_email'],
        nombre=cita['cliente'],
        fecha=cita['fecha'],
        hora=cita['hora_inicio'],
        barbero=cita['barbero'],
        servicio=cita['servicio'],
        qr_token=qr_token,
        id_cita=id_cita
    )

    
    return jsonify(dict(cita)), 201


@clientes_bp.route('/resenias', methods=['POST'])
def dejar_resenia():
    data = request.get_json()
    id_usuario = data.get('id_usuario')
    id_barbero = data.get('id_barbero')
    id_cita    = data.get('id_cita')
    calificacion = data.get('calificacion')
    comentario = data.get('comentario')

    if not id_usuario or not id_barbero or not id_cita or not calificacion:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cliente = cursor.execute('SELECT id_usuario FROM usuarios WHERE id_usuario = ? and rol = "cliente"', (id_usuario,)).fetchone()
    if not cliente:
        conn.close()
        return jsonify({"error": "Cliente no encontrado"}), 404
    
    barbero = cursor.execute('SELECT id_barbero FROM barberos WHERE id_barbero = ? and activo = 1', (id_barbero,)).fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404
    
    if not isinstance(calificacion, int) or calificacion < 1 or calificacion > 5:
        conn.close()
        return jsonify({"error": "La calificación debe ser un número entero entre 1 y 5"}), 400
    
    #le podriamos agregarle a la bd un estado de cita completada para que se pueda dejar la resenia cuando se termine el turno.
    cita = cursor.execute('SELECT id_cita FROM citas WHERE id_cita =? AND id_usuario = ? AND id_barbero = ? AND estado = "completada"', (id_cita, id_usuario, id_barbero)).fetchone()
    if not cita:
        conn.close()
        return jsonify({"error": "Cita no encontrada, no pertenece al cliente o no es del barbero"}), 404
    
    resenia_existente = cursor.execute('SELECT id_resenia FROM resenias WHERE id_usuario = ? AND id_cita = ?', (id_usuario, id_cita)).fetchone()
    if resenia_existente:
        conn.close()
        return jsonify({"error": "Ya has dejado una reseña para esta cita"}), 409

    cursor.execute('INSERT INTO resenias (id_usuario, id_cita, calificacion, comentario) VALUES (?, ?, ?, ?)', (id_usuario, id_cita, calificacion, comentario))
    id_resenia = cursor.lastrowid
    conn.commit()
    resenia = cursor.execute('SELECT * FROM resenias WHERE id_resenia = ?', (id_resenia,)).fetchone()
    
    conn.close()
    return jsonify({"message": "Reseña subida correctamente", "Reseña": dict(resenia)}), 201


@clientes_bp.route('/turnos/<int:id_cita>/qr', methods=['GET'])
def generar_qr_turno(id_cita):
    conn = get_db_connection()
    cursor = conn.cursor()

    cita = cursor.execute('SELECT qr_token FROM citas WHERE id_cita = ?', (id_cita,)).fetchone()
    conn.close()

    if not cita:
        return jsonify({"error": "Turno no encontrado"}), 404
    
    if not cita['qr_token']:
        return jsonify({"error": "No se pudo generar el QR para este turno"}), 500
    
    #la imagen del qr tambien se puede generar en el front, lo podemos cambiar si quieren

    img = qrcode.make(cita['qr_token'])
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png')
