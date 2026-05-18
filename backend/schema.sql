CREATE TABLE clientes (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(150) UNIQUE NOT NULL,
    telefono      VARCHAR(20),
    fecha_registro DATE DEFAULT CURRENT_DATE,
    activo        BOOLEAN DEFAULT TRUE
);

CREATE TABLE profesionales (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    especialidad    VARCHAR(100),
    email           VARCHAR(150) UNIQUE NOT NULL,
    telefono        VARCHAR(20),
    horario_inicio  TIME NOT NULL,
    horario_fin     TIME NOT NULL,
    dias_descanso   VARCHAR(50),
    activo          BOOLEAN DEFAULT TRUE
);

CREATE TABLE servicios (
    id                 SERIAL PRIMARY KEY,
    nombre             VARCHAR(100) NOT NULL,
    descripcion        TEXT,
    duracion_minutos   INT NOT NULL,
    precio             NUMERIC(10, 2) NOT NULL,
    categoria          VARCHAR(50),
    activo             BOOLEAN DEFAULT TRUE
);

CREATE TABLE citas (
    id                   SERIAL PRIMARY KEY,
    cliente_id           INT NOT NULL REFERENCES clientes(id),
    profesional_id       INT NOT NULL REFERENCES profesionales(id),
    fecha                DATE NOT NULL,
    hora_inicio          TIME NOT NULL,
    hora_fin             TIME NOT NULL,
    estado               VARCHAR(20) DEFAULT 'pendiente',
    notas                TEXT,
    creado_en            TIMESTAMP DEFAULT NOW(),
    cancelado_en         TIMESTAMP,
    motivo_cancelacion   TEXT
);