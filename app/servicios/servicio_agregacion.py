import pymysql
import time
from datetime import datetime, timedelta
from app.servicios.servicio_simulacion import get_db_connection

async def ejecutar_agregacion_horaria(procesar_historico=False, dias_historia=30):
    """
    Agregación horaria que puede procesar datos históricos o recientes
    
    Args:
        procesar_historico: Si es True, procesa datos históricos
        dias_historia: Número de días hacia atrás para procesar (solo si procesar_historico=True)
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
            current_time = datetime.now()
            print(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] 🔄 INICIANDO AGREGACIÓN HORARIA")
            
            # 🚨 CONFIGURAR FILTRO DE TIEMPO SEGÚN MODO
            if procesar_historico:
                # Modo histórico: procesar datos de los últimos N días
                fecha_limite = f"NOW() - INTERVAL {dias_historia} DAY"
                print(f"[{current_time.strftime('%H:%M:%S')}] 📅 MODO HISTÓRICO: Procesando últimos {dias_historia} días")
            else:
                # Modo normal: solo últimas 2 horas
                fecha_limite = "NOW() - INTERVAL 2 HOUR"
                print(f"[{current_time.strftime('%H:%M:%S')}] ⏰ MODO NORMAL: Procesando últimas 2 horas")
            
            # 🚨 DIAGNÓSTICO MEJORADO
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total_valores,
                    COUNT(DISTINCT campo_id) as campos_distintos,
                    COUNT(DISTINCT DATE(fecha_hora_lectura)) as dias_distintos,
                    MIN(fecha_hora_lectura) as fecha_min,
                    MAX(fecha_hora_lectura) as fecha_max
                FROM valores 
                WHERE fecha_hora_lectura >= {fecha_limite}
            """)
            stats_valores = cursor.fetchone()
            print(f"[{current_time.strftime('%H:%M:%S')}] 📊 VALORES: {stats_valores['total_valores']} registros")
            print(f"[{current_time.strftime('%H:%M:%S')}] 📊 RANGO: {stats_valores['fecha_min']} a {stats_valores['fecha_max']}")
            
            if stats_valores['total_valores'] == 0:
                print(f"[{current_time.strftime('%H:%M:%S')}] ⚠️  No hay datos para procesar en el rango seleccionado")
                return {
                    "status": "success", 
                    "message": "No hay datos nuevos para procesar",
                    "affected_rows": 0
                }
            
            # 🚨 CONSULTA PRINCIPAL MEJORADA
            sql_aggregate = f"""
            INSERT INTO valores_agregados 
                (campo_id, fecha, hora, valor_min, valor_max, valor_avg, valor_sum, total_registros)
            SELECT
                v.campo_id,
                DATE(v.fecha_hora_lectura) AS fecha,
                HOUR(v.fecha_hora_lectura) AS hora,
                
                MIN(v.valor) AS valor_min,
                MAX(v.valor) AS valor_max,
                
                CASE 
                    WHEN cs.nombre = 'Movimiento' THEN NULL
                    ELSE AVG(v.valor)
                END AS valor_avg,
                
                CASE
                    WHEN cs.nombre = 'Movimiento' THEN SUM(v.valor)
                    ELSE NULL
                END AS valor_sum,
                
                COUNT(*) AS total_registros
            FROM
                valores v
            JOIN 
                campos_sensores cs ON v.campo_id = cs.id
            WHERE
                v.fecha_hora_lectura >= {fecha_limite}
                AND NOT EXISTS (
                    SELECT 1 
                    FROM valores_agregados va 
                    WHERE va.campo_id = v.campo_id 
                    AND va.fecha = DATE(v.fecha_hora_lectura)
                    AND va.hora = HOUR(v.fecha_hora_lectura)
                )
            GROUP BY
                v.campo_id, cs.nombre, fecha, hora;
            """
            
            # Ejecutar agregación
            start_time = time.time()
            affected_rows = cursor.execute(sql_aggregate)
            conn.commit()
            end_time = time.time()
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ AGREGACIÓN COMPLETADA")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Registros INSERTADOS: {affected_rows}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏱️  Duración: {end_time - start_time:.2f} segundos")
            
            return {
                "status": "success",
                "affected_rows": affected_rows,
                "duration_seconds": end_time - start_time,
                "mode": "historical" if procesar_historico else "recent"
            }

    except Exception as e:
        error_msg = f"❌ Error en agregación: {str(e)}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {error_msg}")
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            conn.close()


# import pymysql
# import time
# from app.servicios.servicio_simulacion import get_db_connection

# async def ejecutar_agregacion_horaria():
#     """
#     Lee la tabla 'valores' de la última hora, calcula los agregados
#     y los inserta o actualiza en 'valores_agregados'.
#     """
#     conn = None
#     try:
#         conn = get_db_connection()
#         with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            
#             print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando agregación horaria...")

#             # 🚨 ESTA ES LA CONSULTA SQL OPTIMIZADA PARA PRODUCCIÓN 🚨
#             # Inserta nuevos resúmenes o actualiza los existentes si ya hay datos para esa hora.
#             sql_aggregate = """
#             INSERT INTO valores_agregados 
#                 (campo_id, fecha, hora, valor_min, valor_max, valor_avg, total_registros)
#             SELECT
#                 campo_id,
#                 DATE(fecha_hora_lectura) AS fecha,
#                 HOUR(fecha_hora_lectura) AS hora,
#                 MIN(valor) AS valor_min,
#                 MAX(valor) AS valor_max,
#                 AVG(valor) AS valor_avg,
#                 COUNT(*) AS total_registros
#             FROM
#                 valores
#             WHERE
#                 -- Procesa solo los datos de las últimas 2 horas (margen de seguridad)
#                 fecha_hora_lectura >= NOW() - INTERVAL 2 HOUR
#             GROUP BY
#                 campo_id, fecha, hora
#             ON DUPLICATE KEY UPDATE
#                 -- Si ya existe un resumen para esa hora, lo actualiza
#                 valor_min = LEAST(valores_agregados.valor_min, VALUES(valor_min)),
#                 valor_max = GREATEST(valores_agregados.valor_max, VALUES(valor_max)),
#                 valor_avg = ( (valores_agregados.valor_avg * valores_agregados.total_registros) + (VALUES(valor_avg) * VALUES(total_registros)) ) 
#                             / (valores_agregados.total_registros + VALUES(total_registros)),
#                 total_registros = valores_agregados.total_registros + VALUES(total_registros);
#             """
            
#             affected_rows = cursor.execute(sql_aggregate)
#             conn.commit()
#             print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Agregación completada. Filas afectadas/actualizadas: {affected_rows}")

#     except Exception as e:
#         print(f"Error en agregación programada: {e}")
#         if conn:
#             conn.rollback()
#     finally:
#         if conn:
#             conn.close()