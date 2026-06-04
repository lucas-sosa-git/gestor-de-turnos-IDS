from flask import Blueprint, request, jsonify
from db import get_db_connection
import hashlib

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Tenés que enviar datos en formato JSON"}), 400

    email = data.get('email')
    clave = data.get('clave')

    if not email or not clave:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    clave_hash = hashlib.sha256(clave.encode()).hexdigest()

    usuario = cursor.execute(
        '''
        SELECT id_usuario, nombre, email, rol
        FROM usuarios
        WHERE email = ? AND clave = ?
        ''',
        (email, clave_hash)
    ).fetchone()

    conn.close()

    if not usuario:
        return jsonify({"error": "Credenciales inválidas"}), 401

    return jsonify({
        "message": "Login exitoso",
        "usuario": dict(usuario)
    }), 200

