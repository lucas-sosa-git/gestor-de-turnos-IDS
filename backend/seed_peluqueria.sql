INSERT INTO usuarios (nombre, email, clave, rol)
VALUES
('Juan Pérez', 'juan.perez@mail.com', 'clave123', 'cliente'),
('María Gómez', 'maria.gomez@mail.com', 'clave123', 'cliente'),
('Lucía Fernández', 'lucia.fernandez@mail.com', 'clave123', 'cliente'),
('Carlos Rodríguez', 'carlos.rodriguez@mail.com', 'clave123', 'cliente'),
('Sofía Martínez', 'sofia.martinez@mail.com', 'clave123', 'cliente'),
('Pedro López', 'pedro.lopez@peluqueria.com', 'clave123', 'barbero'),
('Ana Torres', 'ana.torres@peluqueria.com', 'clave123', 'barbero'),
('Martín Silva', 'martin.silva@peluqueria.com', 'clave123', 'barbero');

INSERT INTO barberos (id_usuario)
VALUES
(6),
(7),
(8);

INSERT INTO disponibilidad_barberos 
(id_barbero, dia_semana, hora_inicio, hora_fin)
VALUES
-- Pedro López
(1, '1', '09:00:00', '18:00:00'),
(1, '2', '09:00:00', '18:00:00'),
(1, '3', '09:00:00', '18:00:00'),
(1, '4', '09:00:00', '18:00:00'),
(1, '5', '09:00:00', '18:00:00'),

-- Ana Torres
(2, '0', '10:00:00', '19:00:00'),
(2, '2', '10:00:00', '19:00:00'),
(2, '3', '10:00:00', '19:00:00'),
(2, '4', '10:00:00', '19:00:00'),
(2, '5', '10:00:00', '19:00:00'),
(2, '6', '10:00:00', '19:00:00'),

-- Martín Silva
(3, '0', '11:00:00', '20:00:00'),
(3, '1', '11:00:00', '20:00:00'),
(3, '3', '11:00:00', '20:00:00'),
(3, '4', '11:00:00', '20:00:00'),
(3, '5', '11:00:00', '20:00:00'),
(3, '6', '11:00:00', '20:00:00');

INSERT INTO servicios (nombre, descripcion, duracion, precio)
VALUES
('Corte pelo de hombre','Corte clásico o moderno para hombre',30,15000.00),
('Corte pelo de mujer','Corte y terminación para mujer',45,45000.00),
('Barba','Recorte y perfilado de barba',25,20000.00),
('Cejas','Perfilado y limpieza de cejas',15,4000.00),
('Tintura','Aplicación de tintura completa',90,80000.00);

INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado)
VALUES
(1,1,1,'2026-05-20','10:00:00','10:30:00','pendiente'),
(2,2,2,'2026-05-20','11:00:00','11:45:00','pendiente'),
(3,1,3,'2026-05-21','12:00:00','12:25:00','confirmada'),
(4,2,4,'2026-05-21','12:30:00','12:45:00','pendiente'),
(5,3,5,'2026-05-22','13:00:00','14:30:00','confirmada');