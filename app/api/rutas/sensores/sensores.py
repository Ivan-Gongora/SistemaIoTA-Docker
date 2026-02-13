# app/api/rutas/sensores/sensores.py (Fragmento)

from fastapi import APIRouter, HTTPException, Depends, status,Query
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Any, Optional
import pymysql

#  Modelos y Utilidades
from app.servicios.auth_utils import get_current_user_id # Solo autenticación
from app.servicios.servicio_simulacion import get_db_connection
from app.api.modelos.sensores import SensorCrear,Sensor, SensorActualizar, SensorGeneral,RespuestaPaginadaSensores
from app.servicios.servicio_permisos import verificar_permiso_proyecto,obtener_proyecto_id_desde_dispositivo, obtener_proyecto_id_desde_sensor

from app.servicios.servicio_actividad import registrar_actividad_db
router_sensor = APIRouter()

# -----------------------------------------------------------
# 1. OBTENER SENSORES POR DISPOSITIVO (PAGINADO)
# -----------------------------------------------------------
@router_sensor.get("/sensores/dispositivo/{dispositivo_id}")
async def get_sensores_por_dispositivo(
    dispositivo_id: int,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: str = Query("", description="Búsqueda por nombre o tipo"),
    current_user_id: int = Depends(get_current_user_id)
):
   
    proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

    try:
        # Llamada a la nueva función paginada
        return await obtener_sensores_por_dispositivo_paginado_db(
            dispositivo_id, current_user_id,page, limit, search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sensores: {str(e)}")


# -----------------------------------------------------------
# 2. OBTENER TODOS LOS SENSORES (GLOBAL - PAGINADO)
# -----------------------------------------------------------
@router_sensor.get("/sensores/todos",response_model=RespuestaPaginadaSensores)
async def get_all_sensores_general(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: str = Query("", description="Búsqueda global"),
    current_user_id: int = Depends(get_current_user_id) 
):
    try:
        # Esta función ya filtra por usuario (Dueño o Invitado)
        return await obtener_sensores_globales_paginado_db(
            current_user_id, page, limit, search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sensores globales: {str(e)}")


# -----------------------------------------------------------
# 3. OBTENER SENSOR POR ID (INDIVIDUAL)
# -----------------------------------------------------------
@router_sensor.get("/sensores/{id}", response_model=Sensor)
async def get_sensor_por_id(
    id: int,
    current_user_id: int = Depends(get_current_user_id)
):
   
    proyecto_id = await obtener_proyecto_id_desde_sensor(id)
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

    try:
        sensor = await obtener_sensor_por_id_db(id)
        if not sensor:
            raise HTTPException(status_code=404, detail="Sensor no encontrado.")
        return sensor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener sensor: {str(e)}")
# -----------------------------------------------------------
# 1. CREAR SENSOR (POST)
# -----------------------------------------------------------
@router_sensor.post("/sensores/")
async def crear_sensor_endpoint(
    datos: SensorCrear,
    current_user_id: int = Depends(get_current_user_id)
):

    # 1. Averiguar el proyecto del dispositivo padre
    proyecto_id = await obtener_proyecto_id_desde_dispositivo(datos.dispositivo_id)
    
    # 2. Verificar permiso sobre ese proyecto
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada al servicio (ya incluye registro de actividad)
        resultados = await set_sensor(datos, current_user_id)
        return {"message": "Sensor registrado exitosamente.", "resultados": resultados}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado", "details": str(e)})
    
    
# 

# -----------------------------------------------------------
# 2. ACTUALIZAR SENSOR (PUT)
@router_sensor.put("/sensores/{id}")
async def actualizar_sensor_endpoint(
    id: int,
    datos: SensorActualizar,
    current_user_id: int = Depends(get_current_user_id)
):
   
    # 1. Averiguar el proyecto usando el ID del sensor
    proyecto_id = await obtener_proyecto_id_desde_sensor(id)
    
    # 2. Verificar permiso
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # 1. Ejecutar la actualización
        await actualizar_sensor_db(id, datos, current_user_id)
        
        # 2. Obtener y devolver el objeto actualizado
        sensor_actualizado = await obtener_sensor_por_id_db(id)
        
        if not sensor_actualizado:
             raise HTTPException(status_code=404, detail="Sensor actualizado no encontrado para devolver.")
             
        return {"status": "success", "resultados": [sensor_actualizado]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar sensor: {str(e)}")


# -----------------------------------------------------------
# 3. ELIMINAR SENSOR (DELETE)
# -----------------------------------------------------------
@router_sensor.delete("/sensores/{id}")
async def eliminar_sensor_endpoint(
    id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    # 1. Averiguar el proyecto usando el ID del sensor
    proyecto_id = await obtener_proyecto_id_desde_sensor(id)
    
    # 2. Verificar permiso
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')
    
    try:
        # Llamada al servicio (ya incluye registro de actividad)
        return await eliminar_sensor_db(id, current_user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar sensor: {str(e)}")
    
# ----------------------------------------------------------------------
# FUNCIONES DE SERVICIO DE BASE DE DATOS
# ----------------------------------------------------------------------

# POST: Insertar un nuevo sensor y sus campos asociados
async def set_sensor(datos: SensorCrear,usuario_id: int) -> Dict[str, Any]:
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
            # 🚨 CRÍTICO: IMPRIMIR EL PAYLOAD COMPLETO ANTES DE LA LÓGICA
        # Esto te mostrará la estructura real que el backend está viendo.
        print("-" * 50)
        print("PAYLOAD RECIBIDO DEL FRONTEND:")
        # Usamos .model_dump_json() para obtener el JSON completo como string
        print(datos.model_dump_json(indent=2)) 
        print("-" * 50)
            
        # 1. Validar existencia del dispositivo padre
        cursor.execute(
            "SELECT id, nombre, proyecto_id FROM dispositivos WHERE id = %s", 
            (datos.dispositivo_id,)
        )
        dispositivo_padre = cursor.fetchone()
        
        if not dispositivo_padre:
            raise HTTPException(status_code=404, detail=f"Dispositivo con ID '{datos.dispositivo_id}' no encontrado.")
        
        # Guardamos los datos para el log
        proyecto_id_padre = dispositivo_padre['proyecto_id']
        dispositivo_nombre = dispositivo_padre['nombre']
            
        fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 2. Insertar el sensor principal
        cursor.execute(
            """INSERT INTO sensores (nombre, tipo, habilitado, fecha_creacion, dispositivo_id) 
               VALUES (%s, %s, %s, %s, %s)""", 
            (datos.nombre, datos.tipo, datos.habilitado, fecha_creacion, datos.dispositivo_id)
        )
        
        # 3. 🚨 CRÍTICO: Obtener el ID del sensor recién insertado
        sensor_id = conn.insert_id()
        
        # 4. 🚨 ITERAR E INSERTAR CAMPOS DE SENSOR
        campos_agregados_count = 0
        if datos.campos:
            for campo in datos.campos:
                cursor.execute(
                    """INSERT INTO campos_sensores (nombre, tipo_valor, sensor_id, unidad_medida_id) 
                       VALUES (%s, %s, %s, %s)""",
                    (campo.nombre, campo.tipo_valor, sensor_id, campo.unidad_medida_id)
                )
                
                # -------------------------------------------------
                # 🚨 NUEVO: Registrar la actividad de CADA CAMPO CREADO
                # -------------------------------------------------
                await registrar_actividad_db(
                    usuario_id=usuario_id,
                    proyecto_id=proyecto_id_padre,
                    tipo_evento='CAMPO_CREADO',
                    titulo=campo.nombre, # Ej: "Temperatura"
                    fuente=f"Sensor: {datos.nombre}" # Ej: "Sensor: DHT22"
                )
                # -------------------------------------------------
                campos_agregados_count += 1
        
        conn.commit() # 👈 Transacción completada
        
        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='SENSOR_CREADO',
            titulo=datos.nombre, 
            fuente=f"Dispositivo: {dispositivo_nombre}" 
        )
        
        return {
            "status": "success", 
            "id_insertado": sensor_id, 
            "nombre": datos.nombre,
            "campos_agregados": len(datos.campos)
        }
    
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al insertar sensor/campos: {str(e)}")
    finally:
        if conn: conn.close()



# PUT: Actualizar un sensor
async def actualizar_sensor_db(
    id: int, 
    datos: SensorActualizar, 
    usuario_id: int 
) -> Dict[str, Any]:
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql_info = """
        SELECT 
            s.nombre AS nombre_sensor,
            d.nombre AS nombre_dispositivo,
            d.proyecto_id
        FROM sensores s
        JOIN dispositivos d ON s.dispositivo_id = d.id
        WHERE s.id = %s;
        """
        cursor.execute(sql_info, (id,))
        info_sensor = cursor.fetchone()

        if not info_sensor:
            raise HTTPException(status_code=404, detail="Sensor no encontrado.")

   
        proyecto_id_padre = info_sensor['proyecto_id']
        nombre_dispositivo_padre = info_sensor['nombre_dispositivo']
        nombre_actual_sensor = info_sensor['nombre_sensor']


        campos = []
        valores = []
        
        if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
        if datos.tipo is not None: campos.append("tipo = %s"); valores.append(datos.tipo)
        if datos.habilitado is not None: campos.append("habilitado = %s"); valores.append(datos.habilitado)
        
        if not campos:
             return {"status": "warning", "message": "No se proporcionaron datos para actualizar"}
             
        valores.append(id)
        sql_update = f"UPDATE sensores SET {', '.join(campos)} WHERE id = %s"
        
        cursor.execute(sql_update, valores)
        conn.commit()
        
  
        nombre_para_log = datos.nombre if datos.nombre is not None else nombre_actual_sensor

        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='SENSOR_MODIFICADO',
            titulo=nombre_para_log, # Nombre del sensor
            fuente=f"Dispositivo: {nombre_dispositivo_padre}" # Nombre del dispositivo padre
        )

        
        return {"status": "success", "rows_affected": cursor.rowcount}
        
    except pymysql.MySQLError as db_error:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error de base de datos al actualizar sensor: {db_error}")
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP (como el 404)
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error al actualizar sensor: {str(e)}")
    finally:
        if conn: conn.close()

async def eliminar_sensor_db(id: int, usuario_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
        # 🚨 3. Cambiar a DictCursor para leer los nombres
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 4. VALIDAR Y OBTENER DATOS PARA EL LOG (ANTES DE BORRAR)
        sql_info = """
        SELECT 
            s.nombre AS nombre_sensor,
            d.nombre AS nombre_dispositivo,
            d.proyecto_id
        FROM sensores s
        JOIN dispositivos d ON s.dispositivo_id = d.id
        WHERE s.id = %s;
        """
        cursor.execute(sql_info, (id,))
        info_sensor = cursor.fetchone()

        if not info_sensor:
            raise HTTPException(status_code=404, detail="Sensor no encontrado.")
        
        # Guardamos los datos para el log
        proyecto_id_padre = info_sensor['proyecto_id']
        nombre_dispositivo_padre = info_sensor['nombre_dispositivo']
        nombre_sensor_eliminado = info_sensor['nombre_sensor']

        # 5. Lógica de Eliminación en Cascada (Tu lógica original)
        
        # a) Eliminar VALORES (depende de campos_sensores)
        # (Nota: Si 'campos_sensores' tiene ON DELETE CASCADE, esto es redundante,
        # pero es más seguro hacerlo explícitamente).
        cursor.execute("DELETE FROM valores WHERE campo_id IN (SELECT id FROM campos_sensores WHERE sensor_id = %s)", (id,))
        
        # b) Eliminar CAMPOS DE SENSORES
        cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (id,))
        
        # 6. Eliminar SENSOR
        cursor.execute("DELETE FROM sensores WHERE id = %s", (id,))
        
        row_count = cursor.rowcount # Capturar filas afectadas por la última consulta
        
        conn.commit() # 👈 Transacción completada
        
        if row_count == 0:
            # Esto no debería pasar si la validación del paso 4 funcionó
            raise HTTPException(status_code=404, detail="Sensor no encontrado (fallo post-commit).")

        # -------------------------------------------------
        # 🚨 7. REGISTRAR LA ACTIVIDAD (Después del Commit)
        # -------------------------------------------------
        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='SENSOR_ELIMINADO',
            titulo=nombre_sensor_eliminado, # El nombre del sensor
            fuente=f"Dispositivo: {nombre_dispositivo_padre}" # El nombre del dispositivo padre
        )
        # -------------------------------------------------
            
        return {"status": "success", "message": f"Sensor '{nombre_sensor_eliminado}' eliminado exitosamente."}
        
    except pymysql.Error as e:
        if conn: conn.rollback()
        if e.args[0] == 1451: 
             raise HTTPException(status_code=400, detail="No se puede eliminar: El sensor aún tiene dependencias externas.")
        raise HTTPException(status_code=500, detail=f"DB Error al eliminar sensor: {str(e)}")
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if conn: conn.close()



# GET: Obtener un sensor por ID
async def obtener_sensor_por_id_db(sensor_id: int) -> Dict[str, Any] | None:
    conn = None
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 🚨 CONSULTA: Obtener todos los detalles del sensor
        cursor.execute("SELECT * FROM sensores WHERE id = %s", (sensor_id,))
        sensor = cursor.fetchone()
        
        if sensor:
            # 🚨 Conversión de tipos (CRÍTICO para Pydantic)
            if 'habilitado' in sensor:
                sensor['habilitado'] = int(sensor['habilitado']) == 1
            if 'fecha_creacion' in sensor and isinstance(sensor['fecha_creacion'], datetime):
                sensor['fecha_creacion'] = sensor['fecha_creacion'].strftime(DATE_FORMAT)
        return sensor
    except Exception as e:
        print(f"Error al obtener sensor por ID: {e}")
        return None
    finally:
        if conn: conn.close()


async def obtener_sensores_por_dispositivo_paginado_db(
    dispositivo_id: int, 
    usuario_id: int,
    page: int = 1, 
    limit: int = 10, 
    search: str = ""
) -> Dict[str, Any]:
    
    offset = (page - 1) * limit
    search_pattern = f"%{search}%"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 1. Obtener proyecto_id (necesario para verificar roles)
        cursor.execute("SELECT proyecto_id FROM dispositivos WHERE id = %s", (dispositivo_id,))
        proyecto_row = cursor.fetchone()
        if not proyecto_row:
             # Si no existe dispositivo, devolvemos vacío o error (tu decides)
             return {"data": [], "total": 0, "page": 1, "limit": limit, "total_pages": 0}
        proyecto_id = proyecto_row['proyecto_id']

        # 2. Consulta de Datos con ROL calculado
        sql_data = f"""
            SELECT 
                s.*,
                (SELECT COUNT(*) FROM campos_sensores cs WHERE cs.sensor_id = s.id) as total_campos,
                
                -- Lógica de Rol
                CASE 
                    WHEN p.usuario_id = %s THEN 'Propietario'
                    ELSE IFNULL(r.nombre_rol, 'Observador')
                END as mi_rol

            FROM sensores s
            JOIN dispositivos d ON s.dispositivo_id = d.id
            JOIN proyectos p ON d.proyecto_id = p.id
            LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
            LEFT JOIN roles r ON pu.rol_id = r.id
            
            WHERE s.dispositivo_id = %s
              AND (s.nombre LIKE %s OR s.tipo LIKE %s)
            
            ORDER BY s.id DESC 
            LIMIT %s OFFSET %s
        """
        
        # Params: [user_id, user_id, dispositivo_id, search, search, limit, offset]
        params = [usuario_id, usuario_id, dispositivo_id, search_pattern, search_pattern, limit, offset]
        
        cursor.execute(sql_data, params)
        sensores = cursor.fetchall()
        
        # 3. Obtener Total (para paginación)
        sql_count = "SELECT COUNT(*) as total FROM sensores WHERE dispositivo_id = %s AND (nombre LIKE %s OR tipo LIKE %s)"
        cursor.execute(sql_count, [dispositivo_id, search_pattern, search_pattern])
        total_records = cursor.fetchone()['total']
        
        # 4. Formateo
        for s in sensores:
            if 'habilitado' in s: s['habilitado'] = bool(s['habilitado'])
            if 'fecha_creacion' in s and isinstance(s['fecha_creacion'], datetime):
                s['fecha_creacion'] = s['fecha_creacion'].strftime(DATE_FORMAT)
                
        return {
            "data": sensores,
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
        }

    except Exception as e:
        print(f"Error DB sensores paginados: {e}")
        raise e
    finally:
        if conn: conn.close()

async def obtener_sensores_globales_paginado_db(
    current_user_id: int,
    page: int = 1,
    limit: int = 10,
    search: str = ""
) -> Dict[str, Any]:
    
    offset = (page - 1) * limit
    search_pattern = f"%{search}%"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 1. Definir el WHERE común (Filtros de seguridad y búsqueda)
        # El usuario debe ser el DUEÑO del proyecto (p.usuario_id) 
        # O estar invitado en el proyecto (pu.usuario_id)
        where_clause = """
            WHERE (p.usuario_id = %s OR pu.usuario_id = %s)
              AND (s.nombre LIKE %s OR s.tipo LIKE %s OR d.nombre LIKE %s)
        """
        # Params para el WHERE: [user, user, search, search, search]
        params_base = [current_user_id, current_user_id, search_pattern, search_pattern, search_pattern]

        # 2. Obtener Total (COUNT) para la paginación
        sql_count = f"""
            SELECT COUNT(DISTINCT s.id) as total
            FROM sensores s
            JOIN dispositivos d ON s.dispositivo_id = d.id
            JOIN proyectos p ON d.proyecto_id = p.id
            LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
            {where_clause}
        """
        # Necesitamos pasar current_user_id extra para el LEFT JOIN del count
        cursor.execute(sql_count, [current_user_id] + params_base)
        total_records = cursor.fetchone()['total']
        
        # 3. Obtener Datos Paginados (CON CAMPOS y ROL)
        sql_data = f"""
            SELECT DISTINCT 
                s.*, 
                d.nombre as nombre_dispositivo, 
                p.nombre as nombre_proyecto, 
                p.usuario_id as propietario_id,
                
          
                (SELECT COUNT(*) FROM campos_sensores cs WHERE cs.sensor_id = s.id) as total_campos,
                
           
                CASE 
                    WHEN p.usuario_id = %s THEN 'Propietario'
                    ELSE IFNULL(r.nombre_rol, 'Observador') -- Si es null, fallback a Observador
                END as mi_rol

            FROM sensores s
            JOIN dispositivos d ON s.dispositivo_id = d.id
            JOIN proyectos p ON d.proyecto_id = p.id
            
            -- Unimos para ver si es invitado
            LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
            LEFT JOIN roles r ON pu.rol_id = r.id
            
            {where_clause}
            
            ORDER BY s.id DESC 
            LIMIT %s OFFSET %s
        """
        
        # Params: 
        # 1. current_user_id (para el CASE del rol)
        # 2. current_user_id (para el LEFT JOIN de proyecto_usuarios)
        # 3. params_base (para el WHERE)
        # 4. limit, offset (para paginación)
        params_data = [current_user_id, current_user_id] + params_base + [limit, offset]
        
        cursor.execute(sql_data, params_data)
        sensores = cursor.fetchall()
        
        # 4. Formateo de datos (Fechas y Booleanos)
        for s in sensores:
            if 'habilitado' in s: 
                s['habilitado'] = bool(s['habilitado'])
            if 'fecha_creacion' in s and isinstance(s['fecha_creacion'], datetime):
                s['fecha_creacion'] = s['fecha_creacion'].strftime(DATE_FORMAT)
                
        return {
            "data": sensores,
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
        }

    except Exception as e:
        print(f"Error DB sensores globales: {e}")
        raise e
    finally:
        if conn: conn.close()



# # GET: Obtener Sensores por Dispositivo (Requiere JWT)
# async def obtener_sensores_por_dispositivo_db(dispositivo_id: int) -> List[Dict[str, Any]]:
#     conn = None
#     DATE_FORMAT = "%Y-%m-%d %H:%M:%S" 
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         sql = """
#         SELECT 
#             s.*, -- Selecciona todas las columnas base del sensor
#             (
#                 SELECT COUNT(cs.id) 
#                 FROM campos_sensores cs 
#                 WHERE cs.sensor_id = s.id
#             ) AS total_campos 
#         FROM sensores s 
#         WHERE s.dispositivo_id = %s;
#         """
        
#         cursor.execute(sql, (dispositivo_id,))
#         sensores = cursor.fetchall()
        
#         for sensor in sensores:
#             if 'habilitado' in sensor:
#                 sensor['habilitado'] = int(sensor['habilitado']) == 1 
#             if 'fecha_creacion' in sensor and isinstance(sensor['fecha_creacion'], datetime):
#                 sensor['fecha_creacion'] = sensor['fecha_creacion'].strftime(DATE_FORMAT)
            
#             if 'total_campos' in sensor:
#                 # Se asegura de que se pase como int, no como string o Decimal
#                 sensor['total_campos'] = int(sensor['total_campos'])

#         return sensores
        
#     except Exception as e:
#         print(f"Error al obtener sensores por dispositivo: {e}") 
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
        
#     finally:
#         if conn: conn.close()

# # GET: Obtener todos los sensores accesibles para el usuario (propietario o miembro)
# async def obtener_sensores_globales_db(current_user_id: int) -> List[Dict[str, Any]]:
#     """
#     Obtiene todos los sensores a los que un usuario tiene acceso (como propietario o miembro),
#     incluyendo los nombres del dispositivo y proyecto.
#     """
#     conn = None
#     DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # 🚨 CONSULTA CRÍTICA: JOIN de 3 niveles (Sensor -> Dispositivo -> Proyecto)
#         # Filtra por el usuario actual
#         sql = """
#         SELECT 
#             DISTINCT 
#             s.id, s.nombre, s.tipo, s.habilitado, s.fecha_creacion, s.dispositivo_id,
#             d.nombre AS nombre_dispositivo,
#             p.nombre AS nombre_proyecto,
#             p.id AS proyecto_id,
#             (SELECT COUNT(cs.id) FROM campos_sensores cs WHERE cs.sensor_id = s.id) AS total_campos
#         FROM 
#             sensores s
#         JOIN 
#             dispositivos d ON s.dispositivo_id = d.id
#         JOIN 
#             proyectos p ON d.proyecto_id = p.id
#         LEFT JOIN 
#             proyecto_usuarios pu ON p.id = pu.proyecto_id
#         WHERE 
#             p.usuario_id = %s OR pu.usuario_id = %s;
#         """
        
#         cursor.execute(sql, (current_user_id, current_user_id)) 
#         sensores = cursor.fetchall()
        
#         # Procesamiento de tipos (Booleano y Fecha)
#         for sensor in sensores:
#             if 'habilitado' in sensor:
#                 sensor['habilitado'] = int(sensor['habilitado']) == 1 
#             if 'fecha_creacion' in sensor and isinstance(sensor['fecha_creacion'], datetime):
#                 sensor['fecha_creacion'] = sensor['fecha_creacion'].strftime(DATE_FORMAT)
#             if 'total_campos' in sensor:
#                 sensor['total_campos'] = int(sensor['total_campos'])

#         return sensores

#     except Exception as e:
#         print(f"Error en DB al obtener sensores globales: {e}")
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
#     finally:
#         if conn:
#             conn.close()



# async def actualizar_sensor_db(id: int, datos: SensorActualizar) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # 1. Validación de existencia
#         cursor.execute("SELECT id FROM sensores WHERE id = %s", (id,))
#         if not cursor.fetchone():
#             raise HTTPException(status_code=404, detail="Sensor no encontrado.")

#         # 2. Construcción de UPDATE dinámico
#         campos = []
#         valores = []
        
#         if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
#         if datos.tipo is not None: campos.append("tipo = %s"); valores.append(datos.tipo)
#         if datos.habilitado is not None: campos.append("habilitado = %s"); valores.append(datos.habilitado)
        
#         if not campos:
#              return {"status": "warning", "message": "No se proporcionaron datos para actualizar"}
             
#         valores.append(id)
#         sql = f"UPDATE sensores SET {', '.join(campos)} WHERE id = %s"
#         cursor.execute(sql, valores)
#         conn.commit()
        
#         return {"status": "success", "rows_affected": cursor.rowcount}
#     except Exception as e:
#         if conn: conn.rollback()
#         raise HTTPException(status_code=500, detail=f"DB Error al actualizar sensor: {str(e)}")
#     finally:
#         if conn: conn.close()

# DELETE: Eliminar un sensor (Y sus campos/datos)

# async def eliminar_sensor_db(id: int) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # 1. Lógica de Eliminación en Cascada (Hojas primero)
        
#         # a) Eliminar VALORES (depende de campos_sensores)
#         cursor.execute("DELETE FROM valores WHERE campo_id IN (SELECT id FROM campos_sensores WHERE sensor_id = %s)", (id,))
        
#         # b) Eliminar CAMPOS DE SENSORES
#         cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (id,))
        
#         # 2. Eliminar SENSOR
#         cursor.execute("DELETE FROM sensores WHERE id = %s", (id,))
#         conn.commit()
        
#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Sensor no encontrado.")
            
#         return {"status": "success", "message": "Sensor eliminado exitosamente."}
#     except pymysql.Error as e:
#         if e.args[0] == 1451: # Si falla por otra clave foránea (no debería)
#              raise HTTPException(status_code=400, detail="No se puede eliminar: El sensor aún tiene dependencias externas.")
#         raise HTTPException(status_code=500, detail=f"DB Error al eliminar sensor: {str(e)}")
#     finally:
#         if conn: conn.close()


# GET: Obtener todos los sensores accesibles para el usuario (propietario o miembro)
# @router_sensor.get("/sensores/todos", response_model=List[SensorGeneral])
# async def get_all_sensores_general(
#     current_user_id: int = Depends(get_current_user_id) 
# ):
  
#     try:
#         sensores = await obtener_sensores_globales_db(current_user_id) 
        
#         if not sensores:
#             raise HTTPException(status_code=404, detail="No se encontraron sensores para este usuario.")
        
#         return sensores
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener sensores globales: {str(e)}")

# # GET: Obtener Sensor por ID (Requiere JWT)
# @router_sensor.get("/sensores/{id}", response_model=Sensor)
# async def get_sensor_por_id(
#     id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         sensor = await obtener_sensor_por_id_db(id)
#         if not sensor:
#             raise HTTPException(status_code=404, detail="Sensor no encontrado.")
#         # Nota: Aquí se debería verificar que el usuario tenga acceso al dispositivo/proyecto.
        
#         return sensor
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener sensor: {str(e)}")
    
# # GET: Obtener Sensores por Dispositivo (Requiere JWT)
# @router_sensor.get("/sensores/dispositivo/{dispositivo_id}", response_model=List[Sensor])
# async def get_sensores_por_dispositivo(
#     dispositivo_id: int,
#     current_user_id: int = Depends(get_current_user_id) # 🚨 AUTENTICACIÓN
# ):
#     # Nota: Aquí se debería verificar que el usuario tenga acceso al dispositivo/proyecto.
    
#     try:
#         sensores = await obtener_sensores_por_dispositivo_db(dispositivo_id)
#         if not sensores:
#             raise HTTPException(status_code=404, detail="No se encontraron sensores para este dispositivo.")
#         return sensores
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener sensores: {str(e)}")



# async def obtener_sensores_por_dispositivo_paginado_db(
#     dispositivo_id: int, 
#     page: int = 1, 
#     limit: int = 10, 
#     search: str = ""
# ) -> Dict[str, Any]:
    
#     offset = (page - 1) * limit
#     search_pattern = f"%{search}%"
#     DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # 1. Consulta Base
#         sql_base = """
#         FROM sensores 
#         WHERE dispositivo_id = %s 
#           AND (nombre LIKE %s OR tipo LIKE %s)
#         """
#         params = [dispositivo_id, search_pattern, search_pattern]
        
#         # 2. Total
#         cursor.execute(f"SELECT COUNT(*) as total {sql_base}", params)
#         total_records = cursor.fetchone()['total']
        
#         # 3. Paginación
#         sql_final = f"SELECT * {sql_base} ORDER BY id DESC LIMIT %s OFFSET %s"
#         params.extend([limit, offset])
        
#         cursor.execute(sql_final, params)
#         sensores = cursor.fetchall()
        
#         # Formateo
#         for s in sensores:
#             if 'habilitado' in s: s['habilitado'] = bool(s['habilitado'])
#             if 'fecha_creacion' in s and isinstance(s['fecha_creacion'], datetime):
#                 s['fecha_creacion'] = s['fecha_creacion'].strftime(DATE_FORMAT)
                
#         return {
#             "data": sensores,
#             "total": total_records,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
#         }
#     except Exception as e:
#         print(f"Error DB sensores paginados: {e}")
#         raise e
#     finally:
#         if conn: conn.close()