INSERT INTO clientes (nombre, email, telefono)
VALUES
('Juan Pérez', 'juan.perez@mail.com', '1122334455'),
('María Gómez', 'maria.gomez@mail.com', '1133445566'),
('Lucía Fernández', 'lucia.fernandez@mail.com', '1144556677'),
('Carlos Rodríguez', 'carlos.rodriguez@mail.com', '1155667788'),
('Sofía Martínez', 'sofia.martinez@mail.com', '1166778899');

INSERT INTO profesionales (nombre, especialidad, email, telefono, horario_inicio, horario_fin, dias_descanso)
VALUES
('Pedro López', 'Barbero', 'pedro.lopez@peluqueria.com', '1177889900', '09:00', '18:00', 'Domingo'),
('Ana Torres', 'Peluquera', 'ana.torres@peluqueria.com', '1188990011', '10:00', '19:00', 'Lunes'),
('Martín Silva', 'Colorista', 'martin.silva@peluqueria.com', '1199001122', '11:00', '20:00', 'Martes');

INSERT INTO servicios (nombre, descripcion, duracion_minutos, precio, categoria)
VALUES
('Corte pelo de hombre', 'Corte clásico o moderno para hombre', 30, 15000.00, 'Peluquería'),
('Corte pelo de mujer', 'Corte y terminación para mujer', 45, 45000.00, 'Peluquería'),
('Barba', 'Recorte y perfilado de barba', 25, 20000.00, 'Barbería'),
('Cejas', 'Perfilado y limpieza de cejas', 15, 4000.00, 'Estética'),
('Tintura', 'Aplicación de tintura completa', 90, 80000.00, 'Coloración');

INSERT INTO citas (cliente_id, profesional_id, servicio_id, fecha, hora_inicio, hora_fin, estado, notas)
VALUES
(1, 1, 1, '2026-05-20', '10:00', '10:30', 'pendiente', 'Turno para corte de pelo de hombre'),
(2, 2, 2, '2026-05-20', '11:00', '11:45', 'pendiente', 'Turno para corte de pelo de mujer'),
(3, 1, 3, '2026-05-21', '12:00', '12:25', 'confirmado', 'Turno para barba'),
(4, 2, 4, '2026-05-21', '15:00', '15:15', 'pendiente', 'Turno para cejas'),
(5, 3, 5, '2026-05-22', '16:00', '17:30', 'confirmado', 'Turno para tintura');
