from flask import Blueprint, request, jsonify
from db import get_db_connection

clientes_bp = Blueprint('clientes', __name__)

# 1. REGISTRAR CLIENTE
@clientes_bp.route('/', methods=['POST'])
def registrar_cliente():
    nuevo_cliente = request.get_json()
    nombre = nuevo_cliente.get('nombre')
    email = nuevo_cliente.get('email')
    contraseña = nuevo_cliente.get('contraseña')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO clientes (nombre, email, contraseña, rol) VALUES (?, ?, ?, ?)', (nombre, email, contraseña, "cliente"))
        conn.commit()
        return jsonify({"mensaje": "Cliente creado"}), 201
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

# 3. MOSTRAR BARBEROS
@clientes_bp.route('/barberos', methods=['GET'])
def mostrar_barberos():
    conn = get_db_connection()
    barberos = conn.execute('SELECT b.id_barbero, u.nombre, u.email, b.activo FROM barberos b JOIN usuarios u on b.id_usuario=u.id_usuario').fetchall()
    conn.close()
    return jsonify([dict(b) for b in barberos])


@clientes_bp.route('/barberos/<int:id_barbero>/horarios', methods=['GET'])
def mostrar_horarios_barbero(id_barbero):
    conn = get_db_connection()
    # Aquí podrías traer los horarios disponibles de una tabla 'horarios' 
    # o simplemente los turnos que ya tiene ocupados para bloquearlos en el front
    query = '''
        SELECT fecha, hora 
        FROM citas 
        WHERE id_barbero = ?
    '''
    horarios_ocupados = conn.execute(query, (id_barbero,)).fetchall()
    conn.close()
    
    return jsonify([dict(h) for h in horarios_ocupados])


# CANCELAR TURNO (DELETE)
@clientes_bp.route('/turnos/<int:id_cita>', methods=['DELETE'])
def cancelar_turno(id_cita):
    # En REST, el id_usuario suele venir del token de seguridad, 
    # pero por ahora podemos recibirlo en el JSON para probar
    id_usuario = request.json.get('id_usuario')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Borramos el turno solo si pertenece a ese cliente
    cursor.execute('DELETE FROM turnos WHERE id_cita = ? AND id_usuario = ?', (id_cita, id_usuario))
    conn.commit()
    filas_afectadas = cursor.rowcount
    conn.close()

    if filas_afectadas == 0:
        return jsonify({"error": "Turno no encontrado o no pertenece al cliente"}), 404
        
    return jsonify({"mensaje": "Turno cancelado correctamente"}), 200


@clientes_bp.route('/turnos/<int:id_cita>/reprogramar', methods=['PATCH'])
def reprogramar_turno(id_cita):
    data = request.get_json()
    nueva_fecha = data.get('nueva_fecha') # Ejemplo: "2024-10-25"
    nueva_hora = data.get('nueva_hora') # Ejemplo: "15:00"
    id_usario = data.get('id_usuario')   # Por seguridad, verificamos que sea su turno

    if not nueva_fecha:
        return jsonify({"error": "Falta la nueva fecha"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Actualizamos solo la fecha_hora
        cursor.execute('''
            UPDATE citas 
            SET fecha = ?, hora = ? 
            WHERE id_cita = ? AND id_usario = ?
        ''', (nueva_fecha, nueva_hora, id_cita, id_usario))
        
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Turno no encontrado o no pertenece al cliente"}), 404
            
        return jsonify({"mensaje": "Turno reprogramado con éxito"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()
        

# HISTORIAL DE TURNOS (GET)
@clientes_bp.route('/<int:id_usuario>/historial', methods=['GET'])
def historial_turnos(id_usuario):
    conn = get_db_connection()
    # Traemos los turnos uniendo tablas para que el cliente vea el nombre del barbero y servicio
    query = '''
        SELECT 
            c.id_cita,
            c.fecha,
            c.hora,
            ub.nombre AS barbero,
            s.nombre AS servicio,
            c.estado
        FROM citas c
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.id_usuario = ?
        ORDER BY c.fecha DESC, c.hora DESC
    '''

    turnos = conn.execute(query,(id_usuario,)).fetchall()
    conn.close()
    
    return jsonify([dict(t) for t in turnos])