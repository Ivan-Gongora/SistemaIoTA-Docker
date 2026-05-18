import logging
import traceback
from datetime import datetime
import pymysql
from typing import List, Dict, Any
from app.api.modelos.recepcion_datos import PayloadDispositivo
from app.servicios.servicio_simulacion import get_db_connection

# Configuracion de rastreo de fallas para diagnostico
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recepcion_masiva")

cache_sensores = {}
cache_campos = {}

def es_numero(valor: Any) -> bool:
    try:
        float(valor)
        return True
    except (ValueError, TypeError):
        return False

async def procesar_lectura_individual_db(datos: PayloadDispositivo) -> Dict[str, Any]:
    """
    Procesa un paquete individual de datos.
    Protege el backend ante entradas mal formadas o nulas.
    """
    conexion = None
    try:
        if not datos:
            return {"status": "error", "message": "Peticion sin contenido"}
            
        conexion = get_db_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        
        id_dispositivo = int(datos.dispositivo)
        
        try:
            tiempo_lectura = datetime.strptime(f"{datos.fecha} {datos.hora}", "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            logger.error(f"Falla de formato en fecha: {datos.fecha} {datos.hora}")
            return {"status": "error", "message": f"Tiempo invalido. Detalle: {str(e)}"}
            
        tiempo_registro = datetime.utcnow()

        for elemento_sensor in datos.sensores:
            nombre = elemento_sensor.nombre.strip()
            clave = f"{nombre}_{id_dispositivo}"
            
            if clave in cache_sensores:
                id_sensor = cache_sensores[clave]
            else:
                cursor.execute(
                    "SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s",
                    (nombre, id_dispositivo)
                )
                fila = cursor.fetchone()
                if not fila:
                    logger.warning(f"Sensor no hallado: {nombre} en equipo {id_dispositivo}")
                    continue
                id_sensor = fila["id"]
                cache_sensores[clave] = id_sensor

            for nombre_campo, valor_campo in elemento_sensor.datos.items():
                clave_campo = f"{nombre_campo}_{id_sensor}"
                
                if clave_campo in cache_campos:
                    id_campo = cache_campos[clave_campo]
                else:
                    cursor.execute(
                        "SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s",
                        (nombre_campo, id_sensor)
                    )
                    fila_campo = cursor.fetchone()
                    if not fila_campo:
                        logger.warning(f"Campo no hallado: {nombre_campo} en sensor {id_sensor}")
                        continue
                    id_campo = fila_campo["id"]
                    cache_campos[clave_campo] = id_campo
                
                num = float(valor_campo) if es_numero(valor_campo) else None
                txt = str(valor_campo) if not es_numero(valor_campo) else None

                cursor.execute(
                    """
                    INSERT INTO valores (valor, valor_texto, fecha_hora_lectura, fecha_hora_registro, campo_id) 
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (num, txt, tiempo_lectura, tiempo_registro, id_campo)
                )
        
        conexion.commit()
        return {"status": "success", "message": "Procesado correctamente"}

    except pymysql.MySQLError as e:
        if conexion: conexion.rollback()
        logger.error(f"Falla tecnica en MySQL: {str(e)}")
        return {"status": "error", "message": "Falla de persistencia en base de datos"}
    except Exception as e:
        if conexion: conexion.rollback()
        logger.error(f"Error critico capturado: {traceback.format_exc()}")
        return {"status": "error", "message": f"Falla interna: {str(e)}"}
    finally:
        if conexion: conexion.close()



async def procesar_lote_datos_db(lote: List[Any]) -> Dict[str, Any]:
    """
    Gestiona la carga masiva por bloques usando executemany.
    Reduce el tiempo de inserción de horas a segundos.
    """
    conexion = None
    conteo_exito = 0
    conteo_falla = 0
    reporte_errores = []
    
    # Cachés locales para la ejecución de este lote
    cache_sensores_local = {}
    cache_campos_local = {}
    
    # Lista para acumular todas las inserciones del lote
    valores_a_insertar = []
    
    try:
        if not lote:
            return {"status": "error", "message": "Lote vacio"}
            
        conexion = get_db_connection()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)
        conexion.begin()

        # 1. Procesamiento en Memoria (Súper rápido)
        for indice, entrada in enumerate(lote):
            try:
                id_disp = int(entrada.dispositivo)
                
                try:
                    tiempo_l = datetime.strptime(f"{entrada.fecha} {entrada.hora}", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    conteo_falla += 1
                    reporte_errores.append(f"Indice {indice}: Fecha/Hora mal formada")
                    continue
                    
                tiempo_r = datetime.utcnow()

                for s in entrada.sensores:
                    n_s = s.nombre.strip()
                    c_s = f"{n_s}_{id_disp}"
                    
                    # Resolución de Sensor
                    if c_s in cache_sensores_local:
                        id_s = cache_sensores_local[c_s]
                    else:
                        cursor.execute("SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s", (n_s, id_disp))
                        f_s = cursor.fetchone()
                        if not f_s: continue
                        id_s = f_s["id"]
                        cache_sensores_local[c_s] = id_s

                    # Resolución de Campos
                    for n_c, v_c in s.datos.items():
                        c_c = f"{n_c}_{id_s}"
                        
                        if c_c in cache_campos_local:
                            id_c = cache_campos_local[c_c]
                        else:
                            cursor.execute("SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s", (n_c, id_s))
                            f_c = cursor.fetchone()
                            if not f_c: continue
                            id_c = f_c["id"]
                            cache_campos_local[c_c] = id_c
                        
                        # Preparar valor
                        v_n = float(v_c) if es_numero(v_c) else None
                        v_t = str(v_c) if not es_numero(v_c) else None

                        # ACUMULAR EN LA LISTA, NO INSERTAR AÚN
                        valores_a_insertar.append((v_n, v_t, tiempo_l, tiempo_r, id_c))
                        
                conteo_exito += 1
                
            except Exception as ex:
                conteo_falla += 1
                reporte_errores.append(f"Indice {indice}: {str(ex)}")
                continue

        # 2. Inserción Masiva en Base de Datos (El gran cambio)
        if valores_a_insertar:
            cursor.executemany(
                """
                INSERT INTO valores (valor, valor_texto, fecha_hora_lectura, fecha_hora_registro, campo_id) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                valores_a_insertar
            )

        conexion.commit()
        
        return {
            "status": "success", 
            "procesados": conteo_exito, 
            "fallidos": conteo_falla,
            "resumen_fallas": reporte_errores[:20]
        }

    except Exception as e:
        if conexion: conexion.rollback()
        logger.error(f"Falla masiva detectada: {traceback.format_exc()}")
        return {"status": "error", "message": f"Error general en el lote: {str(e)}"}
    finally:
        if conexion: conexion.close()




# async def procesar_lote_datos_db(lote: List[PayloadDispositivo]) -> Dict[str, Any]:
#     """
#     Gestiona la carga masiva por bloques.
#     Mapea razones de falla por cada registro sin interrumpir el flujo general.
#     """
#     conexion = None
#     conteo_exito = 0
#     conteo_falla = 0
#     reporte_errores = []
    
#     try:
#         if not lote:
#             return {"status": "error", "message": "Lote vacio"}
            
#         conexion = get_db_connection()
#         cursor = conexion.cursor(pymysql.cursors.DictCursor)
#         conexion.begin()

#         for indice, entrada in enumerate(lote):
#             try:
#                 id_disp = int(entrada.dispositivo)
                
#                 try:
#                     tiempo_l = datetime.strptime(f"{entrada.fecha} {entrada.hora}", "%Y-%m-%d %H:%M:%S")
#                 except ValueError:
#                     conteo_falla += 1
#                     reporte_errores.append(f"Indice {indice}: Fecha/Hora mal formada")
#                     continue
                    
#                 tiempo_r = datetime.utcnow()

#                 for s in entrada.sensores:
#                     n_s = s.nombre.strip()
#                     c_s = f"{n_s}_{id_disp}"
                    
#                     if c_s in cache_sensores:
#                         id_s = cache_sensores[c_s]
#                     else:
#                         cursor.execute(
#                             "SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s",
#                             (n_s, id_disp)
#                         )
#                         f_s = cursor.fetchone()
#                         if not f_s: continue
#                         id_s = f_s["id"]
#                         cache_sensores[c_s] = id_s

#                     for n_c, v_c in s.datos.items():
#                         c_c = f"{n_c}_{id_s}"
                        
#                         if c_c in cache_campos:
#                             id_c = cache_campos[c_c]
#                         else:
#                             cursor.execute(
#                                 "SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s",
#                                 (n_c, id_s)
#                             )
#                             f_c = cursor.fetchone()
#                             if not f_c: continue
#                             id_c = f_c["id"]
#                             cache_campos[c_c] = id_c
                        
#                         v_n = float(v_c) if es_numero(v_c) else None
#                         v_t = str(v_c) if not es_numero(v_c) else None

#                         cursor.execute(
#                             """
#                             INSERT INTO valores (valor, valor_texto, fecha_hora_lectura, fecha_hora_registro, campo_id) 
#                             VALUES (%s, %s, %s, %s, %s)
#                             """,
#                             (v_n, v_t, tiempo_l, tiempo_r, id_c)
#                         )
#                 conteo_exito += 1
                
#             except Exception as ex:
#                 conteo_falla += 1
#                 reporte_errores.append(f"Indice {indice}: {str(ex)}")
#                 continue

#         conexion.commit()
#         return {
#             "status": "success", 
#             "procesados": conteo_exito, 
#             "fallidos": conteo_falla,
#             "resumen_fallas": reporte_errores[:20]
#         }

#     except Exception as e:
#         if conexion: conexion.rollback()
#         logger.error(f"Falla masiva detectada: {traceback.format_exc()}")
#         return {"status": "error", "message": f"Error general en el lote: {str(e)}"}
#     finally:
#         if conexion: conexion.close()



# from fastapi import HTTPException
# from datetime import datetime
# import pymysql
# from typing import Dict, Any

# from app.api.modelos.recepcion_datos import PayloadDispositivo
# from app.servicios.servicio_simulacion import get_db_connection

# def es_numero(valor: Any) -> bool:
#     """Verifica si el dato puede tratarse como número."""
#     try:
#         float(valor)
#         return True
#     except (ValueError, TypeError):
#         return False

# async def procesar_datos_dispositivo_db(datos: PayloadDispositivo) -> Dict[str, Any]:
#     """
#     Procesa el payload y detecta si el valor es numérico o texto.
#     Guarda la información en las columnas correspondientes de la base de datos.
#     """
#     conn = None
#     procesados_count = 0
#     errores_count = 0
    
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor) 

#         # Validar IDs principales
#         try:
#             dispositivo_id = int(datos.dispositivo)
#         except ValueError:
#             raise HTTPException(status_code=400, detail="ID de dispositivo no válido.")

#         # Preparar marcas de tiempo
#         fecha_hora_registro = datetime.utcnow()
#         fecha_hora_dispositivo_str = f"{datos.fecha} {datos.hora}"
#         fecha_hora_lectura = datetime.strptime(fecha_hora_dispositivo_str, "%Y-%m-%d %H:%M:%S")

#         for sensor in datos.sensores:
#             sensor_nombre = sensor.nombre.strip()
            
#             # Localizar el Sensor
#             cursor.execute(
#                 "SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s",
#                 (sensor_nombre, dispositivo_id)
#             )
#             sensor_row = cursor.fetchone()
            
#             if not sensor_row:
#                 errores_count += len(sensor.datos)
#                 continue

#             sensor_id = sensor_row['id']

#             for campo_nombre, valor in sensor.datos.items():
#                 # Localizar el Campo
#                 cursor.execute(
#                     "SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s",
#                     (campo_nombre, sensor_id)
#                 )
#                 campo_row = cursor.fetchone()
                
#                 if not campo_row:
#                     errores_count += 1
#                     continue
                
#                 campo_id = campo_row['id']

#                 # Lógica de detección de tipo de dato
#                 valor_numerico = None
#                 valor_texto = None

#                 if es_numero(valor):
#                     valor_numerico = float(valor)
#                 else:
#                     valor_texto = str(valor)
                
#                 # Inserción con las nuevas columnas del Canvas
#                 cursor.execute(
#                     """
#                     INSERT INTO valores (valor, valor_texto, fecha_hora_lectura, fecha_hora_registro, campo_id) 
#                     VALUES (%s, %s, %s, %s, %s)
#                     """,
#                     (valor_numerico, valor_texto, fecha_hora_lectura, fecha_hora_registro, campo_id)
#                 )
#                 procesados_count += 1
        
#         conn.commit() 
        
#         return {
#             "status": "success", 
#             "paquete_id": datos.id_paquete, 
#             "registros_procesados": procesados_count, 
#             "registros_con_error": errores_count
#         }

#     except Exception as e:
#         if conn: 
#             conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Falla al procesar datos: {str(e)}")
#     finally:
#         if conn: 
#             conn.close()


# # app/servicios/servicio_recepcion.py version 1.0 10/2025


# from fastapi import HTTPException
# from datetime import datetime
# import pymysql
# from typing import Dict, Any

# # Importa los modelos y la conexión
# from app.api.modelos.recepcion_datos import PayloadDispositivo
# from app.servicios.servicio_simulacion import get_db_connection

# async def procesar_datos_dispositivo_db(datos: PayloadDispositivo) -> Dict[str, Any]:
#     """
#     Procesa un payload de datos de dispositivo, busca los IDs de campo
#     y guarda los valores en la base de datos de forma transaccional.
#     """
#     conn = None
#     procesados_count = 0
#     errores_count = 0
    
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor) 

#         # 1. Validar IDs principales (convertir de string a int)
#         try:
#             proyecto_id = int(datos.proyecto)
#             dispositivo_id = int(datos.dispositivo)
#         except ValueError:
#             raise HTTPException(status_code=400, detail="Proyecto ID o Dispositivo ID inválidos.")

#         # 2. Preparar las fechas
#         # Esta es la fecha/hora en que el servidor recibe el dato
#         fecha_hora_registro = datetime.utcnow()  # ✅ CORREGIDO: fecha_hora_registro
        
#         # Esta es la fecha/hora que el dispositivo reporta (fecha_hora_lectura)
#         fecha_hora_dispositivo_str = f"{datos.fecha} {datos.hora}"
#         fecha_hora_lectura = datetime.strptime(fecha_hora_dispositivo_str, "%Y-%m-%d %H:%M:%S")  # ✅ CORREGIDO: fecha_hora_lectura

#         # 3. Iterar sobre Sensores y Campos
#         for sensor in datos.sensores:
#             sensor_nombre = sensor.nombre.strip()
            
#             # 3a. Encontrar el Sensor ID (basado en el nombre y el dispositivo padre)
#             cursor.execute(
#                 "SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s",
#                 (sensor_nombre, dispositivo_id)
#             )
#             sensor_row = cursor.fetchone()
            
#             if not sensor_row:
#                 errores_count += len(sensor.datos)
#                 print(f"Error: Sensor '{sensor_nombre}' no encontrado en Dispositivo ID {dispositivo_id}.")
#                 continue

#             sensor_id = sensor_row['id']

#             # 3b. Iterar sobre los datos (ej: "Temperatura": 26.3)
#             for campo_nombre, valor in sensor.datos.items():
                
#                 # 3c. Encontrar el Campo ID (basado en el nombre y el sensor padre)
#                 cursor.execute(
#                     "SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s",
#                     (campo_nombre, sensor_id)
#                 )
#                 campo_row = cursor.fetchone()
                
#                 if not campo_row:
#                     errores_count += 1
#                     print(f"Error: Campo '{campo_nombre}' no encontrado en Sensor ID {sensor_id}.")
#                     continue
                
#                 campo_id = campo_row['id']
                
#                 # 3d. Insertar el valor en la tabla 'valores' (✅ COLUMNAS CORREGIDAS)
#                 cursor.execute(
#                     """
#                     INSERT INTO valores (valor, fecha_hora_lectura, fecha_hora_registro, campo_id) 
#                     VALUES (%s, %s, %s, %s)
#                     """,
#                     (str(valor), fecha_hora_lectura, fecha_hora_registro, campo_id)  # ✅ CORREGIDO
#                 )
#                 procesados_count += 1
        
#         # 4. Confirmar la transacción
#         conn.commit() 
        
#         return {
#             "status": "success", 
#             "paquete_id": datos.id_paquete, 
#             "registros_procesados": procesados_count, 
#             "registros_con_error": errores_count
#         }

#     except Exception as e:
#         if conn: 
#             conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Error interno procesando datos: {str(e)}")
#     finally:
#         if conn: 
#             conn.close()




# from fastapi import HTTPException
# from datetime import datetime
# import pymysql
# from typing import Dict, Any

# # Importa los modelos y la conexión
# from app.api.modelos.recepcion_datos import PayloadDispositivo
# from app.servicios.servicio_simulacion import get_db_connection

# async def procesar_datos_dispositivo_db(datos: PayloadDispositivo) -> Dict[str, Any]:
#     """
#     Procesa un payload de datos de dispositivo, busca los IDs de campo
#     y guarda los valores en la base de datos de forma transaccional.
#     """
#     conn = None
#     procesados_count = 0
#     errores_count = 0
    
#     try:
#         conn = get_db_connection()
#         # Usamos DictCursor para buscar IDs por nombre
#         cursor = conn.cursor(pymysql.cursors.DictCursor) 

#         # 1. Validar IDs principales (convertir de string a int)
#         try:
#             proyecto_id = int(datos.proyecto)
#             dispositivo_id = int(datos.dispositivo)
#         except ValueError:
#             raise HTTPException(status_code=400, detail="Proyecto ID o Dispositivo ID inválidos.")

#         # (Opcional pero recomendado: Validar que el dispositivo exista)
#         # cursor.execute("SELECT id FROM dispositivos WHERE id = %s AND proyecto_id = %s", (dispositivo_id, proyecto_id))
#         # if not cursor.fetchone():
#         #     raise HTTPException(status_code=404, detail="Dispositivo o Proyecto no encontrado.")

#         # 2. Preparar las fechas
#         # Esta es la fecha/hora en que el servidor recibe el dato
#         fecha_hora_servidor = datetime.utcnow() # (fecha_hora_lectura)
        
#         # Esta es la fecha/hora que el dispositivo reporta
#         fecha_hora_dispositivo_str = f"{datos.fecha} {datos.hora}"
#         fecha_hora_dispositivo = datetime.strptime(fecha_hora_dispositivo_str, "%Y-%m-%d %H:%M:%S") # (fecha_dispositivo)

#         # 3. Iterar sobre Sensores y Campos
#         for sensor in datos.sensores:
#             sensor_nombre = sensor.nombre.strip() # Limpiar espacios (como en "SCT-013-000 ")
            
#             # 3a. Encontrar el Sensor ID (basado en el nombre y el dispositivo padre)
#             cursor.execute(
#                 "SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s",
#                 (sensor_nombre, dispositivo_id)
#             )
#             sensor_row = cursor.fetchone()
            
#             if not sensor_row:
#                 errores_count += len(sensor.datos)
#                 print(f"Error: Sensor '{sensor_nombre}' no encontrado en Dispositivo ID {dispositivo_id}.")
#                 continue # Saltar este sensor si no existe en la DB

#             sensor_id = sensor_row['id']

#             # 3b. Iterar sobre los datos (ej: "Temperatura": 26.3)
#             for campo_nombre, valor in sensor.datos.items():
                
#                 # 3c. Encontrar el Campo ID (basado en el nombre y el sensor padre)
#                 cursor.execute(
#                     "SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s",
#                     (campo_nombre, sensor_id)
#                 )
#                 campo_row = cursor.fetchone()
                
#                 if not campo_row:
#                     errores_count += 1
#                     print(f"Error: Campo '{campo_nombre}' no encontrado en Sensor ID {sensor_id}.")
#                     continue # Saltar este campo si no existe
                
#                 campo_id = campo_row['id']
                
#                 # 3d. Insertar el valor en la tabla 'valores'
#                 cursor.execute(
#                     """
#                     INSERT INTO valores (valor, fecha_hora_lectura, fecha_dispositivo, campo_id) 
#                     VALUES (%s, %s, %s, %s)
#                     """,
#                     (str(valor), fecha_hora_servidor, fecha_hora_dispositivo, campo_id)
#                 )
#                 procesados_count += 1
        
#         # 4. Confirmar la transacción
#         # Para alta velocidad, solo hacemos commit una vez al final del paquete.
#         conn.commit() 
        
#         return {"status": "success", "paquete_id": datos.id_paquete, "registros_procesados": procesados_count, "registros_con_error": errores_count}

#     except Exception as e:
#         if conn: conn.rollback()
#         # Capturamos cualquier error (ej. fecha mal formada) y lo reportamos
#         raise HTTPException(status_code=500, detail=f"Error interno procesando datos: {str(e)}")
#     finally:
#         if conn: conn.close()