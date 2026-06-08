DROP TABLE IF EXISTS resenias;
DROP TABLE IF EXISTS citas;
DROP TABLE IF EXISTS disponibilidad_barberos;
DROP TABLE IF EXISTS barberos;
DROP TABLE IF EXISTS servicios;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    clave   TEXT NOT NULL,
    rol         TEXT NOT NULL CHECK (rol IN ('cliente', 'administrador', 'barbero'))
);

CREATE TABLE IF NOT EXISTS servicios (
    id_servicio  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre       TEXT NOT NULL,
    descripcion  TEXT,
    duracion     INTEGER NOT NULL,
    precio       REAL NOT NULL,
    img_servicio TEXT
);

CREATE TABLE IF NOT EXISTS barberos (
    id_barbero  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario  INTEGER NOT NULL UNIQUE,
    activo      INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE IF NOT EXISTS disponibilidad_barberos (
    id_disp      INTEGER PRIMARY KEY AUTOINCREMENT,
    id_barbero   INTEGER NOT NULL,
    dia_semana   INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_inicio  TEXT NOT NULL,
    hora_fin     TEXT NOT NULL,
    FOREIGN KEY (id_barbero) REFERENCES barberos(id_barbero)
);

CREATE TABLE IF NOT EXISTS citas (
    id_cita           INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario        INTEGER NOT NULL,
    id_barbero        INTEGER NOT NULL,
    id_servicio       INTEGER NOT NULL,
    fecha             TEXT NOT NULL,
    hora_inicio       TEXT NOT NULL,
    hora_fin          TEXT NOT NULL,
    estado            TEXT NOT NULL DEFAULT 'confirmada' CHECK (estado IN ('confirmada', 'completada', 'pendiente', 'cancelada')),
    ausencia          INTEGER NOT NULL DEFAULT 0,
    fecha_creacion    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cancelacion TIMESTAMP NULL DEFAULT NULL,
    qr_token          TEXT NULL UNIQUE,
    FOREIGN KEY (id_usuario)  REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_barbero)  REFERENCES barberos(id_barbero),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);

CREATE TABLE IF NOT EXISTS resenias (
    id_resenia     INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario     INTEGER NOT NULL,
    id_cita        INTEGER NOT NULL UNIQUE,
    calificacion   INTEGER NOT NULL CHECK (calificacion BETWEEN 1 AND 5),
    comentario     TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_cita)    REFERENCES citas(id_cita)
);
