from flask import Flask
# Importamos todos los blueprints
from rutas.admin_rutas import admin_bp
from rutas.clientes_rutas import clientes_bp
from rutas.profesionales_rutas import profesionales_bp
from rutas.auth_rutas import auth_bp

app = Flask(__name__)

# Registramos cada uno con su prefijo
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(clientes_bp, url_prefix='/clientes')
app.register_blueprint(profesionales_bp, url_prefix='/profesionales')
app.register_blueprint(auth_bp, url_prefix='/api/auth')

@app.route('/')
def index():
    return "Servidor de Barbería Funcionando 💈"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
