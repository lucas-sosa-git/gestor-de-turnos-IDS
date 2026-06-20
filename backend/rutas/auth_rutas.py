from datetime import datetime, timedelta
import hashlib
import os

import jwt
from flask import Blueprint, jsonify, request

from db import get_db_connection


auth_bp = Blueprint('auth', __name__)

JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_ALGORITHM = "HS256"


def generar_token(usuario_id, rol):
    if not JWT_SECRET:
        raise RuntimeError("Falta configurar JWT_SECRET")

    payload = {
        "usuario_id": usuario_id,
        "rol": rol,
        "exp": datetime.utcnow() + timedelta(hours=2)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Tenes que enviar datos en formato JSON"}), 400

    email = data.get('email')
    clave = data.get('clave')

    if not email or not clave:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    usuario = cursor.execute(
        '''
        SELECT id_usuario, nombre, email, clave, rol
        FROM usuarios
        WHERE email = ?
        ''',
        (email,)
    ).fetchone()

    conn.close()

    clave_hash = hashlib.sha256(clave.encode()).hexdigest()

    if not usuario or usuario['clave'] != clave_hash:
        return jsonify({"error": "Credenciales invalidas"}), 401

    usuario_dto = {
        "id_usuario": usuario["id_usuario"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "rol": usuario["rol"]
    }

    token = generar_token(usuario["id_usuario"], usuario["rol"])

    return jsonify({
        "message": "Login exitoso",
        "token": token,
        "usuario": usuario_dto
    }), 200
