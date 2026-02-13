USE sistemaiotA_db;

-- ===========================================
-- 1️⃣ Crear el proyecto
-- ===========================================
INSERT INTO proyectos (nombre, descripcion, tipo_industria, usuario_id)
VALUES (
  'Red de sensores para la gestión del consumo energético',
  'Proyecto IoT para la monitorización y gestión del consumo energético con sensores ambientales y eléctricos.',
  'Energía',
  1
)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

SET @proyecto_id = LAST_INSERT_ID();

-- ===========================================
-- 2️⃣ Crear el dispositivo principal
-- ===========================================
INSERT INTO dispositivos (nombre, descripcion, tipo, latitud, longitud, habilitado, fecha_creacion, proyecto_id)
VALUES (
  'Dispositivo Principal',
  'Controlador IoT con múltiples sensores conectados.',
  'ESP32',
  18.5, -88.3,
  TRUE,
  NOW(),
  @proyecto_id
)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

SET @dispositivo_id = LAST_INSERT_ID();

-- ===========================================
-- 3️⃣ Crear sensores (evita duplicados)
-- ===========================================
INSERT INTO sensores (nombre, tipo, fecha_creacion, habilitado, dispositivo_id)
VALUES ('DHT22', 'Ambiente', NOW(), TRUE, @dispositivo_id)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @sensor_dht22 = LAST_INSERT_ID();

INSERT INTO sensores (nombre, tipo, fecha_creacion, habilitado, dispositivo_id)
VALUES ('SCT-013-000', 'Corriente', NOW(), TRUE, @dispositivo_id)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @sensor_sct = LAST_INSERT_ID();

INSERT INTO sensores (nombre, tipo, fecha_creacion, habilitado, dispositivo_id)
VALUES ('BH1750', 'Luz', NOW(), TRUE, @dispositivo_id)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @sensor_bh1750 = LAST_INSERT_ID();

INSERT INTO sensores (nombre, tipo, fecha_creacion, habilitado, dispositivo_id)
VALUES ('PIR HC-SR501', 'Movimiento', NOW(), TRUE, @dispositivo_id)
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);
SET @sensor_pir = LAST_INSERT_ID();

-- ===========================================
-- 4️⃣ Crear campos para cada sensor
-- ===========================================

ALTER TABLE campos_sensores 
ADD UNIQUE KEY unique_nombre_sensor (nombre, sensor_id);

-- DHT22
INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Temperatura', 'FLOAT', @sensor_dht22, id FROM unidades_medida WHERE nombre = 'Celsius'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Humedad', 'FLOAT', @sensor_dht22, id FROM unidades_medida WHERE nombre = 'Humedad Relativa'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

-- SCT-013-000
INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Energia', 'FLOAT', @sensor_sct, id FROM unidades_medida WHERE nombre = 'Kilowatt-hora'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Corriente', 'FLOAT', @sensor_sct, id FROM unidades_medida WHERE nombre = 'Amperios'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Potencia', 'FLOAT', @sensor_sct, id FROM unidades_medida WHERE nombre = 'Watts'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

-- BH1750
INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Iluminacion', 'FLOAT', @sensor_bh1750, id FROM unidades_medida WHERE nombre = 'Lux'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

-- PIR HC-SR501
INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id)
SELECT 'Movimiento', 'BOOLEAN', @sensor_pir, id FROM unidades_medida WHERE nombre = 'Booleano (Estado)'
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id);

-- ===========================================
-- 5️⃣ Insertar valores del paquete JSON
-- ===========================================
SET @fecha_lectura = '2025-10-21 14:03:00';

-- DHT22
INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '22.5', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Temperatura' AND sensor_id = @sensor_dht22;

INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '78.9', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Humedad' AND sensor_id = @sensor_dht22;

-- SCT-013-000
INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '123.7', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Energia' AND sensor_id = @sensor_sct;

INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '23.45', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Corriente' AND sensor_id = @sensor_sct;

INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '245.1', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Potencia' AND sensor_id = @sensor_sct;

-- BH1750
INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '684', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Iluminacion' AND sensor_id = @sensor_bh1750;

-- PIR HC-SR501
INSERT INTO valores (valor, fecha_hora_lectura, campo_id)
SELECT '1', @fecha_lectura, id FROM campos_sensores WHERE nombre = 'Movimiento' AND sensor_id = @sensor_pir;
