from copy import error

from flask import Blueprint, request, jsonify
from storage import subir_imagen
from db import get_db_connection
import hashlib
from datetime import date, timedelta
import calendar


admin_bp = Blueprint('admin', __name__)

DIAS_DISPONIBLES = {0, 1, 2, 3, 4, 5, 6}


def minutos_a_hora(minutos):
    horas = minutos // 60
    mins = minutos % 60
    return f"{horas:02d}:{mins:02d}:00"


def hora_a_minutos(hora):
    partes = str(hora).split(":")
    return int(partes[0]) * 60 + int(partes[1])


def validar_rango_horario(hora_inicio, hora_fin):
    inicio = hora_a_minutos(hora_inicio)
    fin = hora_a_minutos(hora_fin)

    if fin <= inicio:
        raise ValueError("hora_fin debe ser mayor que hora_inicio")

    return inicio, fin


def parsear_disponibilidad_form(form):
    dias_raw = form.getlist("dias[]")
    hora_inicio = (form.get("hora_inicio") or "").strip()
    hora_fin = (form.get("hora_fin") or "").strip()

    try:
        dias = sorted({int(dia) for dia in dias_raw})
    except ValueError:
        raise ValueError("Los dias seleccionados no son validos")

    if not dias:
        raise ValueError("Selecciona al menos un dia de trabajo")

    if any(dia not in DIAS_DISPONIBLES for dia in dias):
        raise ValueError("Los dias seleccionados deben estar entre 0 y 6")

    if not hora_inicio or not hora_fin:
        raise ValueError("hora_inicio y hora_fin son obligatorios")

    inicio, fin = validar_rango_horario(hora_inicio, hora_fin)

    return dias, minutos_a_hora(inicio), minutos_a_hora(fin)


def rango_cubre_turno(dias, hora_inicio_disp, hora_fin_disp, fecha_turno, hora_inicio, hora_fin):
    dia = (fecha_turno.weekday() + 1) % 7
    inicio = hora_a_minutos(hora_inicio)
    fin = hora_a_minutos(hora_fin)
    disp_inicio = hora_a_minutos(hora_inicio_disp)
    disp_fin = hora_a_minutos(hora_fin_disp)

    return dia in dias and disp_inicio <= inicio and fin <= disp_fin


def citas_fuera_de_disponibilidad(cursor, id_barbero, dias, hora_inicio, hora_fin):
    cursor.execute('''
        SELECT c.id_cita, c.fecha, c.hora_inicio, c.hora_fin, c.estado,
               u.nombre AS cliente
        FROM citas c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        WHERE c.id_barbero = %s
          AND DATE(c.fecha) >= CURRENT_DATE
          AND c.estado IN ('confirmada', 'pendiente')
        ORDER BY c.fecha, c.hora_inicio
    ''', (id_barbero,))
    citas = cursor.fetchall()

    fuera = []
    for cita in citas:
        fecha_turno = cita["fecha"]
        if not hasattr(fecha_turno, "weekday"):
            fecha_turno = date.fromisoformat(str(fecha_turno))

        if not rango_cubre_turno(
            dias,
            hora_inicio,
            hora_fin,
            fecha_turno,
            cita["hora_inicio"],
            cita["hora_fin"],
        ):
            fuera.append(dict(cita))

    return fuera


def mensaje_citas_fuera(citas_fuera):
    detalle = [
        f"#{cita['id_cita']} {cita['fecha']} {str(cita['hora_inicio'])[:5]}-{str(cita['hora_fin'])[:5]}"
        for cita in citas_fuera[:5]
    ]
    return (
        "No se puede actualizar la disponibilidad porque hay citas futuras "
        "confirmadas o pendientes fuera del nuevo horario: " + ", ".join(detalle)
    )


def reemplazar_disponibilidad(cursor, id_barbero, dias, hora_inicio, hora_fin, validar_citas=False):
    validar_rango_horario(hora_inicio, hora_fin)

    if validar_citas:
        citas_fuera = citas_fuera_de_disponibilidad(cursor, id_barbero, dias, hora_inicio, hora_fin)
        if citas_fuera:
            raise ValueError(mensaje_citas_fuera(citas_fuera))

    cursor.execute(
        'DELETE FROM disponibilidad_barberos WHERE id_barbero = %s',
        (id_barbero,)
    )

    valores = []
    for dia in dias:
        valores.append((id_barbero, dia, hora_inicio, hora_fin))

    cursor.executemany('''
        INSERT INTO disponibilidad_barberos (id_barbero, dia_semana, hora_inicio, hora_fin)
        VALUES (%s, %s, %s, %s)
    ''', valores)


def disponibilidad_barbero(cursor, id_barbero):
    cursor.execute('''
        SELECT dia_semana, hora_inicio, hora_fin
        FROM disponibilidad_barberos
        WHERE id_barbero = %s
        ORDER BY dia_semana, hora_inicio
    ''', (id_barbero,))
    filas = cursor.fetchall()

    dias = sorted({fila["dia_semana"] for fila in filas})
    inicios = [hora_a_minutos(fila["hora_inicio"]) for fila in filas]
    fines = [hora_a_minutos(fila["hora_fin"]) for fila in filas]

    return {
        "dias": dias,
        "hora_inicio": minutos_a_hora(min(inicios))[:5] if inicios else "",
        "hora_fin": minutos_a_hora(max(fines))[:5] if fines else "",
    }

# --- CRUD BARBEROS ---

@admin_bp.route('/barberos', methods=['POST'])
def crear_barbero():
    nombre  = request.form.get('nombre')
    email   = request.form.get('email')
    clave   = request.form.get('clave')
    archivo  = request.files.get('imagen')

    try:
        dias, hora_inicio, hora_fin = parsear_disponibilidad_form(request.form)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if not nombre or not email or not clave:
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()

    #validar email que sea unico
    cursor.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
    existe = cursor.fetchone()
    if existe:
        conn.close()
        return jsonify({"error": "Email ya registrado"}), 400
    
    img_barbero = None
    if archivo:
        img_barbero = subir_imagen(archivo)
        if not img_barbero:
            conn.close()
            return jsonify({"error": "Error al subir la imagen"}), 500


    clave_hash = hashlib.sha256(clave.encode()).hexdigest()
    cursor.execute('INSERT INTO usuarios (nombre, email, clave, rol) VALUES (%s, %s, %s, %s)', (nombre, email, clave_hash, "barbero"))
    id_usuario = cursor.lastrowid
    
    #crear barbero asociado
    
    cursor.execute('INSERT INTO barberos (id_usuario, img_barbero) values (%s, %s)', (id_usuario, img_barbero))
    id_barbero = cursor.lastrowid
    reemplazar_disponibilidad(cursor, id_barbero, dias, hora_inicio, hora_fin)
    conn.commit()

    cursor.execute('''
        SELECT b.id_barbero, u.nombre, u.email, b.activo, b.img_barbero
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        WHERE b.id_barbero = %s
    ''', (id_barbero,))
    barbero = cursor.fetchone()
    barbero = dict(barbero)
    barbero["disponibilidad"] = disponibilidad_barbero(cursor, id_barbero)
    conn.close()
    return jsonify({"mensaje": "Barbero creado", "barbero": barbero}), 201

@admin_bp.route('/barberos/<int:id_barbero>', methods=['PATCH'])
def editar_barbero(id_barbero):
    nombre = request.form.get('nombre', '').strip()
    archivo = request.files.get('imagen')

    try:
        dias, hora_inicio, hora_fin = parsear_disponibilidad_form(request.form)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_barbero, id_usuario, img_barbero FROM barberos WHERE id_barbero = %s',
        (id_barbero,)
    )
    barbero = cursor.fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    img_barbero = barbero['img_barbero']

    if archivo and archivo.filename:
        try:
            nueva_url = subir_imagen(archivo)
        except RuntimeError as error:
            conn.close()
            return jsonify({"error": str(error)}), 500

        if not nueva_url:
            conn.close()
            return jsonify({"error": "Error al subir la imagen"}), 500

        img_barbero = nueva_url

    if nombre:
        cursor.execute('''
            UPDATE usuarios
            SET nombre = %s
            WHERE id_usuario = %s
        ''', (nombre, barbero['id_usuario']))

    cursor.execute('''
        UPDATE barberos
        SET img_barbero = %s
        WHERE id_barbero = %s
    ''', (img_barbero, id_barbero))

    try:
        reemplazar_disponibilidad(cursor, id_barbero, dias, hora_inicio, hora_fin, validar_citas=True)
    except ValueError as error:
        conn.close()
        return jsonify({"error": str(error)}), 409
    conn.commit()

    cursor.execute('''
        SELECT b.id_barbero, u.nombre, u.email, b.activo, b.img_barbero
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        WHERE b.id_barbero = %s
    ''', (id_barbero,))
    actualizado = cursor.fetchone()
    actualizado = dict(actualizado)
    actualizado["disponibilidad"] = disponibilidad_barbero(cursor, id_barbero)
    conn.close()
    return jsonify({"mensaje": "Barbero actualizado", "barbero": actualizado}), 200

@admin_bp.route('/barberos/<int:id_barbero>', methods=['DELETE'])
def eliminar_barbero(id_barbero):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Obtener id_usuario asociado
    cursor.execute('''
        SELECT id_usuario
        FROM barberos
        WHERE id_barbero = %s
        ''',(id_barbero,))
    usuario = cursor.fetchone()
    if usuario is None:
        conn.close()
        return jsonify({
            "error": "Barbero no encontrado"
        }), 404
    cursor.execute('DELETE FROM disponibilidad_barberos WHERE id_barbero = %s', (id_barbero,))
    # Eliminar barbero
    cursor.execute('DELETE FROM barberos WHERE id_barbero = %s', (id_barbero,))
    # Eliminar usuario
    cursor.execute('''
        DELETE FROM usuarios
        WHERE id_usuario = %s
        ''',(usuario['id_usuario'],))
    conn.commit()
    conn.close()
    return jsonify({"mensaje": "Barbero eliminado"})

# --- CRUD SERVICIOS ---

@admin_bp.route('/servicios', methods=['POST'])
def crear_servicio():
    nombre      = request.form.get('nombre')
    descripcion = request.form.get('descripcion', '')
    duracion    = request.form.get('duracion')
    precio      = request.form.get('precio')
    archivo     = request.files.get('imagen')

    if not nombre or not duracion or not precio:
        return jsonify({"error": "nombre, duracion y precio son obligatorios"}), 400

    img_servicio = None
    if archivo:
        try:
            img_servicio = subir_imagen(archivo)
        except RuntimeError as error:
            return jsonify({"error": str(error)}), 500
        if not img_servicio:
            return jsonify({"error": "Error al subir la imagen. Verifica el formato (png, jpg, jpeg, webp)"}), 500

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO servicios (nombre, descripcion, duracion, precio, img_servicio)
        VALUES (%s, %s, %s, %s, %s)
    ''', (nombre, descripcion, int(duracion), float(precio), img_servicio))
    id_servicio = cursor.lastrowid
    conn.commit()

    cursor.execute(
        'SELECT * FROM servicios WHERE id_servicio = %s', (id_servicio,)
    )
    servicio = cursor.fetchone()
    conn.close()

    return jsonify({"mensaje": "Servicio creado", "servicio": dict(servicio)}), 201

@admin_bp.route('/servicios/<int:id_servicio>', methods=['PATCH'])
def actualizar_servicio(id_servicio):
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    duracion = request.form.get('duracion')
    precio = request.form.get('precio')
    archivo = request.files.get('imagen')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM servicios WHERE id_servicio = %s', (id_servicio,))
    servicio = cursor.fetchone()
    if not servicio:
        conn.close()
        return jsonify({"error": "Servicio no encontrado"}), 404
    
    img_servicio = servicio['img_servicio']
    if archivo and archivo.filename:
        try:
            nueva_url = subir_imagen(archivo)
            if not nueva_url:
                conn.close()
                return jsonify({"error": "Error al subir la imagen"}), 500
            img_servicio = nueva_url
        except RuntimeError as error:
            conn.close()
            return jsonify({"error": str(error)}), 500


    nombre = nombre or servicio['nombre']
    descripcion = descripcion if descripcion is not None else servicio['descripcion']
    duracion = int(duracion) if duracion is not None else servicio['duracion']
    precio = float(precio) if precio is not None else servicio['precio']

    cursor.execute('''
        UPDATE servicios
        SET nombre = %s, descripcion = %s, duracion = %s, precio = %s, img_servicio = %s
        WHERE id_servicio = %s
    ''', (nombre, descripcion, duracion, precio, img_servicio, id_servicio))
    conn.commit()

    cursor.execute('SELECT * FROM servicios WHERE id_servicio = %s', (id_servicio,))
    actualizado = cursor.fetchone()
    conn.close()
    
    return jsonify({"mensaje": "Servicio actualizado", "servicio": dict(actualizado)}), 200



@admin_bp.route('/servicios/<int:id_servicio>', methods=['DELETE'])
def eliminar_servicio(id_servicio):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_servicio FROM servicios WHERE id_servicio = %s', (id_servicio,)
    )
    servicio = cursor.fetchone()
    if not servicio:
        conn.close()
        return jsonify({"error": "Servicio no encontrado"}), 404

    cursor.execute(
        'SELECT COUNT(*) AS total FROM citas WHERE id_servicio = %s', (id_servicio,)
    )
    citas_asociadas = cursor.fetchone()
    if citas_asociadas["total"] > 0:
        conn.close()
        return jsonify({
            "error": "No se puede eliminar el servicio porque tiene citas asociadas."
        }), 400

    cursor.execute('DELETE FROM servicios WHERE id_servicio = %s', (id_servicio,))
    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Servicio eliminado correctamente"}), 200

# CONFIGURAR HORARIOS (Update de un barbero especifico)
@admin_bp.route('/barberos/<int:id_barbero>/horarios', methods=['PATCH'])
def configurar_horario(id_barbero):
    data = request.get_json(silent=True) or {}

    if "dias" in data:
        try:
            dias = sorted({int(dia) for dia in data.get("dias", [])})
        except (TypeError, ValueError):
            return jsonify({"error": "Los dias seleccionados no son validos"}), 400

        hora_inicio = data.get("hora_inicio")
        hora_fin = data.get("hora_fin")

        if not dias:
            return jsonify({"error": "Selecciona al menos un dia de trabajo"}), 400

        if any(dia not in DIAS_DISPONIBLES for dia in dias):
            return jsonify({"error": "Los dias seleccionados deben estar entre 0 y 6"}), 400

        if not hora_inicio or not hora_fin:
            return jsonify({"error": "hora_inicio y hora_fin son obligatorios"}), 400

        try:
            inicio, fin = validar_rango_horario(hora_inicio, hora_fin)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        hora_inicio = minutos_a_hora(inicio)
        hora_fin = minutos_a_hora(fin)
    else:
        dia_semana = data.get('dia_semana')
        hora_inicio = data.get('hora_inicio')
        hora_fin = data.get('hora_fin')

        if dia_semana is None or not hora_inicio or not hora_fin:
            return jsonify({"error": "Faltan campos obligatorios"}), 400

        try:
            dia = int(dia_semana)
        except ValueError:
            return jsonify({"error": "El dia seleccionado no es valido"}), 400

        if dia not in DIAS_DISPONIBLES:
            return jsonify({"error": "El dia seleccionado debe estar entre 0 y 6"}), 400

        try:
            validar_rango_horario(hora_inicio, hora_fin)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400

        dias = [dia]
        hora_inicio = minutos_a_hora(hora_a_minutos(hora_inicio))
        hora_fin = minutos_a_hora(hora_a_minutos(hora_fin))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id_barbero FROM barberos WHERE id_barbero = %s', (id_barbero,)
    )
    barbero = cursor.fetchone()
    if not barbero:
        conn.close()
        return jsonify({"error": "Barbero no encontrado"}), 404

    try:
        reemplazar_disponibilidad(cursor, id_barbero, dias, hora_inicio, hora_fin, validar_citas=True)
    except ValueError as error:
        conn.close()
        return jsonify({"error": str(error)}), 409
    conn.commit()
    disponibilidad = disponibilidad_barbero(cursor, id_barbero)

    conn.close()
    return jsonify({"mensaje": "Horario actualizado", "disponibilidad": disponibilidad})



@admin_bp.route('/dashboard', methods=['GET'])
def estadisticas():
    conn = get_db_connection()
    cursor = conn.cursor()
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    try:
        if desde and hasta:
            desde_fecha = date.fromisoformat(desde)
            hasta_fecha = date.fromisoformat(hasta)
        else:
            hoy = date.today()
            desde_fecha = date(hoy.year, hoy.month, 1)
            hasta_fecha = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    except ValueError:
        conn.close()
        return jsonify({"error": "Formato de fecha invalido. Usar YYYY-MM-DD."}), 400

    if desde_fecha > hasta_fecha:
        conn.close()
        return jsonify({"error": "El parametro desde no puede ser mayor que hasta."}), 400

    desde = desde_fecha.isoformat()
    hasta = hasta_fecha.isoformat()

    def mes_anterior(fecha):
        if fecha.month == 1:
            return fecha.year - 1, 12
        return fecha.year, fecha.month - 1

    def rango_mes_anterior(fecha):
        anio, mes = mes_anterior(fecha)
        inicio = date(anio, mes, 1)
        fin = date(anio, mes, calendar.monthrange(anio, mes)[1])
        return inicio.isoformat(), fin.isoformat()

    def delta_pct(actual, anterior):
        actual = float(actual or 0)
        anterior = float(anterior or 0)
        if anterior == 0:
            return 0
        return round((actual - anterior) / anterior * 100, 1)

    def get_kpis(inicio, fin):
        cursor.execute('''
            SELECT
                COALESCE(SUM(CASE WHEN c.estado = 'completada' THEN s.precio ELSE 0 END), 0) AS ingresos,
                COUNT(CASE WHEN c.estado = 'completada' THEN 1 END) AS citas,
                COUNT(DISTINCT c.id_usuario) AS clientes,
                ROUND(COALESCE(AVG(r.calificacion), 0), 1) AS rating
            FROM citas c
            JOIN servicios s ON c.id_servicio = s.id_servicio
            LEFT JOIN resenias r ON c.id_cita = r.id_cita
            WHERE DATE(c.fecha) BETWEEN DATE(%s) AND DATE(%s)
        ''', (inicio, fin))
        return cursor.fetchone()

    def get_semanas_mes(anio, mes):
        primer_dia = date(anio, mes, 1)
        ultimo_dia = date(anio, mes, calendar.monthrange(anio, mes)[1])
        semanas = []
        cursor_dia = primer_dia
        semana_num = 1

        while cursor_dia <= ultimo_dia:
            fin_semana = min(cursor_dia + timedelta(days=6), ultimo_dia)
            cursor.execute('''
                SELECT COALESCE(SUM(s.precio), 0) AS monto
                FROM citas c
                JOIN servicios s ON c.id_servicio = s.id_servicio
                WHERE c.estado = 'completada'
                  AND DATE(c.fecha) BETWEEN DATE(%s) AND DATE(%s)
            ''', (cursor_dia.isoformat(), fin_semana.isoformat()))
            row = cursor.fetchone()
            semanas.append({
                "label": f"Sem {semana_num}",
                "monto": row["monto"] or 0,
            })
            cursor_dia = fin_semana + timedelta(days=1)
            semana_num += 1

        return semanas

    kpis = get_kpis(desde, hasta)
    desde_ant, hasta_ant = rango_mes_anterior(desde_fecha)
    kpis_ant = get_kpis(desde_ant, hasta_ant)

    ingresos_mes = kpis["ingresos"] or 0
    citas_completadas = kpis["citas"] or 0
    clientes_activos = kpis["clientes"] or 0
    calificacion_promedio = kpis["rating"] or 0

    stats = {
        "ingresos_mes": ingresos_mes,
        "citas_completadas": citas_completadas,
        "clientes_activos": clientes_activos,
        "calificacion_promedio": calificacion_promedio,
        "delta_ingresos": delta_pct(ingresos_mes, kpis_ant["ingresos"]),
        "delta_citas": delta_pct(citas_completadas, kpis_ant["citas"]),
        "delta_clientes": delta_pct(clientes_activos, kpis_ant["clientes"]),
        "delta_rating": delta_pct(calificacion_promedio, kpis_ant["rating"]),
        "semanas": get_semanas_mes(desde_fecha.year, desde_fecha.month),
    }

    cursor.execute('''
        SELECT c.fecha, c.hora_inicio, c.estado,
               uc.nombre AS cliente,
               ub.nombre AS barbero,
               s.nombre AS servicio
        FROM citas c
        JOIN usuarios uc ON c.id_usuario = uc.id_usuario
        JOIN barberos b ON c.id_barbero = b.id_barbero
        JOIN usuarios ub ON b.id_usuario = ub.id_usuario
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE DATE(c.fecha) BETWEEN DATE(%s) AND DATE(%s)
        ORDER BY DATE(c.fecha) DESC, c.hora_inicio DESC
        LIMIT 8
    ''', (desde, hasta))
    filas_citas = cursor.fetchall()

    estado_map = {
        "confirmada": "Confirmada",
        "completada": "Completada",
        "pendiente": "Pendiente",
        "cancelada": "Cancelada",
    }
    citas = [{
        "cliente": fila["cliente"],
        "barbero": fila["barbero"],
        "servicio": fila["servicio"],
        "hora": fila["hora_inicio"][:5],
        "estado": estado_map.get(fila["estado"], fila["estado"].capitalize()),
    } for fila in filas_citas]

    cursor.execute('''
        SELECT b.id_barbero, u.nombre,
               COUNT(c.id_cita) AS citas,
               COALESCE(SUM(s.precio), 0) AS ingresos,
               ROUND(COALESCE(AVG(r.calificacion), 0), 1) AS rating,
               b.activo, b.img_barbero
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        LEFT JOIN citas c ON b.id_barbero = c.id_barbero
                          AND c.estado = 'completada'
                          AND DATE(c.fecha) BETWEEN DATE(%s) AND DATE(%s)
        LEFT JOIN servicios s ON c.id_servicio = s.id_servicio
        LEFT JOIN resenias r ON c.id_cita = r.id_cita
        GROUP BY b.id_barbero, u.nombre, b.activo, b.img_barbero
        ORDER BY ingresos DESC
    ''', (desde, hasta))
    filas_barberos = cursor.fetchall()

    max_ingresos = max((fila["ingresos"] for fila in filas_barberos), default=1) or 1
    barberos_top = []
    for fila in filas_barberos:
        barberos_top.append({
            "id_barbero": fila["id_barbero"],
            "nombre": fila["nombre"],
            "citas": fila["citas"] or 0,
            "rating": fila["rating"] or 0,
            "ingresos": int(fila["ingresos"] or 0),
            "pct": round((fila["ingresos"] or 0) / max_ingresos * 100),
            "activo": bool(fila["activo"]),
            "img_barbero": fila["img_barbero"],
            "disponibilidad": disponibilidad_barbero(cursor, fila["id_barbero"]),
        })

    barberos = barberos_top

    cursor.execute('''
        SELECT s.nombre, s.precio, COUNT(c.id_cita) AS veces
        FROM citas c
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE DATE(c.fecha) BETWEEN DATE(%s) AND DATE(%s)
        GROUP BY c.id_servicio, s.nombre, s.precio
        ORDER BY veces DESC
    ''', (desde, hasta))
    filas_servicios_top = cursor.fetchall()

    servicios_top = [{
        "nombre": fila["nombre"],
        "precio": int(fila["precio"]),
        "veces": fila["veces"],
    } for fila in filas_servicios_top]

    cursor.execute('''
        SELECT s.id_servicio, s.nombre, s.descripcion, s.duracion, s.precio, s.img_servicio,
               COUNT(c.id_cita) AS veces_solicitado
        FROM servicios s
        LEFT JOIN citas c ON s.id_servicio = c.id_servicio
                          AND DATE(c.fecha) BETWEEN DATE(%s) AND DATE(%s)
        GROUP BY s.id_servicio, s.nombre, s.descripcion, s.duracion, s.precio, s.img_servicio
        ORDER BY veces_solicitado DESC
    ''', (desde, hasta))
    filas_servicios = cursor.fetchall()

    servicios = [{
        "id_servicio": fila["id_servicio"],
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
        "duracion_min": fila["duracion"],
        "precio": int(fila["precio"]),
        "img_servicio": fila["img_servicio"],
        "veces_solicitado": fila["veces_solicitado"],
    } for fila in filas_servicios]

    conn.close()

    return jsonify({
        "stats": stats,
        "citas": citas,
        "barberos_top": barberos_top,
        "barberos": barberos,
        "servicios_top": servicios_top,
        "servicios": servicios
    })
