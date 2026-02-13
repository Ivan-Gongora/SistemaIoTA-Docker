# app/api/rutas/campos_sensores.py

from fastapi import APIRouter, Query, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import pymysql

from app.servicios.auth_utils import get_current_user_id
from app.servicios.servicio_simulacion import get_db_connection
from app.api.modelos.campos_sensores import CampoSensor, CampoSensorCrear, CampoSensorActualizar

from app.servicios.servicio_permisos import (
    verificar_permiso_proyecto,
    obtener_proyecto_id_desde_sensor, # Para GET y POST (tenemos sensor_id)
     obtener_rol_usuario_en_proyecto,
    obtener_proyecto_id_desde_campo   # Para PUT y DELETE (tenemos campo_id)
)

from app.servicios.servicio_actividad import registrar_actividad_db
router_campos = APIRouter()


async def obtener_campos_por_sensor_db(sensor_id: int) -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        SELECT
            cs.id,
            cs.nombre,
            cs.tipo_valor,
            cs.sensor_id,
            cs.unidad_medida_id,
            um.nombre AS nombre_unidad,
            um.simbolo AS simbolo_unidad,
            um.magnitud_tipo,
            uvc.ultimo_valor
        FROM campos_sensores cs
        LEFT JOIN unidades_medida um 
            ON cs.unidad_medida_id = um.id
        LEFT JOIN ultimo_valor_campo uvc 
            ON cs.id = uvc.campo_id
        WHERE cs.sensor_id = %s
        ORDER BY cs.id;
        """

        cursor.execute(sql, (sensor_id,))
        return cursor.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB Error al obtener campos: {str(e)}")
    finally:
        if conn:
            conn.close()

        
# POST: Crear un nuevo campo
async def set_campo_sensor_db(datos: CampoSensorCrear, usuario_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
      
        cursor = conn.cursor(pymysql.cursors.DictCursor) 
        

        sql_val_sensor = """
        SELECT 
            s.id AS sensor_id, 
            s.nombre AS sensor_nombre,
            d.proyecto_id,
            d.nombre AS dispositivo_nombre
        FROM sensores s
        JOIN dispositivos d ON s.dispositivo_id = d.id
        WHERE s.id = %s;
        """
        cursor.execute(sql_val_sensor, (datos.sensor_id,))
        sensor_padre = cursor.fetchone()
        
        if not sensor_padre:
            raise HTTPException(status_code=404, detail="Sensor padre no encontrado.")

        # Guardamos los datos para el log
        proyecto_id_padre = sensor_padre['proyecto_id']
        sensor_nombre_padre = sensor_padre['sensor_nombre']
            
        # 4. Validar Unidad de medida (si se proporciona)
        if datos.unidad_medida_id:
            cursor.execute("SELECT id FROM unidades_medida WHERE id = %s", (datos.unidad_medida_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Unidad de medida no encontrada.")

        # 5. Insertar el campo
        cursor.execute(
            "INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id) VALUES (%s, %s, %s, %s)",
            (datos.nombre, datos.tipo_valor, datos.sensor_id, datos.unidad_medida_id)
        )
        id_insertado = conn.insert_id()
        conn.commit()


        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='CAMPO_CREADO',
            titulo=datos.nombre, # Ej: "Temperatura"
            fuente=f"Sensor: {sensor_nombre_padre}" # Ej: "Sensor: DHT22"
        )
        # -------------------------------------------------
        
        return {"status": "success", "id_insertado": id_insertado, "nombre": datos.nombre}
    
    except pymysql.MySQLError as db_error:
        # Manejo de error específico de DB
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos al insertar campo: {db_error}")
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP (como el 404)
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado al insertar campo: {str(e)}")
    finally:
        if conn: conn.close()


# PUT: Actualizar un campo de sensor
async def actualizar_campo_sensor_db(
    id: int, 
    datos: CampoSensorActualizar, 
    usuario_id: int 
) -> Dict[str, Any]:
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        

        sql_info = """
        SELECT 
            cs.nombre AS nombre_campo,
            s.nombre AS nombre_sensor,
            d.proyecto_id
        FROM campos_sensores cs
        JOIN sensores s ON cs.sensor_id = s.id
        JOIN dispositivos d ON s.dispositivo_id = d.id
        WHERE cs.id = %s;
        """
        cursor.execute(sql_info, (id,))
        info_campo = cursor.fetchone()

        if not info_campo:
            raise HTTPException(status_code=404, detail="Campo de sensor no encontrado.")

        proyecto_id_padre = info_campo['proyecto_id']
        nombre_sensor_padre = info_campo['nombre_sensor']
        nombre_actual_campo = info_campo['nombre_campo']

        campos = []
        valores = []
        
        if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
        if datos.tipo_valor is not None: campos.append("tipo_valor = %s"); valores.append(datos.tipo_valor)
        
        # Validación extra para unidad_medida_id
        if datos.unidad_medida_id is not None:
            cursor.execute("SELECT id FROM unidades_medida WHERE id = %s", (datos.unidad_medida_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Unidad de medida no encontrada.")
            campos.append("unidad_medida_id = %s"); valores.append(datos.unidad_medida_id)
        
        if not campos:
             return {"status": "warning", "message": "No se proporcionaron datos para actualizar"}
             
        valores.append(id)
        sql_update = f"UPDATE campos_sensores SET {', '.join(campos)} WHERE id = %s"
        
        cursor.execute(sql_update, valores)
        row_count = cursor.rowcount # Capturar filas afectadas
        conn.commit() # 👈 Transacción completada
        
       
        nombre_para_log = datos.nombre if datos.nombre is not None else nombre_actual_campo

        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='CAMPO_MODIFICADO',
            titulo=nombre_para_log, # Nombre del campo
            fuente=f"Sensor: {nombre_sensor_padre}" # Nombre del sensor padre
        )
       
        return {"status": "success", "rows_affected": row_count}

    except pymysql.MySQLError as db_error:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos al actualizar campo: {db_error}")
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP (como el 404)
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error al actualizar campo: {str(e)}")
    finally:
        if conn: conn.close()



# DELETE: Eliminar un campo de sensor
async def eliminar_campo_sensor_db(id: int, usuario_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        

        sql_info = """
        SELECT 
            cs.nombre AS nombre_campo,
            s.nombre AS nombre_sensor,
            d.proyecto_id
        FROM campos_sensores cs
        JOIN sensores s ON cs.sensor_id = s.id
        JOIN dispositivos d ON s.dispositivo_id = d.id
        WHERE cs.id = %s;
        """
        cursor.execute(sql_info, (id,))
        info_campo = cursor.fetchone()

        if not info_campo:
            raise HTTPException(status_code=404, detail="Campo de sensor no encontrado.")

        # Guardamos los datos para el log
        proyecto_id_padre = info_campo['proyecto_id']
        nombre_sensor_padre = info_campo['nombre_sensor']
        nombre_campo_eliminado = info_campo['nombre_campo']

        cursor.execute("DELETE FROM valores WHERE campo_id = %s", (id,))
        
        cursor.execute("DELETE FROM campos_sensores WHERE id = %s", (id,))
        
        conn.commit() 
        
   
        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='CAMPO_ELIMINADO',
            titulo=nombre_campo_eliminado, # El nombre del campo
            fuente=f"Sensor: {nombre_sensor_padre}" # El nombre del sensor padre
        )
        # -------------------------------------------------
            
        return {"status": "success", "message": f"Campo '{nombre_campo_eliminado}' eliminado exitosamente."}

    except pymysql.Error as e:
        if conn: conn.rollback()
        if e.args[0] == 1451: # Error de FK
             raise HTTPException(status_code=400, detail="No se puede eliminar: El campo aún tiene dependencias externas.")
        raise HTTPException(status_code=500, detail=f"DB Error al eliminar campo: {str(e)}")
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn: conn.close()


# -----------------------------------------------------------
# GET: Obtener Campos por Sensor (Lectura)
# -----------------------------------------------------------
@router_campos.get("/sensores/{sensor_id}/campos")
async def get_campos_por_sensor(
    sensor_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    # 1. Obtener proyecto
    proyecto_id = await obtener_proyecto_id_desde_sensor(sensor_id)

    # 2. Validar permiso
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

    # 3. Obtener rol del usuario en ese proyecto
    rol_usuario = await obtener_rol_usuario_en_proyecto(current_user_id, proyecto_id)

    try:
        campos = await obtener_campos_por_sensor_db(sensor_id)

        return {
            "rol": rol_usuario,
            "campos": campos or []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener campos: {str(e)}")


# -----------------------------------------------------------
# POST: Crear Campo (Escritura)
# -----------------------------------------------------------
@router_campos.post("/campos_sensores/", response_model=Dict[str, Any])
async def crear_campo_sensor(
    datos: CampoSensorCrear,
    current_user_id: int = Depends(get_current_user_id)
):
    # 🚨 1. Averiguar el proyecto usando el sensor_id del payload
    proyecto_id = await obtener_proyecto_id_desde_sensor(datos.sensor_id)
    
    # 🚨 2. Verificar permiso de ESCRITURA
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada al servicio (ya incluye registro de actividad)
        resultado = await set_campo_sensor_db(datos, current_user_id)
        return {"message": "Campo de sensor creado exitosamente.", "resultados": resultado}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado", "details": str(e)})


# -----------------------------------------------------------
# PUT: Actualizar Campo (Escritura)
# -----------------------------------------------------------
@router_campos.put("/campos_sensores/{id}", response_model=Dict[str, Any])
async def actualizar_campo_sensor(
    id: int,
    datos: CampoSensorActualizar,
    current_user_id: int = Depends(get_current_user_id)
):
    # 🚨 1. Averiguar el proyecto usando el ID del campo
    proyecto_id = await obtener_proyecto_id_desde_campo(id)
    
    # 🚨 2. Verificar permiso de ESCRITURA
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada al servicio (ya incluye registro de actividad)
        return await actualizar_campo_sensor_db(id, datos, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado", "details": str(e)})


# -----------------------------------------------------------
# DELETE: Eliminar Campo (Escritura)
# -----------------------------------------------------------
@router_campos.delete("/campos_sensores/{id}", response_model=Dict[str, Any])
async def eliminar_campo_sensor(
    id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    # 🚨 1. Averiguar el proyecto usando el ID del campo
    proyecto_id = await obtener_proyecto_id_desde_campo(id)
    
    # 🚨 2. Verificar permiso de ESCRITURA
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada al servicio (Pasamos current_user_id para el log de actividad)
        return await eliminar_campo_sensor_db(id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado", "details": str(e)})
    
    
    
# ----------------------------------------------------------------------
# FUNCIONES DE SERVICIO DE BASE DE DATOS
# ----------------------------------------------------------------------

# GET: Obtener campos por sensor_id (con datos de unidad)
# async def obtener_campos_por_sensor_db(sensor_id: int) -> List[Dict[str, Any]]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         sql = """
#         SELECT 
#             cs.id, cs.nombre, cs.tipo_valor, cs.sensor_id, cs.unidad_medida_id, 
#             um.nombre AS nombre_unidad, 
#             um.simbolo AS simbolo_unidad,
#             um.magnitud_tipo,
#             (
#                 SELECT v.valor 
#                 FROM valores v 
#                 WHERE v.campo_id = cs.id 
#                 ORDER BY v.fecha_hora_lectura DESC 
#                 LIMIT 1
#             ) AS ultimo_valor
#         FROM campos_sensores cs
#         LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
#         WHERE cs.sensor_id = %s;
#         """
#         cursor.execute(sql, (sensor_id,))
#         return cursor.fetchall()
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"DB Error al obtener campos: {str(e)}")
#     finally:
#         if conn: conn.close()
        # app/api/rutas/campos_sensor/campos_sensor.py (Función de servicio)
#23/10/2025
#lo que hay arriba es la version que si funciona con la vista de : TarjetaCampoSensor.vue,habra que actualizarlo para que funcione con la nueva version
# app/api/rutas/campos_sensor/campos_sensor.py (Función de servicio)

# # POST: Crear un nuevo campo
# async def set_campo_sensor_db(datos: CampoSensorCrear) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # Validaciones (Sensor padre y Unidad de medida)
#         cursor.execute("SELECT id FROM sensores WHERE id = %s", (datos.sensor_id,))
#         if not cursor.fetchone():
#             raise HTTPException(status_code=404, detail="Sensor padre no encontrado.")
            
#         cursor.execute("SELECT id FROM unidades_medida WHERE id = %s", (datos.unidad_medida_id,))
#         if not cursor.fetchone():
#             raise HTTPException(status_code=404, detail="Unidad de medida no encontrada.")

#         # Insertar el campo
#         cursor.execute(
#             "INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id) VALUES (%s, %s, %s, %s)",
#             (datos.nombre, datos.tipo_valor, datos.sensor_id, datos.unidad_medida_id)
#         )
#         conn.commit()
#         return {"status": "success", "id_insertado": conn.insert_id(), "nombre": datos.nombre}
    
#     except Exception as e:
#         if conn: conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Error al insertar campo: {str(e)}")
#     finally:
#         if conn: conn.close()



# async def actualizar_campo_sensor_db(id: int, datos: CampoSensorActualizar) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         campos = []
#         valores = []
        
#         if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
#         if datos.tipo_valor is not None: campos.append("tipo_valor = %s"); valores.append(datos.tipo_valor)
#         if datos.unidad_medida_id is not None: campos.append("unidad_medida_id = %s"); valores.append(datos.unidad_medida_id)
        
#         if not campos:
#              return {"status": "warning", "message": "No se proporcionaron datos para actualizar"}
             
#         valores.append(id)
#         sql = f"UPDATE campos_sensores SET {', '.join(campos)} WHERE id = %s"
#         cursor.execute(sql, valores)
#         conn.commit()
        
#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Campo de sensor no encontrado.")
        
#         return {"status": "success", "rows_affected": cursor.rowcount}
#     except pymysql.Error as e:
#         raise HTTPException(status_code=500, detail=f"DB Error al actualizar campo: {str(e)}")
#     finally:
#         if conn: conn.close()



# async def eliminar_campo_sensor_db(id: int) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # 1. Eliminar valores asociados (Hoja)
#         cursor.execute("DELETE FROM valores WHERE campo_id = %s", (id,))
        
#         # 2. Eliminar el campo
#         cursor.execute("DELETE FROM campos_sensores WHERE id = %s", (id,))
#         conn.commit()
        
#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Campo de sensor no encontrado.")
            
#         return {"status": "success", "message": "Campo de sensor eliminado exitosamente."}
#     except pymysql.Error as e:
#         if e.args[0] == 1451: # Error de FK (si valores falla)
#              raise HTTPException(status_code=400, detail="No se puede eliminar: El campo aún tiene valores asociados.")
#         raise HTTPException(status_code=500, detail=f"DB Error al eliminar campo: {str(e)}")
#     finally:
#         if conn: conn.close()

# ----------------------------------------------------------------------
# ENDPOINTS (Protegidos por JWT)
# ----------------------------------------------------------------------