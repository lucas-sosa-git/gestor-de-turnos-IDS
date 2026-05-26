DROP DATABASE IF EXISTS barberia_db;
CREATE DATABASE barberia_db;
USE barberia_db;

CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    contraseña VARCHAR(255) NOT NULL,
    rol ENUM('cliente', 'administrador', 'barbero') NOT NULL
);

CREATE TABLE servicios (
    id_servicio INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    duracion INT NOT NULL, 
    precio DECIMAL(10, 2) NOT NULL
);

CREATE TABLE barberos (
    id_barbero INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT 1,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

CREATE TABLE disponibilidad_barberos (
    id_disp INT AUTO_INCREMENT PRIMARY KEY,
    id_barbero INT NOT NULL,
    dia_semana ENUM('0', '1', '2', '3', '4', '5', '6') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    FOREIGN KEY (id_barbero) REFERENCES barberos(id_barbero)
);

CREATE TABLE citas (
    id_cita INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_barbero INT NOT NULL,
    id_servicio INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    estado ENUM('pendiente', 'confirmada', 'cancelada') NOT NULL DEFAULT 'pendiente',
    ausencia BOOLEAN NOT NULL DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_barbero) REFERENCES barberos(id_barbero),
    FOREIGN KEY (id_servicio) REFERENCES servicios(id_servicio)
);

CREATE TABLE resenias (
    id_resenia INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_cita INT NOT NULL UNIQUE,
    calificacion INT NOT NULL CHECK (calificacion >= 1 AND calificacion <= 5),
    comentario TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    FOREIGN KEY (id_cita) REFERENCES citas(id_cita)
);

#PRUEBAS 

INSERT INTO usuarios (nombre, email, contraseña, rol) VALUES 
('Gabriel Hauche', 'gabrielhauche@ejemplo.com', 'contrasena111', 'cliente'),
('Daniel Osvaldo', 'danielosvaldo@ejemplo.com', 'contrasena333', 'barbero');

INSERT INTO servicios (nombre, descripcion, duracion, precio) VALUES 
('Corte de cabello', 'Corte de cabello clásico', 30, 15000.00),
('Afeitado', 'Afeitado tradicional con navaja', 20, 10000.00);

INSERT INTO barberos (id_usuario) VALUES 
(2);

INSERT INTO disponibilidad_barberos (id_barbero, dia_semana, hora_inicio, hora_fin) VALUES 
(1, '1', '09:00:00', '17:00:00'),
(1, '2', '09:00:00', '17:00:00'),
(1, '3', '09:00:00', '17:00:00'),
(1, '4', '09:00:00', '17:00:00'),
(1, '5', '09:00:00', '17:00:00');

INSERT INTO citas (id_usuario, id_barbero, id_servicio, fecha, hora_inicio, hora_fin, estado) VALUES 
(1, 1, 1, '2024-07-01', '10:00:00', '10:30:00', 'confirmada'),
(1, 1, 2, '2024-07-02', '11:00:00', '11:20:00', 'pendiente');