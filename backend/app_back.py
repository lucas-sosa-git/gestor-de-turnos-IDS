import os
from flask import Flask
# Importamos todos los blueprints
from rutas.admin_rutas import admin_bp
from rutas.clientes_rutas import clientes_bp
from rutas.profesionales_rutas import profesionales_bp
from rutas.auth_rutas import auth_bp
from rutas.cancelacion_rutas import cancelacion_bp  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_TEMPLATES = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "templates"))
FRONTEND_STATIC = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend", "statics"))
app = Flask(__name__, template_folder=FRONTEND_TEMPLATES, static_folder=FRONTEND_STATIC)

# Registramos cada uno con su prefijo
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(clientes_bp, url_prefix='/clientes')
app.register_blueprint(profesionales_bp, url_prefix='/profesionales')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(cancelacion_bp)

@app.route('/')
def index():
    return "Servidor de Barbería Funcionando 💈"

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
