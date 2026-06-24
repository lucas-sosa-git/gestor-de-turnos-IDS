SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

ALTER DATABASE `gestor_de_turnos`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    clave VARCHAR(255) NOT NULL,
    rol VARCHAR(32) NOT NULL,
    CHECK (rol IN ('cliente', 'administrador', 'barbero'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS servicios (
    id_servicio INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    duracion INT NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    img_servicio TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS barberos (
    id_barbero INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    img_barbero TEXT,
    CONSTRAINT fk_barberos_usuarios
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS disponibilidad_barberos (
    id_disp INT AUTO_INCREMENT PRIMARY KEY,
    id_barbero INT NOT NULL,
    dia_semana INT NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    CHECK (dia_semana BETWEEN 0 AND 6),
    CONSTRAINT fk_disponibilidad_barberos
        FOREIGN KEY (id_barbero) REFERENCES barberos(id_barbero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_disponibilidad_barbero_dia
    ON disponibilidad_barberos (id_barbero, dia_semana);

CREATE TABLE IF NOT EXISTS citas (
    id_cita INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_barbero INT NOT NULL,
    id_servicio INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado VARCHAR(32) NOT NULL DEFAULT 'confirmada',
    ausencia TINYINT(1) NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cancelacion TIMESTAMP NULL DEFAULT NULL,
    qr_token VARCHAR(255) NULL UNIQUE,
    CHECK (estado IN ('confirmada', 'completada', 'pendiente', 'cancelada')),
    CONSTRAINT fk_citas_usuarios
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_citas_barberos
        FOREIGN KEY (id_barbero) REFERENCES barberos(id_barbero),
    CONSTRAINT fk_citas_servicios
        FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_citas_barbero_fecha_hora
    ON citas (id_barbero, fecha, hora_inicio, hora_fin);

CREATE INDEX idx_citas_usuario_estado
    ON citas (id_usuario, estado);

CREATE TABLE IF NOT EXISTS resenias (
    id_resenia INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_cita INT NOT NULL UNIQUE,
    calificacion INT NOT NULL,
    comentario TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (calificacion BETWEEN 1 AND 5),
    CONSTRAINT fk_resenias_usuarios
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_resenias_citas
        FOREIGN KEY (id_cita) REFERENCES citas(id_cita)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- clave123 = 5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5
-- admin1234 = ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270

-- Admin
INSERT INTO usuarios (id_usuario, nombre, email, clave, rol)
VALUES
(1, 'Admin', 'admin@barberia.com', 'ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270', 'administrador');

-- Clientes y barberos
INSERT INTO usuarios (id_usuario, nombre, email, clave, rol)
VALUES
(2, 'Juan Pérez', 'juan.perez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(3, 'María Gómez', 'maria.gomez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(4, 'Lucía Fernández', 'lucia.fernandez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(5, 'Carlos Rodríguez', 'carlos.rodriguez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(6, 'Sofía Martínez', 'sofia.martinez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(7, 'Pedro López', 'pedro.lopez@peluqueria.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'barbero'),
(8, 'Ana Torres', 'ana.torres@peluqueria.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'barbero'),
(9, 'Martín Silva', 'martin.silva@peluqueria.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'barbero');

-- Barberos
INSERT INTO barberos (id_barbero, id_usuario, img_barbero)
VALUES
(1, 7, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/render/image/public/gestor-imagenes/6ca320f4f4194d8e9bf2ddc872750963.png?width=300&height=300&resize=cover'),
(2, 8, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/render/image/public/gestor-imagenes/9e62a088d91c4da383c0a2674dcf3bbb.jpg?width=300&height=300&resize=cover'),
(3, 9, NULL);

INSERT INTO disponibilidad_barberos (id_barbero, dia_semana, hora_inicio, hora_fin)
VALUES
-- Pedro López
(1, 1, '09:00:00', '18:00:00'),
(1, 2, '09:00:00', '18:00:00'),
(1, 3, '09:00:00', '18:00:00'),
(1, 4, '09:00:00', '18:00:00'),
(1, 5, '09:00:00', '18:00:00'),
-- Ana Torres
(2, 0, '10:00:00', '19:00:00'),
(2, 2, '10:00:00', '19:00:00'),
(2, 3, '10:00:00', '19:00:00'),
(2, 4, '10:00:00', '19:00:00'),
(2, 5, '10:00:00', '19:00:00'),
(2, 6, '10:00:00', '19:00:00'),
-- Martín Silva
(3, 0, '11:00:00', '20:00:00'),
(3, 1, '11:00:00', '20:00:00'),
(3, 3, '11:00:00', '20:00:00'),
(3, 4, '11:00:00', '20:00:00'),
(3, 5, '11:00:00', '20:00:00'),
(3, 6, '11:00:00', '20:00:00');

INSERT INTO servicios (id_servicio, nombre, descripcion, duracion, precio, img_servicio)
VALUES
(1, 'Corte pelo de hombre', 'Corte clásico o moderno para hombre', 30, 15000.00, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/8d1aaf567e86412aae29bb862937692d.jpeg'),
(2, 'Corte pelo de mujer', 'Corte y terminación para mujer', 45, 45000.00, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/83aacaf513d14922b91ad3a6bca0f844.png'),
(3, 'Barba', 'Recorte y perfilado de barba', 25, 20000.00, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/c910af5c4648404e9dc4422c9c41ebc4.jpeg'),
(4, 'Cejas', 'Perfilado y limpieza de cejas', 15, 4000.00, NULL),
(5, 'Tintura', 'Aplicación de tintura completa', 90, 80000.00, NULL);

INSERT INTO citas (id_cita, id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(1, 2, 1, 1, '2026-05-20', '10:00:00', '10:30:00', 'confirmada', 'qr_token_demo_1'),
(2, 3, 2, 2, '2026-05-20', '11:00:00', '11:45:00', 'confirmada', 'qr_token_demo_2'),
(3, 4, 1, 3, '2026-05-21', '12:00:00', '12:25:00', 'confirmada', 'qr_token_demo_3'),
(4, 5, 2, 4, '2026-05-21', '15:00:00', '15:15:00', 'confirmada', 'qr_token_demo_4'),
(5, 6, 3, 5, '2026-05-22', '16:00:00', '17:30:00', 'confirmada', 'qr_token_demo_5');

-- Mas datos para el dashboard.html
INSERT INTO usuarios (id_usuario, nombre, email, clave, rol)
VALUES
(10, 'Valentina Ruiz', 'valentina@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(11, 'Nicolás Herrera', 'nicolas@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(12, 'Camila Soto', 'camila@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente');

-- Datos de prueba para estadísticas de junio
INSERT INTO citas (id_cita, id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(6, 2, 1, 1, '2026-06-03', '10:00:00', '10:30:00', 'confirmada', 'qr_junio_1'),
(7, 3, 2, 2, '2026-06-04', '11:00:00', '11:45:00', 'confirmada', 'qr_junio_2'),
(8, 4, 1, 3, '2026-06-05', '12:00:00', '12:25:00', 'cancelada', 'qr_junio_3'),
(9, 5, 3, 1, '2026-06-10', '15:00:00', '15:30:00', 'confirmada', 'qr_junio_4'),
(10, 6, 2, 5, '2026-06-12', '16:00:00', '17:30:00', 'pendiente', 'qr_junio_5'),
(11, 6, 2, 5, '2026-06-20', '16:00:00', '17:30:00', 'pendiente', 'qr_junio_6');

INSERT INTO resenias (id_usuario, id_cita, calificacion, comentario)
VALUES
(2, 1, 5, 'Excelente atención'),
(3, 2, 4, 'Muy buen servicio'),
(4, 3, 5, 'Todo perfecto'),
(2, 6, 5, 'Excelente corte'),
(3, 7, 4, 'Muy buena atención'),
(5, 9, 5, 'Rapido y prolijo');

INSERT INTO citas (id_cita, id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado)
VALUES
(12, 2, 1, 1, '2026-05-20', '10:00:00', '10:30:00', 'completada'),
(13, 1, 1, 5, '2026-05-22', '10:00:00', '11:30:00', 'confirmada'),
(14, 2, 2, 2, '2026-05-20', '11:00:00', '11:45:00', 'pendiente'),
(15, 3, 1, 3, '2026-05-21', '12:00:00', '12:25:00', 'confirmada'),
(16, 4, 2, 4, '2026-05-21', '12:30:00', '12:45:00', 'pendiente'),
(17, 5, 3, 5, '2026-05-22', '13:00:00', '14:30:00', 'confirmada');