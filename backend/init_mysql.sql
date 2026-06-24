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
(10, 6, 2, 5, '2026-06-12', '16:00:00', '17:30:00', 'confirmada', 'qr_junio_5'),
(11, 6, 2, 5, '2026-06-20', '16:00:00', '17:30:00', 'confirmada', 'qr_junio_6');

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
(14, 2, 2, 2, '2026-05-20', '11:00:00', '11:45:00', 'confirmada'),
(15, 3, 1, 3, '2026-05-21', '12:00:00', '12:25:00', 'confirmada'),
(16, 4, 2, 4, '2026-05-21', '12:30:00', '12:45:00', 'confirmada'),
(17, 5, 3, 5, '2026-05-22', '13:00:00', '14:30:00', 'confirmada');

-- Clientes extra para poblar agendas y resenias
INSERT INTO usuarios (id_usuario, nombre, email, clave, rol)
VALUES
(20, 'Agustina Rojas', 'agustina.rojas@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(21, 'Mateo Cabrera', 'mateo.cabrera@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(22, 'Julieta Molina', 'julieta.molina@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(23, 'Bruno Arias', 'bruno.arias@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(24, 'Florencia Vega', 'florencia.vega@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
(25, 'Tomas Medina', 'tomas.medina@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente');

-- Turnos completados para enriquecer resenias
INSERT INTO citas (id_cita, id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(80, 20, 1, 1, '2026-06-08', '09:30:00', '10:00:00', 'completada', 'qr_resenia_80'),
(81, 21, 1, 3, '2026-06-09', '11:00:00', '11:25:00', 'completada', 'qr_resenia_81'),
(82, 22, 1, 2, '2026-06-11', '14:00:00', '14:45:00', 'completada', 'qr_resenia_82'),
(83, 23, 1, 4, '2026-06-12', '16:30:00', '16:45:00', 'completada', 'qr_resenia_83'),
(84, 24, 2, 2, '2026-06-09', '10:30:00', '11:15:00', 'completada', 'qr_resenia_84'),
(85, 25, 2, 5, '2026-06-10', '12:00:00', '13:30:00', 'completada', 'qr_resenia_85'),
(86, 20, 2, 1, '2026-06-12', '15:00:00', '15:30:00', 'completada', 'qr_resenia_86'),
(87, 21, 2, 3, '2026-06-13', '17:00:00', '17:25:00', 'completada', 'qr_resenia_87'),
(88, 22, 3, 5, '2026-06-08', '12:00:00', '13:30:00', 'completada', 'qr_resenia_88'),
(89, 23, 3, 1, '2026-06-10', '14:00:00', '14:30:00', 'completada', 'qr_resenia_89'),
(90, 24, 3, 3, '2026-06-12', '16:00:00', '16:25:00', 'completada', 'qr_resenia_90'),
(91, 25, 3, 2, '2026-06-13', '18:00:00', '18:45:00', 'completada', 'qr_resenia_91');

INSERT INTO resenias (id_usuario, id_cita, calificacion, comentario)
VALUES
(20, 80, 5, 'Muy prolijo y puntual. Me gusto mucho el resultado.'),
(21, 81, 4, 'Buena atencion y el perfilado quedo perfecto.'),
(22, 82, 5, 'Excelente trato, sali muy conforme.'),
(23, 83, 4, 'Servicio rapido y cuidado.'),
(24, 84, 5, 'Ana fue muy clara con las recomendaciones.'),
(25, 85, 5, 'La tintura quedo pareja y con muy buen color.'),
(20, 86, 4, 'Corte moderno, justo lo que pedi.'),
(21, 87, 5, 'Ambiente comodo y muy buena atencion.'),
(22, 88, 4, 'Buen trabajo y muy buena onda.'),
(23, 89, 5, 'Martin entendio perfecto el estilo que queria.'),
(24, 90, 4, 'Barba muy bien perfilada.'),
(25, 91, 5, 'Excelente servicio, volveria sin dudas.');

-- Turnos confirmados para mostrar en paneles de peluqueros
-- Semana del 22 de junio de 2026
INSERT INTO citas (id_cita, id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(100, 20, 1, 1, '2026-06-22', '09:00:00', '09:30:00', 'confirmada', 'qr_sem22_pedro_100'),
(101, 21, 1, 3, '2026-06-23', '11:30:00', '11:55:00', 'confirmada', 'qr_sem22_pedro_101'),
(102, 22, 1, 2, '2026-06-24', '14:00:00', '14:45:00', 'confirmada', 'qr_sem22_pedro_102'),
(103, 23, 1, 4, '2026-06-26', '16:15:00', '16:30:00', 'confirmada', 'qr_sem22_pedro_103'),
(104, 24, 2, 2, '2026-06-23', '10:00:00', '10:45:00', 'confirmada', 'qr_sem22_ana_104'),
(105, 25, 2, 5, '2026-06-24', '12:00:00', '13:30:00', 'confirmada', 'qr_sem22_ana_105'),
(106, 20, 2, 1, '2026-06-25', '15:30:00', '16:00:00', 'confirmada', 'qr_sem22_ana_106'),
(107, 21, 2, 3, '2026-06-27', '17:00:00', '17:25:00', 'confirmada', 'qr_sem22_ana_107'),
(108, 22, 3, 5, '2026-06-22', '11:00:00', '12:30:00', 'confirmada', 'qr_sem22_martin_108'),
(109, 23, 3, 1, '2026-06-24', '13:30:00', '14:00:00', 'confirmada', 'qr_sem22_martin_109'),
(110, 24, 3, 3, '2026-06-26', '16:00:00', '16:25:00', 'confirmada', 'qr_sem22_martin_110'),
(111, 25, 3, 2, '2026-06-27', '18:00:00', '18:45:00', 'confirmada', 'qr_sem22_martin_111');

-- Semana del 29 de junio de 2026
INSERT INTO citas (id_cita, id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(112, 24, 1, 1, '2026-06-29', '10:00:00', '10:30:00', 'confirmada', 'qr_sem29_pedro_112'),
(113, 25, 1, 5, '2026-06-30', '12:00:00', '13:30:00', 'confirmada', 'qr_sem29_pedro_113'),
(114, 20, 1, 3, '2026-07-01', '15:00:00', '15:25:00', 'confirmada', 'qr_sem29_pedro_114'),
(115, 21, 1, 2, '2026-07-02', '16:30:00', '17:15:00', 'confirmada', 'qr_sem29_pedro_115'),
(116, 22, 2, 1, '2026-06-30', '10:30:00', '11:00:00', 'confirmada', 'qr_sem29_ana_116'),
(117, 23, 2, 4, '2026-07-01', '12:15:00', '12:30:00', 'confirmada', 'qr_sem29_ana_117'),
(118, 24, 2, 2, '2026-07-03', '14:00:00', '14:45:00', 'confirmada', 'qr_sem29_ana_118'),
(119, 25, 2, 5, '2026-07-04', '16:00:00', '17:30:00', 'confirmada', 'qr_sem29_ana_119'),
(120, 20, 3, 3, '2026-06-29', '11:30:00', '11:55:00', 'confirmada', 'qr_sem29_martin_120'),
(121, 21, 3, 1, '2026-07-01', '13:00:00', '13:30:00', 'confirmada', 'qr_sem29_martin_121'),
(122, 22, 3, 5, '2026-07-02', '15:30:00', '17:00:00', 'confirmada', 'qr_sem29_martin_122'),
(123, 23, 3, 2, '2026-07-04', '18:00:00', '18:45:00', 'confirmada', 'qr_sem29_martin_123');
