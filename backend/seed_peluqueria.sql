--clave123 = 5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5
--admin1234 = ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270

-- Admin
INSERT INTO usuarios (nombre, email, clave, rol)
VALUES ('Admin', 'admin@barberia.com', 'ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270', 'administrador');

-- Clientes y barberos
INSERT INTO usuarios (nombre, email, clave, rol)
VALUES
('Juan Pérez', 'juan.perez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('María Gómez', 'maria.gomez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('Lucía Fernández', 'lucia.fernandez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('Carlos Rodríguez', 'carlos.rodriguez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('Sofía Martínez', 'sofia.martinez@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('Pedro López', 'pedro.lopez@peluqueria.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'barbero'),
('Ana Torres', 'ana.torres@peluqueria.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'barbero'),
('Martín Silva', 'martin.silva@peluqueria.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'barbero');

-- Barberos (los IDs cambiaron porque ahora el admin es el id 1)
INSERT INTO barberos (id_usuario, img_barbero)
VALUES
(7, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/6ca320f4f4194d8e9bf2ddc872750963.png'),
(8, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/9e62a088d91c4da383c0a2674dcf3bbb.jpg'),
(9, NULL);

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

INSERT INTO servicios (nombre, descripcion, duracion, precio, img_servicio)
VALUES
('Corte pelo de hombre', 'Corte clásico o moderno para hombre', 30, 15000.00, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/8d1aaf567e86412aae29bb862937692d.jpeg'),
('Corte pelo de mujer', 'Corte y terminación para mujer', 45, 45000.00, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/83aacaf513d14922b91ad3a6bca0f844.png'),
('Barba', 'Recorte y perfilado de barba', 25, 20000.00, 'https://cstrkukbiiodroebybcv.supabase.co/storage/v1/object/public/gestor-imagenes/c910af5c4648404e9dc4422c9c41ebc4.jpeg'),
('Cejas', 'Perfilado y limpieza de cejas', 15, 4000.00, NULL),
('Tintura', 'Aplicación de tintura completa', 90, 80000.00, NULL);

INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(2, 1, 1, '2026-05-20', '10:00:00', '10:30:00', 'confirmada',    'qr_token_demo_1'),
(3, 2, 2, '2026-05-20', '11:00:00', '11:45:00', 'confirmada',    'qr_token_demo_2'),
(4, 1, 3, '2026-05-21', '12:00:00', '12:25:00', 'confirmada',   'qr_token_demo_3'),
(5, 2, 4, '2026-05-21', '15:00:00', '15:15:00', 'confirmada',    'qr_token_demo_4'),
(6, 3, 5, '2026-05-22', '16:00:00', '17:30:00', 'confirmada',   'qr_token_demo_5');

-- mas datos para el dashboard.html
INSERT INTO usuarios (nombre, email, clave, rol)
VALUES
('Valentina Ruiz', 'valentina@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('Nicolás Herrera', 'nicolas@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente'),
('Camila Soto', 'camila@mail.com', '5ac0852e770506dcd80f1a36d20ba7878bf82244b836d9324593bd14bc56dcb5', 'cliente');

-- Datos de prueba para estadísticas de junio
INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado, qr_token)
VALUES
(2, 1, 1, '2026-06-03', '10:00:00', '10:30:00', 'confirmada', 'qr_junio_1'),
(3, 2, 2, '2026-06-04', '11:00:00', '11:45:00', 'confirmada', 'qr_junio_2'),
(4, 1, 3, '2026-06-05', '12:00:00', '12:25:00', 'cancelada', 'qr_junio_3'),
(5, 3, 1, '2026-06-10', '15:00:00', '15:30:00', 'confirmada', 'qr_junio_4'),
(6, 2, 5, '2026-06-12', '16:00:00', '17:30:00', 'pendiente', 'qr_junio_5'),
(6, 2, 5, '2026-06-20', '16:00:00', '17:30:00', 'pendiente', 'qr_junio_6');

INSERT INTO resenias (id_usuario, id_cita, calificacion, comentario)
VALUES
(2, 1, 5, 'Excelente atención'),
(3, 2, 4, 'Muy buen servicio'),
(4, 3, 5, 'Todo perfecto'),
(2, 6, 5, 'Excelente corte'),
(3, 7, 4, 'Muy buena atención'),
(5, 9, 5, 'Rapido y prolijo');
INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado)
VALUES
(1,1,1,'2026-05-20','10:00:00','10:30:00','pendiente'),
(1,1,5, '2026-05-22', '10:00:00','11:30:00', 'confirmada'),
(2,2,2,'2026-05-20','11:00:00','11:45:00','pendiente'),
(3,1,3,'2026-05-21','12:00:00','12:25:00','confirmada'),
(4,2,4,'2026-05-21','12:30:00','12:45:00','pendiente'),
(5,3,5,'2026-05-22','13:00:00','14:30:00','confirmada');
