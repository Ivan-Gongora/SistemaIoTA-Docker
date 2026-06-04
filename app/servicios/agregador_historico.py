import pymysql
import logging
import traceback
from datetime import datetime
import pymysql
from typing import List, Dict, Any
from app.api.modelos.recepcion_datos import PayloadDispositivo
from app.servicios.servicio_simulacion import get_db_connection

logging.basicConfig(level=logging.INFO)

def procesar_agregaciones_historicas(dispositivo_id, fecha_inicio, fecha_fin):
    conexion = get_db_connection()
    try:
        cursor = conexion.cursor()
        
        sql_minutos = """
        INSERT IGNORE INTO valores_agregados_minuto (
            campo_id, timestamp_minuto, valor_avg, valor_max, valor_min, valor_sum, valor_texto, total_registros
        )
        SELECT 
            v.campo_id,
            FROM_UNIXTIME((UNIX_TIMESTAMP(v.fecha_hora_lectura) DIV 60) * 60),
            AVG(v.valor),
            MAX(v.valor),
            MIN(v.valor),
            SUM(v.valor),
            MAX(v.valor_texto),
            COUNT(v.id)
        FROM valores v
        JOIN campos_sensores c ON v.campo_id = c.id
        JOIN sensores s ON c.sensor_id = s.id
        WHERE s.dispositivo_id = %s 
          AND v.fecha_hora_lectura >= %s 
          AND v.fecha_hora_lectura <= %s
          AND (v.valor IS NOT NULL OR v.valor_texto IS NOT NULL)
        GROUP BY v.campo_id, FROM_UNIXTIME((UNIX_TIMESTAMP(v.fecha_hora_lectura) DIV 60) * 60)
        """
        cursor.execute(sql_minutos, (dispositivo_id, fecha_inicio, fecha_fin))

        sql_horas = """
        INSERT IGNORE INTO valores_agregados (
            campo_id, fecha, hora, valor_min, valor_max, valor_avg, valor_sum, valor_texto, total_registros
        )
        SELECT
            v.campo_id,
            DATE(v.fecha_hora_lectura),
            HOUR(v.fecha_hora_lectura),
            MIN(v.valor),
            MAX(v.valor),
            AVG(v.valor),
            SUM(v.valor),
            MAX(v.valor_texto),
            COUNT(v.id)
        FROM valores v
        JOIN campos_sensores c ON v.campo_id = c.id
        JOIN sensores s ON c.sensor_id = s.id
        WHERE s.dispositivo_id = %s
          AND v.fecha_hora_lectura >= %s
          AND v.fecha_hora_lectura <= %s
          AND (v.valor IS NOT NULL OR v.valor_texto IS NOT NULL)
        GROUP BY v.campo_id, DATE(v.fecha_hora_lectura), HOUR(v.fecha_hora_lectura)
        """
        cursor.execute(sql_horas, (dispositivo_id, fecha_inicio, fecha_fin))
        conexion.commit()
        
    except Exception as e:
        conexion.rollback()
        print(f"Fallo en agregacion masiva: {e}")
    finally:
        conexion.close()