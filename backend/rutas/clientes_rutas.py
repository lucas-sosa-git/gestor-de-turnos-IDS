from flask import Blueprint, request, jsonify
from db import get_db_connection

clientes_bp = Blueprint('clientes', __name__)

# 1. REGISTRAR CLIENTE
@clientes_bp.route('/', methods=['POST'])
def registrar_cliente():
    nuevo_cliente = request.get_json()
    nombre = nuevo_cliente.get('nombre')
    email = nuevo_cliente.get('email')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO clientes (nombre, email) VALUES (?, ?)', (nombre, email))
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
    barberos = conn.execute('SELECT * FROM barberos').fetchall()
    conn.close()
    return jsonify([dict(b) for b in barberos])

# CANCELAR TURNO (DELETE)
@clientes_bp.route('/turnos/<int:id_turno>', methods=['DELETE'])
def cancelar_turno(id_turno):
    # En REST, el id_cliente suele venir del token de seguridad, 
    # pero por ahora podemos recibirlo en el JSON para probar
    id_cliente = request.json.get('id_cliente')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Borramos el turno solo si pertenece a ese cliente
    cursor.execute('DELETE FROM turnos WHERE id = ? AND id_cliente = ?', (id_turno, id_cliente))
    conn.commit()
    filas_afectadas = cursor.rowcount
    conn.close()

    if filas_afectadas == 0:
        return jsonify({"error": "Turno no encontrado o no pertenece al cliente"}), 404
        
    return jsonify({"mensaje": "Turno cancelado correctamente"}), 200

# HISTORIAL DE TURNOS (GET)
@clientes_bp.route('/<int:id_cliente>/historial', methods=['GET'])
def historial_turnos(id_cliente):
    conn = get_db_connection()
    # Traemos los turnos uniendo tablas para que el cliente vea el nombre del barbero y servicio
    query = '''
        SELECT t.id, t.fecha_hora, b.nombre as barbero, s.nombre as servicio
        FROM turnos t
        JOIN barberos b ON t.id_barbero = b.id
        JOIN servicios s ON t.id_servicio = s.id
        WHERE t.id_cliente = ?
        ORDER BY t.fecha_hora DESC
    '''
    turnos = conn.execute(query, (id_cliente,)).fetchall()
    conn.close()
    
    return jsonify([dict(t) for t in turnos])