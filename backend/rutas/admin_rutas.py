from flask import Blueprint, request, jsonify
from db import get_db_connection

admin_bp = Blueprint('admin', __name__)

# --- CRUD BARBEROS ---

@admin_bp.route('/barberos', methods=['POST'])
def crear_barbero():
    nombre = request.json.get('nombre')
    conn = get_db_connection()
    conn.execute('INSERT INTO barberos (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Barbero creado"}), 201

@admin_bp.route('/barberos/<int:id>', methods=['PUT'])
def editar_barbero(id):
    nuevo_nombre = request.json.get('nombre')
    conn = get_db_connection()
    conn.execute('UPDATE barberos SET nombre = ? WHERE id = ?', (nuevo_nombre, id))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Barbero actualizado"})

@admin_bp.route('/barberos/<int:id>', methods=['DELETE'])
def eliminar_barbero(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM barberos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Barbero eliminado"})

# --- CRUD SERVICIOS ---

@admin_bp.route('/servicios', methods=['POST'])
def crear_servicio():
    data = request.json
    conn = get_db_connection()
    conn.execute('INSERT INTO servicios (nombre, precio) VALUES (?, ?)', 
                 (data['nombre'], data['precio']))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Servicio creado"}), 201

# CONFIGURAR HORARIOS (Update de un barbero específico)
@admin_bp.route('/barberos/<int:id>/horarios', methods=['PATCH'])
def configurar_horario(id):
    nuevo_horario = request.json.get('horario_texto') # Ej: "Lunes a Viernes 9-18hs"
    conn = get_db_connection()
    conn.execute('UPDATE barberos SET horarios = ? WHERE id = ?', (nuevo_horario, id))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Horario actualizado"})

# MOSTRAR ESTADÍSTICAS (El cerebro del negocio)
@admin_bp.route('/estadisticas', methods=['GET'])
def mostrar_estadisticas():
    conn = get_db_connection()
    
    # Barbero con más turnos
    top_barbero = conn.execute('''
        SELECT b.nombre, COUNT(t.id) as total 
        FROM turnos t 
        JOIN barberos b ON t.id_barbero = b.id 
        GROUP BY t.id_barbero 
        ORDER BY total DESC LIMIT 1
    ''').fetchone()

    # Servicio más pedido
    top_servicio = conn.execute('''
        SELECT s.nombre, COUNT(t.id) as total 
        FROM turnos t 
        JOIN servicios s ON t.id_servicio = s.id 
        GROUP BY t.id_servicio 
        ORDER BY total DESC LIMIT 1
    ''').fetchone()

    conn.close()
    
    return jsonify({
        "barbero_estrella": dict(top_barbero) if top_barbero else None,
        "servicio_popular": dict(top_servicio) if top_servicio else None
    })