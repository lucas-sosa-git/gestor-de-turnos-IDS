from flask import Flask, render_template


app = Flask(__name__, template_folder="templates", static_folder="statics")


@app.route("/")
def login():
    return render_template("login.html")

@app.route("/admin")
def admin_panel():
    # Datos de ejemplo
    stats = {
        'ingresos_mes': 15000,
        'delta_ingresos': 15,
        'citas_completadas': 45,
        'delta_citas': 10,
        'clientes_activos': 120,
        'delta_clientes': 8,
        'calificacion_promedio': 4.8,
        'delta_rating': 0.3,
        'semanas': [
            {'label': 'Sem 1', 'monto': 10000},
            {'label': 'Sem 2', 'monto': 15000},
            {'label': 'Sem 3', 'monto': 20000},
            {'label': 'Sem 4', 'monto': 25000},
        ]
    }
    
    citas = [
        {'cliente': 'Juan Pérez', 'barbero': 'Carlos', 'servicio': 'Corte', 'hora': '10:00', 'estado': 'Completada'},
        {'cliente': 'María López', 'barbero': 'Ana', 'servicio': 'Tinte', 'hora': '11:30', 'estado': 'Pendiente'},
    ]
    
    barberos = [
        {'nombre': 'Carlos', 'citas': 50, 'rating': 4.8, 'ingresos': 50000, 'activo': True},
        {'nombre': 'Ana', 'citas': 45, 'rating': 4.9, 'ingresos': 48000, 'activo': True},
    ]
    
    servicios = [
        {'nombre': 'Corte', 'duracion_min': 30, 'precio': 10000, 'veces_solicitado': 45},
        {'nombre': 'Barba', 'duracion_min': 20, 'precio': 5000, 'veces_solicitado': 30},
    ]
    
    return render_template("admin/dashboard.html", 
                         stats=stats, 
                         citas=citas, 
                         barberos=barberos,
                         barberos_top=barberos,
                         servicios=servicios,
                         servicios_top=servicios)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
