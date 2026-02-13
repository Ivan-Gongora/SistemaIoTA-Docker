from fastapi import Path, APIRouter, Query, HTTPException, Depends, status # 🚨 Añadido Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Dict, Any, Optional
import pymysql

#  Importaciones CRÍTICAS de Utilidades JWT
from app.servicios.auth_utils import get_current_user_id 
from app.configuracion import configuracion
from app.servicios.servicio_simulacion import get_db_connection, simular_datos_json
from app.api.modelos.dispositivos import DispositivoCrear, DispositivoActualizar,Dispositivo, Sensor, CampoSensor,DispositivoGeneral
from app.servicios import servicio_simulacion as servicio_simulacion 
from app.servicios.servicio_actividad import registrar_actividad_db
from app.servicios.servicio_permisos import verificar_permiso_proyecto, obtener_proyecto_id_desde_dispositivo,obtener_rol_usuario_en_proyecto

# Importamos TODAS las funciones del servicio (incluyendo Resumen)
from app.servicios.servicio_dispositivos import (
    obtener_dispositivos_globales_paginado_db, 
    obtener_dispositivo_por_id_db, 
    obtener_dispositivos_por_proyecto_paginado_db,
    get_resumen_dispositivo_db
)

router_dispositivo = APIRouter()

# -----------------------------------------------------------
#0.1  OBTENER TODOS LOS DISPOSITIVOS (GLOBAL - VISTA GENERAL)
# -----------------------------------------------------------
@router_dispositivo.get("/dispositivos/todos")
async def obtener_todos_los_dispositivos(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    search: str = Query("", description="Término de búsqueda"),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene todos los dispositivos accesibles.
    OPTIMIZACIÓN: Devuelve los roles agrupados por proyecto en 'roles_context'
    para evitar repetir el dato en cada dispositivo.
    """
    try:
        # 1. Obtener datos crudos de la DB (paginados)
        resultado = await obtener_dispositivos_globales_paginado_db(
            current_user_id, page, limit, search
        )
        
        dispositivos = resultado["data"]

        # 2. Optimización: Extraer IDs de proyectos únicos de esta página
        # Usamos un set para eliminar duplicados (ej. 5 dispositivos del mismo proyecto)
        # Esto reduce drásticamente las llamadas a la DB si hay muchos dispositivos del mismo proyecto.
        ids_proyectos_unicos = {disp["proyecto_id"] for disp in dispositivos}

        # 3. Consultar el rol UNA sola vez por proyecto
        mapa_roles = {}
        for pid in ids_proyectos_unicos:
            mapa_roles[pid] = await obtener_rol_usuario_en_proyecto(current_user_id, pid)

        # 4. Inyectar el diccionario de roles en la respuesta principal (Side-Loading)
        # El frontend buscará el rol así: const rol = data.roles_context[dispositivo.proyecto_id]
        resultado["roles_context"] = mapa_roles

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener lista global: {str(e)}")

# -----------------------------------------------------------
# 1. CREAR DISPOSITIVO (POST)
# -----------------------------------------------------------
@router_dispositivo.post("/dispositivos/")
async def crear_Dispositivo(
    datos: DispositivoCrear,
    current_user_id: int = Depends(get_current_user_id)
):
 
    # El usuario debe tener permiso 'CRUD_HARDWARE' en el proyecto donde quiere crear el dispositivo.
    await verificar_permiso_proyecto(current_user_id, datos.proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada a la función de servicio (que ya incluye el registro de actividad)
        resultados = await set_dispositivo(datos, current_user_id)
        
        resultado_final = resultados[0]
        if resultado_final.get("status") == "error":
             raise HTTPException(status_code=400, detail=resultado_final.get("message"))
             
        return {"message": "Se registro el dispositivo", "resultados": resultados}

    except HTTPException:
        raise
    except ValueError as e:
        return {"message": "Error en los datos enviados", "details": str(e)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado durante la inserción ", "details": str(e)})


# -----------------------------------------------------------
# 2. ELIMINAR DISPOSITIVO (DELETE)
# -----------------------------------------------------------
@router_dispositivo.delete("/dispositivos/")
async def eliminar_dispositivo_endpoint(
    id: Optional[int] = Query(None, description="ID del dispositivo a eliminar"),
    proyecto_id: int = Query(..., description="ID del proyecto obligatorio para validar permisos"),
    current_user_id: int = Depends(get_current_user_id) 
) -> Dict:
    

    # Validamos que el usuario tenga permiso sobre el proyecto entero antes de borrar nada.
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada a la función de servicio (que ya incluye el registro de actividad)
        return await eliminar_dispositivo_db(id, proyecto_id, current_user_id) 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar dispositivo(s): {str(e)}")


# -----------------------------------------------------------
# 3. ACTUALIZAR DISPOSITIVO (PUT)
# -----------------------------------------------------------
@router_dispositivo.put("/dispositivos/{dispositivo_id}") 
async def endpoint_actualizar_dispositivo(
    dispositivo_id: int, 
    datos: DispositivoActualizar,
    current_user_id: int = Depends(get_current_user_id)
):

    
    # 1. Obtenemos el ID del proyecto dueño del dispositivo
    proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
    
    # 2. Verificamos permiso sobre ese proyecto
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'CRUD_HARDWARE')

    try:
        # Llamada a la función de servicio (que ya incluye el registro de actividad)
        resultados = await actualizar_datos_dispositivo(dispositivo_id, datos, current_user_id) 
        return {"message": "Actualización de datos completada.", "resultados": resultados}

    except HTTPException:
        raise
    except ValueError as e:
        return {"message": "Error en los datos enviados", "details": str(e)}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado durante la actualización", "details": str(e)})
 
# # Actualizar información de dispositivos (CORREGIDO Y PROTEGIDO)
# @router_dispositivo.put("/dispositivos/{dispositivo_id}") # RUTA CORREGIDA: Usando Path parameter
# async def endpoint_actualizar_dispositivo(
#     dispositivo_id: int, 
#     datos: DispositivoActualizar,
#     current_user_id: int = Depends(get_current_user_id) # PROTEGIDO
# ):
#     # Nota: Aquí se debería verificar que el current_user_id sea propietario del proyecto.
#     try:
#         resultados = await actualizar_datos_dispositivo(dispositivo_id, datos,current_user_id) # Llama a la función de DB
#         return {"message": "Actualización de datos completada.", "resultados": resultados}

#     except ValueError as e:
#         return {"message": "Error en los datos enviados", "details": str(e)}
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"message": "Error inesperado durante la actualización", "details": str(e)},)
    
# ------------------------------------------------------------------
# 2. ENDPOINTS DE CONSULTA (PROTEGIDOS)
# ------------------------------------------------------------------

# app/api/rutas/dispositivos/dispositivos.py (ENDPOINT ACTUALIZADO)

# -----------------------------------------------------------
# 1. OBTENER DISPOSITIVOS POR PROYECTO (PAGINADO Y CON BÚSQUEDA)
# -----------------------------------------------------------
@router_dispositivo.get("/dispositivos/proyecto/{proyecto_id}")
async def get_dispositivos_por_proyecto(
    proyecto_id: int,
    page: int = Query(1, ge=1), limit: int = Query(10, ge=1), search: str = Query(""),
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

        # ✅ LLAMADA CORRECTA: 4 argumentos (Función DB Limpia)
        resultado = await obtener_dispositivos_por_proyecto_paginado_db(proyecto_id, page, limit, search)
        
        # Inyectamos el rol externamente
        rol = await obtener_rol_usuario_en_proyecto(current_user_id, proyecto_id)
        resultado["roles_context"] = {str(proyecto_id): rol}
        
        return resultado
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error proyecto: {str(e)}")
# -----------------------------------------------------------
# 2. OBTENER RESUMEN DE DISPOSITIVO
# -----------------------------------------------------------
# -----------------------------------------------------------
# 3. RESUMEN DE DISPOSITIVO (CON ROL INYECTADO)
# -----------------------------------------------------------
@router_dispositivo.get("/dispositivos/{dispositivo_id}/resumen")
async def get_dispositivo_resumen(
    dispositivo_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        # 1. Seguridad
        proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
        if not proyecto_id:
             raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")
        
        await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

        # 2. Obtener Datos del Resumen
        resumen = await get_resumen_dispositivo_db(dispositivo_id)
        if not resumen:
            raise HTTPException(status_code=404, detail="Resumen no encontrado.")

        # 3. Inyectar Rol (Nuevo requisito)
        rol = await obtener_rol_usuario_en_proyecto(current_user_id, proyecto_id)
        resumen["mi_rol"] = rol

        return resumen

    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# -----------------------------------------------------------
# # 3. OBTENER UN DISPOSITIVO POR ID

@router_dispositivo.get("/dispositivos/{dispositivo_id}")
async def get_dispositivo_por_id(
    dispositivo_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        # 1. Seguridad: Obtener ID Proyecto y Verificar acceso general
        proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
        if not proyecto_id:
             raise HTTPException(status_code=404, detail="Dispositivo no encontrado o sin proyecto.")
             
        # Bloquea acceso si no es dueño ni invitado
        await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

        # 2. Datos: Obtener información cruda del dispositivo
        dispositivo = await obtener_dispositivo_por_id_db(dispositivo_id)
        
        if not dispositivo:
            raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")

        # 3. Contexto: Obtener el Rol específico usando la función centralizada
        # Inyectamos el rol directamente en el objeto porque es una vista de detalle única
        rol_usuario = await obtener_rol_usuario_en_proyecto(current_user_id, proyecto_id)
        dispositivo['mi_rol'] = rol_usuario

        return dispositivo

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar dispositivo: {str(e)}")

        

# @router_dispositivo.get("/dispositivos/{dispositivo_id}", response_model=Dispositivo)
# async def get_dispositivo_por_id(
#     dispositivo_id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     # 1. Seguridad
#     proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
#     await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

#     conn = None
#     DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
#         cursor.execute("SELECT * FROM dispositivos WHERE id = %s", (dispositivo_id,))
#         dispositivo = cursor.fetchone()

#         if not dispositivo:
#             raise HTTPException(status_code=404, detail=f"Dispositivo no encontrado.")
        
#         # Conversión de fecha y bool
#         if 'fecha_creacion' in dispositivo and isinstance(dispositivo['fecha_creacion'], datetime):
#             dispositivo['fecha_creacion'] = dispositivo['fecha_creacion'].strftime(DATE_FORMAT)
#         if 'habilitado' in dispositivo:
#              dispositivo['habilitado'] = bool(dispositivo['habilitado'])

#         return dispositivo

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al consultar dispositivo: {str(e)}")
#     finally:
#         if conn: conn.close()


# ------------------------------------------------------------------
# 3. FUNCIONES DE BASE DE DATOS (SERVICIO DE DATOS BASE)
# ------------------------------------------------------------------

async def set_dispositivo(datos: DispositivoCrear, usuario_id: int) -> List[Dict[str, Any]]:
    procesado = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Validar existencia del proyecto Y OBTENER SU NOMBRE
        cursor.execute("SELECT id, nombre FROM proyectos WHERE id = %s", (datos.proyecto_id,))
        proyecto_row = cursor.fetchone()
        
        if not proyecto_row:
            return [{"status": "error", "message": f"El proyecto con id: '{datos.proyecto_id}' no existe"}]
        
        # Guardamos el nombre del proyecto para el log
        nombre_del_proyecto = proyecto_row['nombre']
        
        fecha_creacion = datos.fecha_creacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insertar el dispositivo
        cursor.execute("INSERT INTO dispositivos (nombre, descripcion, tipo, latitud, longitud, habilitado, fecha_creacion, proyecto_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (
            datos.nombre, datos.descripcion, datos.tipo, datos.latitud, datos.longitud, datos.habilitado, fecha_creacion, datos.proyecto_id
        ))
        
        id_insertado = conn.insert_id()
        conn.commit() # 

        
        await registrar_actividad_db(
            usuario_id=usuario_id,           
            proyecto_id=datos.proyecto_id,   
            tipo_evento='DISPOSITIVO_CREADO',
            titulo=datos.nombre,             
            fuente=f"Proyecto: {nombre_del_proyecto}" 
        )
        # -------------------------------------------------

        procesado.append({"nombre": datos.nombre, "status": "success", "id_insertado": id_insertado})

    except pymysql.MySQLError as e:
        if conn: conn.rollback()
        procesado.append({"status": "error", "message": f"DB Error: {str(e)}"})
    except Exception as e:
        if conn: conn.rollback()
        procesado.append({"status": "error", "message": f"Unexpected Error: {str(e)}"})
    finally:
        if conn: conn.close()
    return procesado

async def actualizar_datos_dispositivo(
    dispositivo_id: int, 
    datos: DispositivoActualizar, 
    usuario_id: int 
) -> List[Dict[str, Any]]:
    
    procesado = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 3. VALIDAR Y OBTENER DATOS 
        # Obtenemos los datos del dispositivo (y su proyecto padre) ANTES de actualizar
        sql_info = """
        SELECT 
            d.nombre AS nombre_dispositivo, 
            p.id AS proyecto_id,
            p.nombre AS nombre_proyecto
        FROM dispositivos d
        JOIN proyectos p ON d.proyecto_id = p.id
        WHERE d.id = %s
        """
        cursor.execute(sql_info, (dispositivo_id,))
        info_dispositivo = cursor.fetchone()
        
        if not info_dispositivo:
            return [{"status": "error", "message": f"El dispositivo con id: '{dispositivo_id}' no existe"}]
        
        # Guardamos los datos para el log
        proyecto_id_padre = info_dispositivo['proyecto_id']
        nombre_proyecto_padre = info_dispositivo['nombre_proyecto']
        nombre_actual_dispositivo = info_dispositivo['nombre_dispositivo']


        # 4. Construir la consulta de actualización (Tu lógica original)
        campos = []
        valores = []

        if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
        if datos.descripcion is not None: campos.append("descripcion = %s"); valores.append(datos.descripcion)
        if datos.tipo is not None: campos.append("tipo = %s"); valores.append(datos.tipo)
        if datos.latitud is not None: campos.append("latitud = %s"); valores.append(datos.latitud)
        if datos.longitud is not None: campos.append("longitud = %s"); valores.append(datos.longitud)
        if datos.habilitado is not None: campos.append("habilitado = %s"); valores.append(datos.habilitado)

        if not campos:
            procesado.append({"status": "warning", "message": "No se proporcionaron datos para actualizar"})
            return procesado # Salir temprano si no hay nada que actualizar

        valores.append(dispositivo_id)

        # 5. Ejecutar la actualización
        sql_update = f"UPDATE dispositivos SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(sql_update, valores)
        conn.commit() 


        # Determinar qué nombre usar para el log (el nuevo o el viejo)
        nombre_para_log = datos.nombre if datos.nombre is not None else nombre_actual_dispositivo

        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=proyecto_id_padre,
            tipo_evento='DISPOSITIVO_MODIFICADO',
            titulo=nombre_para_log, # El nombre del dispositivo (actualizado si cambió)
            fuente=f"Proyecto: {nombre_proyecto_padre}"
        )
        # -------------------------------------------------

        procesado.append({"status": "success", "message": f"Dispositivo con id '{dispositivo_id}' actualizado correctamente", "actualizado": datos.model_dump(exclude_none=True)})

    except Exception as e:
        if conn: conn.rollback()
        procesado.append({"status": "error", "message": f"Unexpected Error: {str(e)}"})
    finally:
        if conn: conn.close()
        
    return procesado

# Función de Eliminación de Dispositivo
async def eliminar_dispositivo_db(id: Optional[int], proyecto_id: int, usuario_id: int) -> Dict:
    conn = None
    try:
        conn = get_db_connection()
       
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 4. Validar proyecto y obtener nombre para el log
        cursor.execute("SELECT nombre FROM proyectos WHERE id = %s AND usuario_id = %s", (proyecto_id, usuario_id))
        proyecto_row = cursor.fetchone()
        if not proyecto_row: 
             raise HTTPException(status_code=404, detail=f"El proyecto con id: '{proyecto_id}' no existe o no pertenece al usuario.")
        
        nombre_proyecto = proyecto_row['nombre'] # Guardamos para el log

        
        # 5. Obtener los dispositivos a eliminar (CON NOMBRE)
        if id is not None:
            # Obtener un solo dispositivo si pertenece al proyecto
            cursor.execute("SELECT id, nombre FROM dispositivos WHERE id = %s AND proyecto_id = %s", (id, proyecto_id))
        else:
            # Obtener todos los dispositivos del proyecto
            cursor.execute("SELECT id, nombre FROM dispositivos WHERE proyecto_id = %s", (proyecto_id,))
            
        dispositivos_a_eliminar = cursor.fetchall()
        if not dispositivos_a_eliminar: 
            raise HTTPException(status_code=404, detail="No se encontraron dispositivos para eliminar")

        # 6. ELIMINACIÓN EN CASCADA (Tu lógica original)
        for dispositivo in dispositivos_a_eliminar:
            dispositivo_id = dispositivo["id"]
            
            # 1. Obtener y eliminar campos/valores (Hojas)
            cursor.execute("SELECT id FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
            sensores = cursor.fetchall()

            for sensor in sensores:
                sensor_id = sensor["id"]
               
                cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))
            
            # 2. Eliminar Sensores
            cursor.execute("DELETE FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
            
            # 3. Eliminar Dispositivo
            cursor.execute("DELETE FROM dispositivos WHERE id = %s", (dispositivo_id,))

        conn.commit() 
        for dispositivo in dispositivos_a_eliminar:
            await registrar_actividad_db(
                usuario_id=usuario_id,
                proyecto_id=proyecto_id,
                tipo_evento='DISPOSITIVO_ELIMINADO',
                titulo=dispositivo['nombre'], # El nombre del dispositivo eliminado
                fuente=f"Proyecto: {nombre_proyecto}"
            )
        # -------------------------------------------------

        return {"status": "success", "message": f"{len(dispositivos_a_eliminar)} dispositivo(s) eliminado(s) correctamente."}

    except HTTPException as http_exc:
        # Re-lanzar errores de validación (404, 403)
        if conn: conn.rollback()
        raise http_exc
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error al eliminar dispositivo(s): {str(e)}")
    finally:
        if conn: conn.close()
        
        
# =============================================================================
# FUNCIONES DE SERVICIO (DB)
# =============================================================================

# async def obtener_dispositivos_por_proyecto_paginado_db(
#     proyecto_id: int, 
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
        
#         # 1. Consulta Base con Filtros
#         # Nota: No incluimos 'SELECT *' aquí, solo el FROM y WHERE
#         sql_base = """
#         FROM dispositivos 
#         WHERE proyecto_id = %s 
#           AND (nombre LIKE %s OR tipo LIKE %s)
#         """
#         params_count = [proyecto_id, search_pattern, search_pattern]
        
#         # 2. Obtener Total (para el paginador)
#         cursor.execute(f"SELECT COUNT(*) as total {sql_base}", params_count)
#         total_records = cursor.fetchone()['total']
        
#         # 3. Obtener Datos Paginados
#         sql_final = f"SELECT * {sql_base} ORDER BY id DESC LIMIT %s OFFSET %s"
#         # Creamos una nueva lista de params para esta consulta
#         params_data = [proyecto_id, search_pattern, search_pattern, limit, offset]
        
#         cursor.execute(sql_final, params_data)
#         dispositivos = cursor.fetchall()
        
#         # 4. Procesar datos (Fechas y Booleanos)
#         for disp in dispositivos:
#             if 'habilitado' in disp:
#                 disp['habilitado'] = bool(disp['habilitado'])
            
#             if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
#                 disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
            
#             if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
#             if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
        
#         return {
#             "data": dispositivos,
#             "total": total_records,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
#         }

#     except Exception as e:
#         print(f"Error DB dispositivos paginados: {e}")
#         raise e
#     finally:
#         if conn: conn.close()


# async def get_resumen_dispositivo_db(dispositivo_id: int) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor) 
        
#         # 1. Obtener la Última Conexión
#         sql_ultima_conexion = """
#         SELECT MAX(v.fecha_hora_lectura) AS ultima_conexion_dt
#         FROM valores v
#         JOIN campos_sensores cs ON v.campo_id = cs.id
#         JOIN sensores s ON cs.sensor_id = s.id
#         WHERE s.dispositivo_id = %s;
#         """
#         cursor.execute(sql_ultima_conexion, (dispositivo_id,))
#         resultado_conexion = cursor.fetchone()
#         ultima_conexion = resultado_conexion['ultima_conexion_dt'] if resultado_conexion else None
        
#         # 2. Obtener Campos Activos
#         sql_campos_activos = """
#         SELECT COUNT(DISTINCT cs.id) AS count_campos_activos
#         FROM campos_sensores cs
#         JOIN sensores s ON cs.sensor_id = s.id
#         WHERE s.dispositivo_id = %s
#           AND cs.id IN (SELECT DISTINCT campo_id FROM valores);
#         """
#         cursor.execute(sql_campos_activos, (dispositivo_id,))
#         resultado_campos = cursor.fetchone()
#         campos_activos_count = resultado_campos['count_campos_activos'] if resultado_campos else 0

#         # 3. Obtener Totales
#         sql_totales = """
#         SELECT 
#             (SELECT COUNT(*) FROM dispositivos WHERE proyecto_id = 
#                 (SELECT proyecto_id FROM dispositivos WHERE id = %s)) AS total_dispositivos,
#             (SELECT COUNT(*) FROM sensores WHERE dispositivo_id = %s) AS total_sensores;
#         """
#         cursor.execute(sql_totales, (dispositivo_id, dispositivo_id))
#         totales_dict = cursor.fetchone()

#         return {
#             "ultima_conexion": ultima_conexion.isoformat() if ultima_conexion else None,
#             "total_dispositivos": totales_dict['total_dispositivos'] if totales_dict else 0,
#             "total_sensores": totales_dict['total_sensores'] if totales_dict else 0,
#             "campos_activos": campos_activos_count,
#             "estado_dispositivo": "Activo" 
#         }

#     except Exception as e:
#         print(f"Error al obtener resumen de dispositivo: {e}")
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
#     finally:
#         if conn: conn.close()




# async def obtener_dispositivos_por_proyecto_paginado_db(
#     proyecto_id: int,
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
        
#         # 1. Consulta Base (Sin JOINs complejos de seguridad, ya que filtramos por ID directo)
#         sql_base = """
#         FROM dispositivos d
#         JOIN proyectos p ON d.proyecto_id = p.id
#         WHERE d.proyecto_id = %s
#           AND (d.nombre LIKE %s OR d.tipo LIKE %s)
#         """
        
#         params_count = [proyecto_id, search_pattern, search_pattern]
        
#         # 2. Total
#         cursor.execute(f"SELECT COUNT(*) as total {sql_base}", params_count)
#         total_records = cursor.fetchone()['total']
        
#         # 3. Datos (Limpios, sin cálculo de rol)
#         sql_final = f"""
#         SELECT 
#             d.id, d.nombre, d.descripcion, d.tipo, d.latitud, d.longitud, d.habilitado, d.fecha_creacion, d.proyecto_id,
#             p.nombre AS nombre_proyecto,
#             p.usuario_id AS propietario_id
#         {sql_base}
#         ORDER BY d.id DESC
#         LIMIT %s OFFSET %s
#         """
        
#         params_data = params_count + [limit, offset]
        
#         cursor.execute(sql_final, params_data)
#         dispositivos = cursor.fetchall()
        
#         # 4. Procesamiento
#         for disp in dispositivos:
#             if 'habilitado' in disp: disp['habilitado'] = bool(disp['habilitado'])
#             if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
#                 disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
#             if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
#             if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
            
#         return {
#             "data": dispositivos,
#             "total": total_records,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
#         }

#     except Exception as e:
#         print(f"Error DB proyecto dispositivos: {e}")
#         raise e
#     finally:
#         if conn: conn.close()





# async def obtener_dispositivos_globales_paginado_db(
#     current_user_id: int,
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
        
#         # 1. Construir la consulta base (FROM y WHERE)
#         # Mantenemos los JOINs para asegurar que solo vea dispositivos donde tiene permiso
#         sql_base = """
#         FROM dispositivos d
#         JOIN proyectos p ON d.proyecto_id = p.id
#         LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
#         WHERE (p.usuario_id = %s OR pu.usuario_id = %s)
#           AND (d.nombre LIKE %s OR d.tipo LIKE %s OR p.nombre LIKE %s)
#         """
        
#         # Params para el COUNT y WHERE: 
#         # [user (join), user (where dueño), user (where invitado), search, search, search]
#         params_count = [current_user_id, current_user_id, current_user_id, search_pattern, search_pattern, search_pattern]
        
#         # 2. Obtener el Total (COUNT)
#         cursor.execute(f"SELECT COUNT(DISTINCT d.id) as total {sql_base}", params_count)
#         result_total = cursor.fetchone()
#         total_records = result_total['total'] if result_total else 0
        
#         # 3. Obtener los Datos Paginados (SIN CÁLCULO DE ROL SQL)
#         # Eliminamos el CASE WHEN. Solo traemos los IDs necesarios.
#         sql_final = f"""
#         SELECT DISTINCT 
#             d.id, d.nombre, d.descripcion, d.tipo, d.latitud, d.longitud, d.habilitado, d.fecha_creacion, d.proyecto_id, 
#             p.nombre AS nombre_proyecto, 
#             p.usuario_id AS propietario_id
#         {sql_base}
#         ORDER BY d.id DESC
#         LIMIT %s OFFSET %s
#         """
        
#         # Params para el SELECT final (Ya no necesitamos el user_id extra para el CASE)
#         params_data = params_count + [limit, offset]
        
#         cursor.execute(sql_final, params_data)
#         dispositivos = cursor.fetchall()
        
#         # 4. Procesar Datos Básicos (Fechas y Tipos)
#         for disp in dispositivos:
#             if 'habilitado' in disp:
#                 disp['habilitado'] = bool(disp['habilitado'])
            
#             if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
#                 disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
            
#             if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
#             if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
            
#             # Nota: 'mi_rol' se agregará en el endpoint
            
#         return {
#             "data": dispositivos,
#             "total": total_records,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
#         }

#     except Exception as e:
#         print(f"Error en DB al obtener dispositivos globales: {e}")
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
#     finally:
#         if conn: conn.close()




# async def obtener_dispositivo_por_id_db(dispositivo_id: int) -> Dict[str, Any]:
#     """
#     Recupera los datos crudos de un dispositivo por su ID.
#     No verifica permisos ni roles (eso lo hace el endpoint).
#     """
#     conn = None
#     DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # SQL Limpio: Solo datos del dispositivo y nombre del proyecto (útil para el header)
#         sql = """
#         SELECT d.*, p.nombre as nombre_proyecto, p.usuario_id as propietario_id
#         FROM dispositivos d
#         JOIN proyectos p ON d.proyecto_id = p.id
#         WHERE d.id = %s
#         """
        
#         cursor.execute(sql, (dispositivo_id,))
#         dispositivo = cursor.fetchone()

#         if not dispositivo:
#             return None
        
#         # Procesamiento de tipos
#         if 'fecha_creacion' in dispositivo and isinstance(dispositivo['fecha_creacion'], datetime):
#             dispositivo['fecha_creacion'] = dispositivo['fecha_creacion'].strftime(DATE_FORMAT)
        
#         if 'habilitado' in dispositivo:
#             dispositivo['habilitado'] = bool(dispositivo['habilitado'])

#         if dispositivo.get('latitud') is not None: dispositivo['latitud'] = float(dispositivo['latitud'])
#         if dispositivo.get('longitud') is not None: dispositivo['longitud'] = float(dispositivo['longitud'])

#         return dispositivo

#     except Exception as e:
#         print(f"Error DB obtener dispositivo: {e}")
#         raise e
#     finally:
#         if conn: conn.close()


# async def obtener_dispositivos_globales_paginado_db(
#     current_user_id: int,
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
        
#         # 1. Construir la consulta base (FROM y WHERE)
#         # Unimos con 'roles' para poder sacar el nombre del rol si es invitado
#         sql_base = """
#         FROM dispositivos d
#         JOIN proyectos p ON d.proyecto_id = p.id
#         LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
#         LEFT JOIN roles r ON pu.rol_id = r.id
#         WHERE (p.usuario_id = %s OR pu.usuario_id = %s)
#           AND (d.nombre LIKE %s OR d.tipo LIKE %s OR p.nombre LIKE %s)
#         """
        
#         # Params para el COUNT y WHERE: 
#         # [user (join), user (where dueño), user (where invitado), search, search, search]
#         params_count = [current_user_id, current_user_id, current_user_id, search_pattern, search_pattern, search_pattern]
        
#         # 2. Obtener el Total (COUNT)
#         cursor.execute(f"SELECT COUNT(DISTINCT d.id) as total {sql_base}", params_count)
#         total_records = cursor.fetchone()['total']
        
#         # 3. Obtener los Datos Paginados CON ROL
#         sql_final = f"""
#         SELECT DISTINCT 
#             d.id, d.nombre, d.descripcion, d.tipo, d.latitud, d.longitud, d.habilitado, d.fecha_creacion, d.proyecto_id, 
#             p.nombre AS nombre_proyecto, 
#             p.usuario_id AS propietario_id,
            
#             -- 🚨 CÁLCULO DEL ROL
#             CASE 
#                 WHEN p.usuario_id = %s THEN 'Propietario'  -- Si soy el dueño del proyecto
#                 ELSE IFNULL(r.nombre_rol, 'Observador')    -- Si soy invitado, tomo el rol
#             END as mi_rol

#         {sql_base}
#         ORDER BY d.id DESC
#         LIMIT %s OFFSET %s
#         """
        
#         # Params para el SELECT final:
#         # [user (case), user (join), user (where dueño), user (where invitado), search, search, search, limit, offset]
#         params_data = [current_user_id] + params_count + [limit, offset]
        
#         cursor.execute(sql_final, params_data)
#         dispositivos = cursor.fetchall()
        
#         # 4. Procesar Datos (Fechas y Booleanos)
#         for disp in dispositivos:
#             if 'habilitado' in disp:
#                 disp['habilitado'] = bool(disp['habilitado'])
            
#             if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
#                 disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
            
#             if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
#             if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
            
#         return {
#             "data": dispositivos,
#             "total": total_records,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
#         }

#     except Exception as e:
#         print(f"Error en DB al obtener dispositivos globales: {e}")
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
#     finally:
#         if conn: conn.close()
        
        
        
        
# async def obtener_dispositivos_globales_paginado_db(
#     current_user_id: int,
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
        
#         # 1. Construir la consulta base (FROM y WHERE)
#         # Filtrar por usuario (Dueño O Invitado) Y por búsqueda
#         sql_base = """
#         FROM dispositivos d
#         JOIN proyectos p ON d.proyecto_id = p.id
#         LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id
#         WHERE (p.usuario_id = %s OR pu.usuario_id = %s)
#           AND (d.nombre LIKE %s OR d.tipo LIKE %s OR p.nombre LIKE %s)
#         """
        
#         # 2. Obtener el Total (COUNT)
#         # (Para esto necesitamos COUNT(DISTINCT d.id) porque el JOIN puede duplicar si hay roles)
#         params_count = [current_user_id, current_user_id, search_pattern, search_pattern, search_pattern]
#         cursor.execute(f"SELECT COUNT(DISTINCT d.id) as total {sql_base}", params_count)
#         total_records = cursor.fetchone()['total']
        
#         # 3. Obtener los Datos Paginados
#         # Seleccionamos DISTINCT d.id para evitar duplicados
#         sql_final = f"""
#         SELECT DISTINCT d.id, d.nombre, d.descripcion, d.tipo, d.latitud, d.longitud, d.habilitado, d.fecha_creacion, d.proyecto_id, 
#                p.nombre AS nombre_proyecto, p.usuario_id AS propietario_id
#         {sql_base}
#         ORDER BY d.id DESC
#         LIMIT %s OFFSET %s
#         """
#         params_data = [current_user_id, current_user_id, search_pattern, search_pattern, search_pattern, limit, offset]
        
#         cursor.execute(sql_final, params_data)
#         dispositivos = cursor.fetchall()
        
#         # 4. Procesar Datos (Fechas y Booleanos)
#         for disp in dispositivos:
#             if 'habilitado' in disp:
#                 disp['habilitado'] = bool(disp['habilitado'])
            
#             if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
#                 disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
            
#             if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
#             if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
            
#         return {
#             "data": dispositivos,
#             "total": total_records,
#             "page": page,
#             "limit": limit,
#             "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
#         }

#     except Exception as e:
#         print(f"Error en DB al obtener dispositivos globales: {e}")
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
#     finally:
#         if conn: conn.close()




# async def get_resumen_dispositivo_db(dispositivo_id: int) -> Dict[str, Any]:
# #esa es la forma que debe devolver el resumen 
# #     {
# #     "ultima_conexion": "2025-10-23T17:15:18",
# #     "total_dispositivos": 2,
# #     "total_sensores": 4,
# #     "campos_activos": 7,
# #     "estado_dispositivo": "Activo"
# # }
#     conn = None
#     try:
#         conn = get_db_connection()
#         # 🚨 CORRECCIÓN: Usar DictCursor para todas las consultas
#         cursor = conn.cursor(pymysql.cursors.DictCursor) 
        
#         # 1. Obtener la Última Conexión
#         sql_ultima_conexion = """
#         SELECT MAX(v.fecha_hora_lectura) AS ultima_conexion_dt
#         FROM valores v
#         JOIN campos_sensores cs ON v.campo_id = cs.id
#         JOIN sensores s ON cs.sensor_id = s.id
#         WHERE s.dispositivo_id = %s;
#         """
#         cursor.execute(sql_ultima_conexion, (dispositivo_id,))
#         resultado_conexion = cursor.fetchone()
#         # 🚨 CORRECCIÓN: Manejar el caso de que no haya conexión (resultado None)
#         ultima_conexion = resultado_conexion['ultima_conexion_dt'] if resultado_conexion else None
        
#         # 2. Obtener Campos Activos
#         sql_campos_activos = """
#         SELECT COUNT(DISTINCT cs.id) AS count_campos_activos
#         FROM campos_sensores cs
#         JOIN sensores s ON cs.sensor_id = s.id
#         WHERE s.dispositivo_id = %s
#           AND cs.id IN (SELECT DISTINCT campo_id FROM valores);
#         """
#         cursor.execute(sql_campos_activos, (dispositivo_id,))
#         # 🚨 CORRECCIÓN: Manejar el caso de que no haya campos (resultado None)
#         resultado_campos = cursor.fetchone()
#         campos_activos_count = resultado_campos['count_campos_activos'] if resultado_campos else 0

#         # 3. Obtener Totales
#         sql_totales = """
#         SELECT 
#             (SELECT COUNT(*) FROM dispositivos WHERE proyecto_id = 
#                 (SELECT proyecto_id FROM dispositivos WHERE id = %s)) AS total_dispositivos,
#             (SELECT COUNT(*) FROM sensores WHERE dispositivo_id = %s) AS total_sensores;
#         """
#         cursor.execute(sql_totales, (dispositivo_id, dispositivo_id))
#         totales_dict = cursor.fetchone() # Ahora sí es un diccionario

#         # 4. Formatear el resultado
#         return {
#             "ultima_conexion": ultima_conexion.isoformat() if ultima_conexion else None,
#             "total_dispositivos": totales_dict['total_dispositivos'] if totales_dict else 0,
#             "total_sensores": totales_dict['total_sensores'] if totales_dict else 0,
#             "campos_activos": campos_activos_count,
#             "estado_dispositivo": "Activo" # Placeholder
#         }

#     except Exception as e:
#         print(f"Error al obtener resumen de dispositivo: {e}")
#         # Lanzar la excepción para que el endpoint la maneje como 500
#         raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
#     finally:
#         if conn: conn.close()
        
        
        
        
        
        
#         # @router_dispositivo.post("/dispositivos/")



# async def crear_Dispositivo(
#     datos: DispositivoCrear,
#     current_user_id: int = Depends(get_current_user_id) # 🚨 PROTEGIDO
# ):
#     try:
#         # 🚨 2. PASA EL 'current_user_id' A LA FUNCIÓN DE SERVICIO
#         resultados = await set_dispositivo(datos, current_user_id)
        
#         # Manejo de respuesta (basado en tu código de set_dispositivo)
#         resultado_final = resultados[0]
#         if resultado_final.get("status") == "error":
#              raise HTTPException(status_code=400, detail=resultado_final.get("message"))
             
#         return {"message": "Se registro el dispositivo", "resultados": resultados}

#     except ValueError as e:
#         return {"message": "Error en los datos enviados", "details": str(e)}
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"message": "Error inesperado durante la inserción ", "details": str(e)},)


    
# # Eliminar dispositivo (RUTA CORREGIDA Y PROTEGIDA) 
# @router_dispositivo.delete("/dispositivos/")
# async def eliminar_dispositivo_endpoint(
#     id: Optional[int] = Query(..., description="ID del dispositivo a eliminar"),
#     proyecto_id: int = Query(..., description="ID del proyecto"),
#     current_user_id: int = Depends(get_current_user_id) 
# ) -> Dict:
#     # Nota: Se debería verificar que el current_user_id sea propietario del proyecto_id
#     try:
#         # Llama a la función de servicio de DB
#         return await eliminar_dispositivo_db(id, proyecto_id, current_user_id) 
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al eliminar dispositivo(s): {str(e)}")


# ------------------------------------------------------------------
# 1. ENDPOINTS DE GESTIÓN (PROTEGIDOS)
# ------------------------------------------------------------------

# Crear Dispositivos (PROTEGIDO)
# @router_dispositivo.post("/dispositivos/")
# async def crear_Dispositivo(
#     datos: DispositivoCrear,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         # Nota: Aquí se debería verificar que el current_user_id sea propietario del proyecto.
#         resultados = await set_dispositivo(datos)
#         return {"message": "Se registro el dispositivo", "resultados": resultados}

#     except ValueError as e:
#         return {"message": "Error en los datos enviados", "details": str(e)}
#     except Exception as e:
#         return JSONResponse(status_code=500, content={"message": "Error inesperado durante la inserción ", "details": str(e)},)

# # Crear dispositivo
# async def set_dispositivo(datos: DispositivoCrear) -> List[Dict[str, Any]]:
#     # ... (cuerpo de la función set_dispositivo que ya tenías) ...
#     procesado = []
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # Validar existencia del proyecto
#         cursor.execute("SELECT id FROM proyectos WHERE id = %s", (datos.proyecto_id,))
#         proyecto_row = cursor.fetchone()
#         if not proyecto_row:
#             return [{"status": "error", "message": f"El proyecto con id: '{datos.proyecto_id}' no existe"}]
        
#         fecha_creacion = datos.fecha_creacion or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#         # Insertar el dispositivo
#         cursor.execute("INSERT INTO dispositivos (nombre, descripcion, tipo, latitud, longitud, habilitado, fecha_creacion, proyecto_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (
#             datos.nombre, datos.descripcion, datos.tipo, datos.latitud, datos.longitud, datos.habilitado, fecha_creacion, datos.proyecto_id
#         ))
#         conn.commit()
#         procesado.append({"nombre": datos.nombre, "status": "success", "id_insertado": conn.insert_id()})

#     except pymysql.MySQLError as e:
#         if conn: conn.rollback()
#         procesado.append({"status": "error", "message": f"DB Error: {str(e)}"})
#     except Exception as e:
#         if conn: conn.rollback()
#         procesado.append({"status": "error", "message": f"Unexpected Error: {str(e)}"})
#     finally:
#         if conn: conn.close()
#     return procesado

        
        
# async def eliminar_dispositivo_db(id: Optional[int], proyecto_id: int) -> Dict:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # 🚨 Lógica de eliminación en cascada de Dispositivos (corregida)
#         cursor.execute("SELECT * FROM proyectos WHERE id = %s", (proyecto_id,))
#         if not cursor.fetchone(): raise HTTPException(status_code=404, detail=f"El proyecto con id: '{proyecto_id}' no existe")

#         cursor_dict = conn.cursor(pymysql.cursors.DictCursor)
        
#         if id is not None:
#             # Eliminar un solo dispositivo si pertenece al proyecto
#             cursor_dict.execute("SELECT id FROM dispositivos WHERE id = %s AND proyecto_id = %s", (id, proyecto_id))
#         else:
#             # Eliminar todos los dispositivos del proyecto
#             cursor_dict.execute("SELECT id FROM dispositivos WHERE proyecto_id = %s", (proyecto_id,))
            
#         dispositivos = cursor_dict.fetchall()
#         if not dispositivos: raise HTTPException(status_code=404, detail="No se encontraron dispositivos para eliminar")

#         for dispositivo in dispositivos:
#             dispositivo_id = dispositivo["id"]
            
#             # 1. Obtener y eliminar campos/valores (Hojas)
#             cursor_dict.execute("SELECT id FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
#             sensores = cursor_dict.fetchall()

#             for sensor in sensores:
#                 sensor_id = sensor["id"]
#                 # Eliminar valores y campos (asumimos que la lógica es compleja y la simplificamos)
#                 cursor.execute("DELETE FROM valores WHERE campo_id IN (SELECT id FROM campos_sensores WHERE sensor_id = %s)", (sensor_id,))
#                 cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))
            
#             # 2. Eliminar Sensores
#             cursor.execute("DELETE FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
            
#             # 3. Eliminar Dispositivo
#             cursor.execute("DELETE FROM dispositivos WHERE id = %s", (dispositivo_id,))

#         conn.commit()
#         return {"status": "success", "message": f"{len(dispositivos)} dispositivo(s) eliminado(s) correctamente."}

#     except Exception as e:
#         if conn: conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Error al eliminar dispositivo(s): {str(e)}")
#     finally:
#         if conn: conn.close()
        
# @router_dispositivo.get("/dispositivos/todos", response_model=List[DispositivoGeneral])
# async def get_all_dispositivos_general(
#     current_user_id: int = Depends(get_current_user_id) 
# ):
#     try:
#         # Llamada a la función de DB
#         dispositivos = await obtener_dispositivos_globales_db(current_user_id) 
        
#         if not dispositivos:
#             raise HTTPException(status_code=404, detail="No se encontraron dispositivos en la base de datos.")
        
#         return dispositivos
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener dispositivos globales: {str(e)}")

# # Función para actualizar datos del dispositivo (CORREGIDO)
# async def actualizar_datos_dispositivo(dispositivo_id: int, datos: DispositivoActualizar,usuario_id:int) -> List[Dict[str, Any]]:
#     procesado = []
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # Validar existencia del dispositivo
#         cursor.execute("SELECT * FROM dispositivos WHERE id = %s", (dispositivo_id,))
#         if not cursor.fetchone():
#             return [{"status": "error", "message": f"El dispositivo con id: '{dispositivo_id}' no existe"}]

#         # Construir lista de campos a actualizar dinámicamente
#         campos = []
#         valores = []

#         if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
#         if datos.descripcion is not None: campos.append("descripcion = %s"); valores.append(datos.descripcion)
#         if datos.tipo is not None: campos.append("tipo = %s"); valores.append(datos.tipo)
#         if datos.latitud is not None: campos.append("latitud = %s"); valores.append(datos.latitud)
#         if datos.longitud is not None: campos.append("longitud = %s"); valores.append(datos.longitud)
#         if datos.habilitado is not None: campos.append("habilitado = %s"); valores.append(datos.habilitado)

#         valores.append(dispositivo_id)

#         if campos:
#             sql = f"UPDATE dispositivos SET {', '.join(campos)} WHERE id = %s"
#             cursor.execute(sql, valores)
#             conn.commit()

#             procesado.append({"status": "success", "message": f"Dispositivo con id '{dispositivo_id}' actualizado correctamente", "actualizado": datos.model_dump(exclude_none=True)})
#         else:
#             procesado.append({"status": "warning", "message": "No se proporcionaron datos para actualizar"})

#     except Exception as e:
#         if conn: conn.rollback()
#         procesado.append({"status": "error", "message": f"Unexpected Error: {str(e)}"})
#     finally:
#         if conn: conn.close()
#     return procesado
# @router_dispositivo.get("/dispositivos/{dispositivo_id}") # Puedes crear un response_model específico si quieres
# async def get_dispositivo_por_id(
#     dispositivo_id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     # 1. Seguridad (Verificar acceso al proyecto)
#     proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
#     await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

#     conn = None
#     DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # 🚨 SQL MEJORADO: Obtiene el dispositivo Y calcula el rol del usuario
#         sql = """
#         SELECT d.*, 
#             CASE 
#                 WHEN p.usuario_id = %s THEN 'Propietario'
#                 ELSE IFNULL(r.nombre_rol, 'Observador')
#             END as mi_rol
#         FROM dispositivos d
#         JOIN proyectos p ON d.proyecto_id = p.id
#         LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
#         LEFT JOIN roles r ON pu.rol_id = r.id
#         WHERE d.id = %s
#         """
        
#         cursor.execute(sql, (current_user_id, current_user_id, dispositivo_id))
#         dispositivo = cursor.fetchone()

#         if not dispositivo:
#             raise HTTPException(status_code=404, detail=f"Dispositivo no encontrado.")
        
#         # Conversión de fecha y bool
#         if 'fecha_creacion' in dispositivo and isinstance(dispositivo['fecha_creacion'], datetime):
#             dispositivo['fecha_creacion'] = dispositivo['fecha_creacion'].strftime(DATE_FORMAT)
#         if 'habilitado' in dispositivo:
#              dispositivo['habilitado'] = bool(dispositivo['habilitado'])

#         return dispositivo

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al consultar dispositivo: {str(e)}")
#     finally:
#         if conn: conn.close()

# @router_dispositivo.get("/dispositivos/todos")
# async def obtener_todos_los_dispositivos(
#     page: int = Query(1, ge=1, description="Número de página"),
#     limit: int = Query(10, ge=1, le=100, description="Registros por página"),
#     search: str = Query("", description="Término de búsqueda"),
#     current_user_id: int = Depends(get_current_user_id)
# ):
   
#     try:
      
#         resultado = await obtener_dispositivos_globales_paginado_db(
#             current_user_id, page, limit, search
#         )
#         return resultado

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener lista global: {str(e)}") 
# @router_dispositivo.get("/dispositivos/{dispositivo_id}/resumen")
# async def get_dispositivo_resumen(
#     dispositivo_id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     # 1. Seguridad (Necesitamos saber el proyecto)
#     proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
#     await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

#     try:
#         resumen = await get_resumen_dispositivo_db(dispositivo_id)
#         if not resumen:
#             raise HTTPException(status_code=404, detail="Resumen no encontrado.")
#         return resumen
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

