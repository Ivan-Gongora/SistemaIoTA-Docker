from fastapi import APIRouter, Query
import pymysql
import traceback
from datetime import datetime
from typing import Dict, Any
from app.servicios.servicio_simulacion import get_db_connection
from app.servicios.analitica.motor_inteligencia import MotorInteligenciaIoT

router_prueba_analitica = APIRouter()
motor = MotorInteligenciaIoT()

@router_prueba_analitica.get("/prueba-motor-db/{dispositivo_id}")
async def ejecutar_prueba_db(dispositivo_id: int) -> Dict[str, Any]:
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # Consulta directa a la tabla optimizada
        sql = """
        SELECT
            va.fecha,
            va.hora,
            cs.nombre as campo,
            va.valor_avg,
            va.valor_sum,
            va.valor_texto
        FROM valores_agregados va
        JOIN campos_sensores cs ON va.campo_id = cs.id
        JOIN sensores s ON cs.sensor_id = s.id
        WHERE s.dispositivo_id = %s
        ORDER BY va.fecha ASC, va.hora ASC
        """
        
        cursor.execute(sql, (dispositivo_id,))
        filas = cursor.fetchall()
        conexion.close()

        if not filas:
            return {"estado": "fallo", "mensaje": "Tabla de agregados vacía para este dispositivo."}

        datos_agrupados = {}
        for fila in filas:
            # Formateo de fecha y hora
            fecha_str = fila['fecha'].strftime("%Y-%m-%d") if isinstance(fila['fecha'], datetime) else str(fila['fecha'])
            hora_str = f"{fila['hora']:02d}:00:00"
            clave = f"{fecha_str} {hora_str}"
            
            if clave not in datos_agrupados:
                datos_agrupados[clave] = {
                    "fecha": fecha_str,
                    "hora": hora_str
                }
            
            # Asignación inteligente del valor según la columna disponible
            nombre_campo = fila['campo']
            if nombre_campo in ('Energia', 'Movimiento'):
                valor_final = fila['valor_sum']
            elif fila['valor_avg'] is not None:
                valor_final = fila['valor_avg']
            else:
                valor_final = fila['valor_texto']
                
            datos_agrupados[clave][nombre_campo] = valor_final

        arreglo_datos = list(datos_agrupados.values())

        if len(arreglo_datos) < 5:
            return {
                "estado": "extraccion_exitosa",
                "mensaje": "El análisis exige un mínimo de 5 bloques horarios distintos.",
                "bloques_obtenidos": len(arreglo_datos)
            }

        # Procesamiento matemático
        df_limpio = motor.limpiar_serie_temporal(arreglo_datos)
        resultado_estadistico = motor.calcular_influencia_pearson(df_limpio)

        return {
            "estado": "analisis_completado",
            "bloques_horarios_analizados": len(arreglo_datos),
            "diagnostico_motor": resultado_estadistico
        }
    except Exception as e:
        return {
            "estado": "error_critico",
            "mensaje": str(e),
            "detalle_tecnico": traceback.format_exc()
        }

@router_prueba_analitica.get("/prueba-motor-puros/{dispositivo_id}")
async def ejecutar_prueba_puros_db(
    dispositivo_id: int,
    fecha_inicio: str = Query(..., description="Formato YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Formato YYYY-MM-DD")
) -> Dict[str, Any]:
    try:
        conexion = get_db_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        sql = """
        SELECT
            DATE(v.fecha_hora_lectura) as fecha,
            HOUR(v.fecha_hora_lectura) as hora,
            MINUTE(v.fecha_hora_lectura) as minuto,
            cs.nombre as campo,
            AVG(v.valor) as valor_avg,
            SUM(v.valor) as valor_sum,
            MAX(v.valor_texto) as valor_texto
        FROM valores v
        JOIN campos_sensores cs ON v.campo_id = cs.id
        JOIN sensores s ON cs.sensor_id = s.id
        WHERE s.dispositivo_id = %s
          AND v.fecha_hora_lectura >= %s 
          AND v.fecha_hora_lectura <= %s
        GROUP BY fecha, hora, minuto, cs.nombre
        ORDER BY fecha ASC, hora ASC, minuto ASC
        """
        
        cursor.execute(sql, (dispositivo_id, f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59"))
        filas = cursor.fetchall()
        conexion.close()

        if not filas:
            return {"estado": "fallo", "mensaje": "Sin datos puros en este rango de fechas."}

        datos_agrupados = {}
        for fila in filas:
            fecha_str = fila['fecha'].strftime("%Y-%m-%d") if isinstance(fila['fecha'], datetime) else str(fila['fecha'])
            hora_str = f"{fila['hora']:02d}:{fila['minuto']:02d}:00"
            clave = f"{fecha_str} {hora_str}"
            
            if clave not in datos_agrupados:
                datos_agrupados[clave] = {
                    "fecha": fecha_str,
                    "hora": hora_str
                }
            
            nombre_campo = fila['campo']
            if nombre_campo in ('Energia', 'Movimiento'):
                valor_final = fila['valor_sum']
            elif fila['valor_avg'] is not None:
                valor_final = fila['valor_avg']
            else:
                valor_final = fila['valor_texto']
                
            datos_agrupados[clave][nombre_campo] = valor_final

        arreglo_datos = list(datos_agrupados.values())

        if len(arreglo_datos) < 5:
            return {
                "estado": "extraccion_exitosa",
                "mensaje": "El análisis exige un mínimo de 5 bloques de un minuto distintos.",
                "bloques_obtenidos": len(arreglo_datos)
            }

        df_limpio = motor.limpiar_serie_temporal(arreglo_datos)
        resultado_estadistico = motor.calcular_influencia_pearson(df_limpio)

        return {
            "estado": "analisis_puros_completado",
            "rango_fechas": f"{fecha_inicio} a {fecha_fin}",
            "bloques_minuto_analizados": len(arreglo_datos),
            "diagnostico_motor": resultado_estadistico
        }
    except Exception as e:
        return {
            "estado": "error_critico",
            "mensaje": str(e),
            "detalle_tecnico": traceback.format_exc()
        }
# from fastapi import APIRouter
# import pymysql
# import traceback
# from datetime import datetime
# from typing import Dict, Any
# from app.servicios.servicio_simulacion import get_db_connection
# from app.servicios.analitica.motor_inteligencia import MotorInteligenciaIoT

# router_prueba_analitica = APIRouter()
# motor = MotorInteligenciaIoT()

# @router_prueba_analitica.get("/prueba-motor-db/{dispositivo_id}")
# async def ejecutar_prueba_db(dispositivo_id: int) -> Dict[str, Any]:
#     try:
#         conexion = get_db_connection()
#         cursor = conexion.cursor(pymysql.cursors.DictCursor)

#         # Consulta directa a la tabla optimizada
#         sql = """
#         SELECT
#             va.fecha,
#             va.hora,
#             cs.nombre as campo,
#             va.valor_avg,
#             va.valor_sum,
#             va.valor_texto
#         FROM valores_agregados va
#         JOIN campos_sensores cs ON va.campo_id = cs.id
#         JOIN sensores s ON cs.sensor_id = s.id
#         WHERE s.dispositivo_id = %s
#         ORDER BY va.fecha ASC, va.hora ASC
#         """
        
#         cursor.execute(sql, (dispositivo_id,))
#         filas = cursor.fetchall()
#         conexion.close()

#         if not filas:
#             return {"estado": "fallo", "mensaje": "Tabla de agregados vacía para este dispositivo."}

#         datos_agrupados = {}
#         for fila in filas:
#             # Formateo de fecha y hora
#             fecha_str = fila['fecha'].strftime("%Y-%m-%d") if isinstance(fila['fecha'], datetime) else str(fila['fecha'])
#             hora_str = f"{fila['hora']:02d}:00:00"
#             clave = f"{fecha_str} {hora_str}"
            
#             if clave not in datos_agrupados:
#                 datos_agrupados[clave] = {
#                     "fecha": fecha_str,
#                     "hora": hora_str
#                 }
            
#             # Asignación inteligente del valor según la columna disponible
#             nombre_campo = fila['campo']
#             if nombre_campo in ('Energia', 'Movimiento'):
#                 valor_final = fila['valor_sum']
#             elif fila['valor_avg'] is not None:
#                 valor_final = fila['valor_avg']
#             else:
#                 valor_final = fila['valor_texto']
                
#             datos_agrupados[clave][nombre_campo] = valor_final

#         arreglo_datos = list(datos_agrupados.values())

#         if len(arreglo_datos) < 5:
#             return {
#                 "estado": "extraccion_exitosa",
#                 "mensaje": "El análisis exige un mínimo de 5 bloques horarios distintos.",
#                 "bloques_obtenidos": len(arreglo_datos)
#             }

#         # Procesamiento matemático
#         df_limpio = motor.limpiar_serie_temporal(arreglo_datos)
#         resultado_estadistico = motor.calcular_influencia_pearson(df_limpio)

#         return {
#             "estado": "analisis_completado",
#             "bloques_horarios_analizados": len(arreglo_datos),
#             "diagnostico_motor": resultado_estadistico
#         }
#     except Exception as e:
#         return {
#             "estado": "error_critico",
#             "mensaje": str(e),
#             "detalle_tecnico": traceback.format_exc()
#         }
# from fastapi import APIRouter
# import pymysql
# import traceback
# from datetime import datetime
# from typing import Dict, Any
# from app.servicios.servicio_simulacion import get_db_connection
# from app.servicios.analitica.motor_inteligencia import MotorInteligenciaIoT

# router_prueba_analitica = APIRouter()
# motor = MotorInteligenciaIoT()

# @router_prueba_analitica.get("/prueba-motor-db/{dispositivo_id}")
# async def ejecutar_prueba_db(dispositivo_id: int) -> Dict[str, Any]:
#     try:
#         conexion = get_db_connection()
#         cursor = conexion.cursor(pymysql.cursors.DictCursor)

#         sql = """
#         SELECT
#             v.id,
#             v.fecha_hora_lectura,
#             cs.nombre as campo,
#             v.valor as valor_num,
#             v.valor_texto as valor_txt
#         FROM valores v
#         JOIN campos_sensores cs ON v.campo_id = cs.id
#         WHERE v.id BETWEEN 33 AND 43
#         ORDER BY v.fecha_hora_lectura ASC
#         """
        
#         cursor.execute(sql)
#         filas = cursor.fetchall()
#         conexion.close()

#         if not filas:
#             return {"estado": "fallo", "mensaje": "Base de datos vacía en los identificadores 33 al 43."}

#         datos_agrupados = {}
#         for fila in filas:
#             fecha_dt = fila['fecha_hora_lectura']
            
#             # Garantiza que la fecha sea un objeto datetime
#             if isinstance(fecha_dt, str):
#                 fecha_dt = datetime.strptime(fecha_dt, "%Y-%m-%d %H:%M:%S")
                
#             clave = str(fecha_dt)
#             if clave not in datos_agrupados:
#                 datos_agrupados[clave] = {
#                     "fecha": fecha_dt.strftime("%Y-%m-%d"),
#                     "hora": fecha_dt.strftime("%H:%M:%S")
#                 }
            
#             valor_final = fila['valor_num'] if fila['valor_num'] is not None else fila['valor_txt']
#             datos_agrupados[clave][fila['campo']] = valor_final

#         arreglo_datos = list(datos_agrupados.values())

#         if len(arreglo_datos) < 3:
#             return {
#                 "estado": "extraccion_exitosa",
#                 "mensaje": "Se requiere un mínimo de 3 registros temporales distintos para calcular Pearson.",
#                 "datos_extraidos": arreglo_datos
#             }

#         df_limpio = motor.limpiar_serie_temporal(arreglo_datos)
#         resultado_estadistico = motor.calcular_influencia_pearson(df_limpio)

#         return {
#             "estado": "analisis_completado",
#             "total_paquetes": len(arreglo_datos),
#             "datos_extraidos": arreglo_datos,
#             "diagnostico_motor": resultado_estadistico
#         }
#     except Exception as e:
#         return {
#             "estado": "error_critico",
#             "mensaje": str(e),
#             "detalle_tecnico": traceback.format_exc()
#         }