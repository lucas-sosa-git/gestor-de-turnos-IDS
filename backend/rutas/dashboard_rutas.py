from flask import Blueprint, render_template, request
from db import get_db_connection
from datetime import date, timedelta
import calendar

dashboard_bp = Blueprint('dashboard', __name__)


def get_semanas_mes(conn, year, month):
    """Devuelve ingresos por semana del mes indicado (solo citas confirmadas)."""
    primer_dia = date(year, month, 1)
    ultimo_dia = date(year, month, calendar.monthrange(year, month)[1])

    semanas = []
    cursor_dia = primer_dia
    semana_num = 1

    while cursor_dia <= ultimo_dia:
        fin_semana = min(cursor_dia + timedelta(days=6), ultimo_dia)
        row = conn.execute('''
            SELECT COALESCE(SUM(s.precio), 0) AS monto
            FROM citas c
            JOIN servicios s ON c.id_servicio = s.id_servicio
            WHERE c.estado = 'confirmada'
              AND DATE(c.fecha) BETWEEN ? AND ?
        ''', (cursor_dia.isoformat(), fin_semana.isoformat())).fetchone()

        semanas.append({
            'label': f'Sem {semana_num}',
            'monto': row['monto']
        })
        cursor_dia = fin_semana + timedelta(days=1)
        semana_num += 1

    return semanas


@dashboard_bp.route('/dashboard')
def vista_dashboard():
    conn = get_db_connection()
    hoy = date.today()

    # Rango: mes actual
    primer_dia_mes = date(hoy.year, hoy.month, 1)
    ultimo_dia_mes = date(hoy.year, hoy.month, calendar.monthrange(hoy.year, hoy.month)[1])
    desde = primer_dia_mes.isoformat()
    hasta = ultimo_dia_mes.isoformat()

    # ── KPIs del mes actual ──────────────────────────────────────────────
    ingresos_mes = conn.execute('''
        SELECT COALESCE(SUM(s.precio), 0) AS total
        FROM citas c
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.estado = 'confirmada'
          AND DATE(c.fecha) BETWEEN ? AND ?
    ''', (desde, hasta)).fetchone()['total']

    citas_completadas = conn.execute('''
        SELECT COUNT(*) AS total FROM citas
        WHERE estado = 'confirmada'
          AND DATE(fecha) BETWEEN ? AND ?
    ''', (desde, hasta)).fetchone()['total']

    clientes_activos = conn.execute('''
        SELECT COUNT(DISTINCT id_usuario) AS total FROM citas
        WHERE DATE(fecha) BETWEEN ? AND ?
    ''', (desde, hasta)).fetchone()['total']

    calificacion_promedio = conn.execute('''
        SELECT ROUND(COALESCE(AVG(r.calificacion), 0), 1) AS prom
        FROM resenias r
        JOIN citas c ON r.id_cita = c.id_cita
        WHERE DATE(c.fecha) BETWEEN ? AND ?
    ''', (desde, hasta)).fetchone()['prom']

    # ── KPIs del mes anterior (para deltas) ─────────────────────────────
    if hoy.month == 1:
        año_ant, mes_ant = hoy.year - 1, 12
    else:
        año_ant, mes_ant = hoy.year, hoy.month - 1

    primer_dia_ant = date(año_ant, mes_ant, 1)
    ultimo_dia_ant = date(año_ant, mes_ant, calendar.monthrange(año_ant, mes_ant)[1])
    desde_ant = primer_dia_ant.isoformat()
    hasta_ant = ultimo_dia_ant.isoformat()

    ingresos_ant = conn.execute('''
        SELECT COALESCE(SUM(s.precio), 0) AS total
        FROM citas c
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE c.estado = 'confirmada'
          AND DATE(c.fecha) BETWEEN ? AND ?
    ''', (desde_ant, hasta_ant)).fetchone()['total']

    citas_ant = conn.execute('''
        SELECT COUNT(*) AS total FROM citas
        WHERE estado = 'confirmada'
          AND DATE(fecha) BETWEEN ? AND ?
    ''', (desde_ant, hasta_ant)).fetchone()['total']

    clientes_ant = conn.execute('''
        SELECT COUNT(DISTINCT id_usuario) AS total FROM citas
        WHERE DATE(fecha) BETWEEN ? AND ?
    ''', (desde_ant, hasta_ant)).fetchone()['total']

    calif_ant = conn.execute('''
        SELECT ROUND(COALESCE(AVG(r.calificacion), 0), 1) AS prom
        FROM resenias r
        JOIN citas c ON r.id_cita = c.id_cita
        WHERE DATE(c.fecha) BETWEEN ? AND ?
    ''', (desde_ant, hasta_ant)).fetchone()['prom']

    def delta_pct(actual, anterior):
        if anterior == 0:
            return '+0'
        cambio = round((actual - anterior) / anterior * 100, 1)
        return f'+{cambio}' if cambio >= 0 else str(cambio)

    stats = {
        'ingresos_mes': ingresos_mes,
        'citas_completadas': citas_completadas,
        'clientes_activos': clientes_activos,
        'calificacion_promedio': calificacion_promedio if calificacion_promedio else '—',
        'delta_ingresos': delta_pct(ingresos_mes, ingresos_ant),
        'delta_citas': delta_pct(citas_completadas, citas_ant),
        'delta_clientes': delta_pct(clientes_activos, clientes_ant),
        'delta_rating': delta_pct(float(calificacion_promedio or 0), float(calif_ant or 0)),
        'semanas': get_semanas_mes(conn, hoy.year, hoy.month),
    }

    # ── Citas recientes (últimas 8) ──────────────────────────────────────
    filas_citas = conn.execute('''
        SELECT c.fecha, c.hora_inicio, c.estado,
               u.nombre  AS cliente,
               ub.nombre AS barbero,
               s.nombre  AS servicio
        FROM citas c
        JOIN usuarios u   ON c.id_usuario  = u.id_usuario
        JOIN barberos b   ON c.id_barbero  = b.id_barbero
        JOIN usuarios ub  ON b.id_usuario  = ub.id_usuario
        JOIN servicios s  ON c.id_servicio = s.id_servicio
        ORDER BY c.fecha DESC, c.hora_inicio DESC
        LIMIT 8
    ''').fetchall()

    estado_map = {'confirmada': 'Completada', 'pendiente': 'Pendiente', 'cancelada': 'Cancelada'}
    citas = []
    for fila in filas_citas:
        citas.append({
            'cliente':  fila['cliente'],
            'barbero':  fila['barbero'],
            'servicio': fila['servicio'],
            'hora':     fila['hora_inicio'][:5],
            'estado':   estado_map.get(fila['estado'], fila['estado'].capitalize()),
        })

    # ── Barberos top (por ingresos del mes) ─────────────────────────────
    filas_barberos = conn.execute('''
        SELECT u.nombre,
               COUNT(c.id_cita)            AS turnos,
               COALESCE(SUM(s.precio), 0)  AS ingresos,
               ROUND(COALESCE(AVG(r.calificacion), 0), 1) AS calif,
               b.activo
        FROM barberos b
        JOIN usuarios u ON b.id_usuario = u.id_usuario
        LEFT JOIN citas c   ON b.id_barbero = c.id_barbero
                            AND c.estado = 'confirmada'
                            AND DATE(c.fecha) BETWEEN ? AND ?
        LEFT JOIN servicios s ON c.id_servicio = s.id_servicio
        LEFT JOIN resenias r  ON c.id_cita    = r.id_cita
        GROUP BY b.id_barbero
        ORDER BY ingresos DESC
    ''', (desde, hasta)).fetchall()

    max_ing = max((r['ingresos'] for r in filas_barberos), default=1) or 1
    barberos_top = []
    for fila in filas_barberos:
        barberos_top.append({
            'nombre':  fila['nombre'],
            'citas':   fila['turnos'],
            'rating':  fila['calif'] if fila['calif'] else '—',
            'ingresos': int(fila['ingresos']),
            'pct':     round(fila['ingresos'] / max_ing * 100),
            'activo':  bool(fila['activo']),
        })

    # Variable barberos completa para el tab de barberos
    barberos = barberos_top

    # ── Servicios más solicitados del mes ────────────────────────────────
    filas_servicios_top = conn.execute('''
        SELECT s.nombre, s.precio, COUNT(c.id_cita) AS veces
        FROM citas c
        JOIN servicios s ON c.id_servicio = s.id_servicio
        WHERE DATE(c.fecha) BETWEEN ? AND ?
        GROUP BY c.id_servicio
        ORDER BY veces DESC
    ''', (desde, hasta)).fetchall()

    servicios_top = [
        {'nombre': r['nombre'], 'precio': int(r['precio']), 'veces': r['veces']}
        for r in filas_servicios_top
    ]

    # ── Catálogo completo de servicios ───────────────────────────────────
    filas_servicios = conn.execute('''
        SELECT s.id_servicio, s.nombre, s.descripcion, s.duracion, s.precio,
               COUNT(c.id_cita) AS veces_mes
        FROM servicios s
        LEFT JOIN citas c ON s.id_servicio = c.id_servicio
                          AND DATE(c.fecha) BETWEEN ? AND ?
        GROUP BY s.id_servicio
        ORDER BY veces_mes DESC
    ''', (desde, hasta)).fetchall()

    servicios = [
        {
            'nombre':          r['nombre'],
            'descripcion':     r['descripcion'],
            'duracion_min':    r['duracion'],
            'precio':          int(r['precio']),
            'veces_solicitado': r['veces_mes'],
        }
        for r in filas_servicios
    ]

    conn.close()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        citas=citas,
        barberos_top=barberos_top,
        barberos=barberos,
        servicios_top=servicios_top,
        servicios=servicios,
    )
