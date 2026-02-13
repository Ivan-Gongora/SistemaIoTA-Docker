# app/servicios/servicio_recepcion.py
# app/servicios/servicio_recepcion.py

from fastapi import HTTPException
from datetime import datetime
import pymysql
from typing import Dict, Any

# Importa los modelos y la conexión
from app.api.modelos.recepcion_datos import PayloadDispositivo
from app.servicios.servicio_simulacion import get_db_connection

async def procesar_datos_dispositivo_db(datos: PayloadDispositivo) -> Dict[str, Any]:
    """
    Procesa un payload de datos de dispositivo, busca los IDs de campo
    y guarda los valores en la base de datos de forma transaccional.
    """
    conn = None
    procesados_count = 0
    errores_count = 0
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor) 

        # 1. Validar IDs principales (convertir de string a int)
        try:
            proyecto_id = int(datos.proyecto)
            dispositivo_id = int(datos.dispositivo)
        except ValueError:
            raise HTTPException(status_code=400, detail="Proyecto ID o Dispositivo ID inválidos.")

        # 2. Preparar las fechas
        # Esta es la fecha/hora en que el servidor recibe el dato
        fecha_hora_registro = datetime.utcnow()  # ✅ CORREGIDO: fecha_hora_registro
        
        # Esta es la fecha/hora que el dispositivo reporta (fecha_hora_lectura)
        fecha_hora_dispositivo_str = f"{datos.fecha} {datos.hora}"
        fecha_hora_lectura = datetime.strptime(fecha_hora_dispositivo_str, "%Y-%m-%d %H:%M:%S")  # ✅ CORREGIDO: fecha_hora_lectura

        # 3. Iterar sobre Sensores y Campos
        for sensor in datos.sensores:
            sensor_nombre = sensor.nombre.strip()
            
            # 3a. Encontrar el Sensor ID (basado en el nombre y el dispositivo padre)
            cursor.execute(
                "SELECT id FROM sensores WHERE nombre = %s AND dispositivo_id = %s",
                (sensor_nombre, dispositivo_id)
            )
            sensor_row = cursor.fetchone()
            
            if not sensor_row:
                errores_count += len(sensor.datos)
                print(f"Error: Sensor '{sensor_nombre}' no encontrado en Dispositivo ID {dispositivo_id}.")
                continue

            sensor_id = sensor_row['id']

            # 3b. Iterar sobre los datos (ej: "Temperatura": 26.3)
            for campo_nombre, valor in sensor.datos.items():
                
                # 3c. Encontrar el Campo ID (basado en el nombre y el sensor padre)
                cursor.execute(
                    "SELECT id FROM campos_sensores WHERE nombre = %s AND sensor_id = %s",
                    (campo_nombre, sensor_id)
                )
                campo_row = cursor.fetchone()
                
                if not campo_row:
                    errores_count += 1
                    print(f"Error: Campo '{campo_nombre}' no encontrado en Sensor ID {sensor_id}.")
                    continue
                
                campo_id = campo_row['id']
                
                # 3d. Insertar el valor en la tabla 'valores' (✅ COLUMNAS CORREGIDAS)
                cursor.execute(
                    """
                    INSERT INTO valores (valor, fecha_hora_lectura, fecha_hora_registro, campo_id) 
                    VALUES (%s, %s, %s, %s)
                    """,
                    (str(valor), fecha_hora_lectura, fecha_hora_registro, campo_id)  # ✅ CORREGIDO
                )
                procesados_count += 1
        
        # 4. Confirmar la transacción
        conn.commit() 
        
        return {
            "status": "success", 
            "paquete_id": datos.id_paquete, 
            "registros_procesados": procesados_count, 
            "registros_con_error": errores_count
        }

    except Exception as e:
        if conn: 
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno procesando datos: {str(e)}")
    finally:
        if conn: 
            conn.close()




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