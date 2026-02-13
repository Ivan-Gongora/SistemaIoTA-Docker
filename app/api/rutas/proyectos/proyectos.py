from fastapi import APIRouter, Query, HTTPException, Depends, status

from fastapi.responses import JSONResponse, RedirectResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pymysql

# Importaciones CRÍTICAS de Utilidades JWT
from app.servicios.auth_utils import get_current_user_id, create_access_token, validate_invitation_token
from app.configuracion import configuracion
from app.servicios.servicio_simulacion import get_db_connection, simular_datos_json

# Importaciones de Modelos
from app.api.modelos.proyectos import ProyectoCrear, ProyectoActualizar, Proyecto,ProyectoConRol,RespuestaPaginadaProyectos 
from app.api.modelos.simulacion import DatosSimulacion
from app.servicios import servicio_simulacion as servicio_simulacion

from app.servicios.servicio_actividad import registrar_actividad_db
from app.servicios.servicio_permisos import verificar_permiso_proyecto,obtener_rol_usuario_en_proyecto



router_proyecto = APIRouter()




# ------------------------------------------------------------------
# 1. ENDPOINTS DE FASTAPI (PROTEGIDOS POR JWT)
# ------------------------------------------------------------------

# -----------------------------------------------------------
# 1. ADMIN: TODOS LOS PROYECTOS
# -----------------------------------------------------------
@router_proyecto.get("/proyectos")
async def get_proyectos(current_user_id: int = Depends(get_current_user_id)):
    # Aquí podrías agregar validación de rol de SuperAdmin si fuera necesario
    proyectos = await servicio_simulacion.obtener_proyectos()
    return proyectos

# -----------------------------------------------------------
# 2. LISTA DE PROYECTOS DEL USUARIO (Paginado + Contexto Roles)
# -----------------------------------------------------------
@router_proyecto.get("/proyectos/usuario/{usuario_id}")
async def obtener_proyectos_por_usuario(
    usuario_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    current_user_id: int = Depends(get_current_user_id)
):
    if usuario_id != current_user_id:
        raise HTTPException(status_code=403, detail="No autorizado.")
        
    try:
        # 1. Obtener datos crudos
        resultado = await servicio_simulacion.obtener_proyectos_paginados_db(
            usuario_id, page, limit, search
        )
        
        proyectos = resultado["data"]
        
        # 2. Construir Contexto de Roles (Side-Loading)
        # Iteramos sobre los proyectos para saber qué rol tengo en cada uno
        mapa_roles = {}
        for proj in proyectos:
            # Usamos la función centralizada
            rol = await obtener_rol_usuario_en_proyecto(current_user_id, proj["id"])
            mapa_roles[proj["id"]] = rol
            
        # 3. Inyectar contexto
        resultado["roles_context"] = mapa_roles
        
        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {str(e)}")

# -----------------------------------------------------------
# 3. DETALLE DE UN PROYECTO (Rol Inyectado en Objeto)
# -----------------------------------------------------------
@router_proyecto.get("/proyectos/{id}")
async def obtener_proyecto_por_id(
    id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        # 1. Verificar Permiso Básico (Firewall)
        # 'VER_DATOS_IOT' es un ejemplo, usa el permiso base para "ver" el proyecto
        await verificar_permiso_proyecto(current_user_id, id, 'VER_DATOS_IOT')
        
        # 2. Obtener Datos Crudos
        proyecto = await servicio_simulacion.obtener_proyecto_por_id_db(id)
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
            
        # 3. Obtener Rol Específico
        rol = await obtener_rol_usuario_en_proyecto(current_user_id, id)
        
        # 4. Inyectar Rol directamente (para el header del detalle)
        proyecto["mi_rol"] = rol
        
        return proyecto
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyecto: {str(e)}")


# Crear Proyectos (PROTEGIDO)
@router_proyecto.post("/crear_proyecto/")
async def crear_proyecto(
    datos: ProyectoCrear,
    current_user_id: int = Depends(get_current_user_id)
):
    if datos.usuario_id != current_user_id:
        raise HTTPException(status_code=403, detail="El ID de usuario en el payload no coincide con el usuario logueado.")
        
    try:
     
        resultados = await set_proyecto(datos) # Llama a la función de servicio definida abajo
        return {"message": "Se registro el proyecto", "resultados": resultados}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error inesperado durante la inserción ", "details": str(e)},)


# -----------------------------------------------------------
# ACTUALIZAR PROYECTO (PUT)
# -----------------------------------------------------------
@router_proyecto.put("/proyectos/{id}")
async def endpoint_actualizar_datos_proyecto(
    id: int, 
    datos: ProyectoActualizar,
    current_user_id: int = Depends(get_current_user_id)
):
    # Este verificará si eres dueño O si tienes el permiso 'CRUD_PROYECTO' como colaborador
    await verificar_permiso_proyecto(current_user_id, id, 'CRUD_PROYECTO') 
    
    try:
        # Pasamos el current_user_id para el registro de actividad
        resultados = await actualizar_datos_proyecto(id, datos, current_user_id) 
        return {"message": "Actualización de datos completada.", "resultados": resultados}
        
    except HTTPException:
        raise 
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"message": "Error inesperado durante la actualización", "details": str(e)}
        )


# -----------------------------------------------------------
# ELIMINAR PROYECTO (DELETE)
# -----------------------------------------------------------
@router_proyecto.delete("/proyectos/{id}")
async def eliminar_proyecto(
    id: int, # Recibimos ID directamente del Path
    current_user_id: int = Depends(get_current_user_id)
) -> Dict:
    
 
    
    # Solo permitirá pasar si tiene 'CRUD_PROYECTO_PROPIO' (que solo el dueño tiene)
    await verificar_permiso_proyecto(current_user_id, id, 'CRUD_PROYECTO_PROPIO')
    
    try:
        # Llamada a la función de servicio
        return await eliminar_proyecto_db(id, current_user_id) 
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar proyecto: {str(e)}")
# ------------------------------------------------------------------
# 2. ENDPOINT DE GESTIÓN DE ACCESO (NUEVA FUNCIONALIDAD JWT)
# ------------------------------------------------------------------
# Endpoint para generar el link de invitación (Protegido)
@router_proyecto.post("/proyectos/{proyecto_id}/invitar")
async def generar_link_invitacion(
    proyecto_id: int,
    # 1. AÑADIR EL PARÁMETRO rol_id (Por defecto 3=Observador)
    rol_id: int = Query(3, description="ID del rol a asignar (3=Observador, 4=Colaborador)"),
    current_user_id: int = Depends(get_current_user_id)
):
    # 1. Verificación de seguridad
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'GESTIONAR_ACCESO_PROYECTO')

    # 2. Validación simple de roles permitidos
    if rol_id not in [3, 4]:
        raise HTTPException(status_code=400, detail="Rol no válido para invitación (Use 3 o 4).")

    try:
        invitation_expires = timedelta(hours=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES / 60)
        
        # 🚨 3. GUARDAR EL ROL EN EL TOKEN
        invitation_token = create_access_token(
            data={
                "sub": str(current_user_id), 
                "project_id": proyecto_id, 
                "role_id": rol_id,  # <--- AQUÍ GUARDAMOS EL ROL SELECCIONADO
                "type": "INVITE"
            },
            expires_delta=invitation_expires
        )
        
        link_completo = f"{configuracion.FRONTEND_URL}/join?token={invitation_token}"

        return {
            "status": "success", 
            "link": link_completo, 
            "rol_asignado": rol_id, # Confirmación visual
            "expira_en_horas": invitation_expires.total_seconds() / 3600
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar link: {str(e)}")
# app/api/rutas/proyectos/proyectos.py (Añadir a la sección de Endpoints de Gestión)

@router_proyecto.delete("/proyectos/{proyecto_id}/miembros/{usuario_id_a_remover}")
async def remove_project_member(
    proyecto_id: int,
    usuario_id_a_remover: int,
    current_user_id: int = Depends(get_current_user_id)
):
    #VERIFICACIÓN DE SEGURIDAD (Usando el servicio centralizado)
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'GESTIONAR_ACCESO_PROYECTO')
    
    if usuario_id_a_remover == current_user_id:
         raise HTTPException(status_code=400, detail="No puedes removerte a ti mismo.")

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Obtener nombres para el log
        cursor.execute("SELECT nombre FROM proyectos WHERE id = %s", (proyecto_id,))
        nombre_proyecto = cursor.fetchone()['nombre']
        
        cursor.execute("SELECT nombre_usuario FROM usuarios WHERE id = %s", (usuario_id_a_remover,))
        usuario_removido = cursor.fetchone()
        nombre_usuario_removido = usuario_removido['nombre_usuario'] if usuario_removido else f"ID {usuario_id_a_remover}"

        # Eliminar
        cursor.execute(
            "DELETE FROM proyecto_usuarios WHERE proyecto_id = %s AND usuario_id = %s",
            (proyecto_id, usuario_id_a_remover)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="El usuario no era miembro de este proyecto.")
            
        conn.commit()

        #  REGISTRAR ACTIVIDAD
        await registrar_actividad_db(
            usuario_id=current_user_id,
            proyecto_id=proyecto_id,
            tipo_evento='USUARIO_REMOVIDO',
            titulo=f"Usuario removido: {nombre_usuario_removido}",
            fuente=f"Proyecto: {nombre_proyecto}"
        )

        return {"status": "success", "message": f"Usuario removido exitosamente."}

    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if conn: conn.close()

# Endpoint para procesar la unión al proyecto (CORREGIDO)
@router_proyecto.post("/join-project/{invitation_token}")
async def process_join_project(
    invitation_token: str,
    current_user_id: int = Depends(get_current_user_id), 
):
    conn = None
    try:
        invitation_data = validate_invitation_token(invitation_token)
        
        project_id = invitation_data.get("project_id")
        inviter_id = int(invitation_data.get("sub")) 
        
        # LEER EL ROL DEL TOKEN (Si no existe, usa 3 por defecto)
        rol_a_asignar = invitation_data.get("role_id", 3) 
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Obtener nombre del proyecto para el log
        cursor.execute("SELECT nombre FROM proyectos WHERE id = %s", (project_id,))
        proyecto_row = cursor.fetchone()
        nombre_proyecto = proyecto_row['nombre'] if proyecto_row else "Proyecto Desconocido"

        #  USAR EL ROL DINÁMICO EN EL INSERT
        cursor.execute(
            """
            INSERT INTO proyecto_usuarios (proyecto_id, usuario_id, rol_id) 
            VALUES (%s, %s, %s)
            """, 
            (project_id, current_user_id, rol_a_asignar) # <--- USAMOS LA VARIABLE, NO EL NÚMERO FIJO
        )
        conn.commit()
        
        # Obtener nombre del rol para el log (Opcional, para que se vea bonito)
        nombre_rol_asignado = "Observador" if rol_a_asignar == 3 else "Colaborador"

        # Registrar Actividad
        await registrar_actividad_db(
            usuario_id=inviter_id,
            proyecto_id=project_id,
            tipo_evento='USUARIO_INVITADO',
            titulo=f"Nuevo miembro: {nombre_rol_asignado}",
            fuente=f"Proyecto: {nombre_proyecto}"
        )
        
        return {"status": "success", "message": f"Te has unido al proyecto como {nombre_rol_asignado}.", "project_id": project_id}

    except pymysql.Error as e:
        if e.args[0] == 1062: 
            return {"status": "warning", "message": "Ya eres miembro de este proyecto."}
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        if conn: conn.close()

#  Endpoint para obtener miembros de un proyecto específico (AÑADIDO)
@router_proyecto.get("/proyectos/{proyecto_id}/miembros")
async def get_project_members(
    proyecto_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    #  VERIFICACIÓN DE SEGURIDAD (Cualquiera con acceso de lectura puede ver miembros)
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        cursor.execute(
            """
            SELECT 
                u.id AS usuario_id,
                u.nombre_usuario, 
                r.nombre_rol
            FROM proyecto_usuarios pu
            JOIN usuarios u ON pu.usuario_id = u.id
            JOIN roles r ON pu.rol_id = r.id
            WHERE pu.proyecto_id = %s;
            """, 
            (proyecto_id,)
        )
        return cursor.fetchall()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if conn: conn.close()



# ------------------------------------------------------------------
# 3. FUNCIONES DE BASE DE DATOS (SERVICIO DE DATOS BASE)
# ------------------------------------------------------------------

# Función de Creación de Proyecto

# Función para crear proyectos (set_proyecto) - CON CAMPO TIPO_INDUSTRIA AÑADIDO
async def set_proyecto(datos: ProyectoCrear) -> List[Dict[str, Any]]:
    procesado = []
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Validar existencia del usuario (código existente)
        cursor.execute("SELECT id FROM usuarios WHERE id = %s", (datos.usuario_id))
        usuario_row = cursor.fetchone()
        if not usuario_row:
            return [{"status": "error", "message": f"El usuario con id: '{datos.usuario_id}' no existe"}]
    
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, usuario_id, tipo_industria) VALUES (%s, %s, %s, %s)",
            (datos.nombre, datos.descripcion, datos.usuario_id, datos.tipo_industria) # 🚨 Pasar el nuevo valor
        )
        
        #  2. Obtener el ID del proyecto recién creado
        proyecto_id = conn.insert_id() 
        
        # Obtener el ID del rol 'Administrador'
        cursor.execute("SELECT id FROM roles WHERE nombre_rol = 'Administrador'")
        rol_admin_row = cursor.fetchone()
        ROL_ADMIN_ID = rol_admin_row['id'] if rol_admin_row else 1 
        
        # 3. Asignar al creador el rol de Administrador en proyecto_usuarios
        cursor.execute(
            "INSERT INTO proyecto_usuarios (proyecto_id, usuario_id, rol_id) VALUES (%s, %s, %s)",
            (proyecto_id, datos.usuario_id, ROL_ADMIN_ID)
        )

        conn.commit()
        await registrar_actividad_db(
            usuario_id=datos.usuario_id,    # El ID del usuario que crea
            proyecto_id=proyecto_id,        # El ID del proyecto recién creado
            tipo_evento='PROYECTO_CREADO',
            titulo=datos.nombre,            # El nombre del proyecto
            fuente="Módulo de Proyectos"
        )
        # Incluir el nuevo campo en la respuesta de procesado
        procesado.append({
            "nombre": datos.nombre, 
            "descripcion": datos.descripcion, 
            "usuario_id": datos.usuario_id, 
            "proyecto_id": proyecto_id,
            "tipo_industria": datos.tipo_industria, 
            "status": "success"
        })
    except Exception as e:
        if conn: conn.rollback()
        procesado.append({"status": "error", "message": f"Unexpected Error: {str(e)}"})
    finally:
        if conn: conn.close()
    return procesado



# Función para actualizar datos del proyecto
async def actualizar_datos_proyecto(id: int, datos: ProyectoActualizar,usuario_id: int) -> List[Dict[str, Any]]:
    procesado = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # -----------------------------------------------------
        # 1. VALIDACIONES DE EXISTENCIA Y PROPIEDAD (Mantenidas)
        # -----------------------------------------------------
        
        # Validar existencia del proyecto
        cursor.execute("SELECT * FROM proyectos WHERE id = %s", (id,))
        proyecto_row = cursor.fetchone()
        if not proyecto_row:
            return [{"status": "error", "message": f"El proyecto con id: '{id}' no existe"}]

        # Validar que el usuario id exista
        cursor.execute("SELECT * FROM usuarios WHERE id = %s", (datos.usuario_id))
        usuario_row = cursor.fetchone()
        if not usuario_row:
            return [{"status": "error", "message": f"El usuario con id: '{datos.usuario_id}' no existe"}]
        
        # Validar que el proyecto le corresponda al usuario id 
        cursor.execute("SELECT * FROM proyectos WHERE id = %s AND usuario_id = %s", (id, datos.usuario_id))
        proyecto_valido = cursor.fetchone()
        if not proyecto_valido:
            return [{"status": "error", "message": f"El proyecto con id '{id}' no le pertenece al usuario con id '{datos.usuario_id}'"}]
            
        # -----------------------------------------------------
        # 2. CONSTRUCCIÓN DEL UPDATE (Añadido tipo_industria)
        # -----------------------------------------------------
        campos = []
        valores = []
        
        if datos.nombre is not None: 
            campos.append("nombre = %s")
            valores.append(datos.nombre)
            
        if datos.descripcion is not None: 
            campos.append("descripcion = %s")
            valores.append(datos.descripcion)
            
       # Código de tu función:
        if datos.tipo_industria is not None: 
            campos.append("tipo_industria = %s")
            valores.append(datos.tipo_industria) 
            
        valores.append(id) 	# Para el WHERE

        # -----------------------------------------------------
        # 3. EJECUCIÓN
        # -----------------------------------------------------
        if campos:
            sql = f"UPDATE proyectos SET {', '.join(campos)} WHERE id = %s"
            cursor.execute(sql, valores)
            conn.commit()
            procesado.append({
                "status": "success", 
                "message": f"Proyecto {id} actualizado correctamente", 
                "actualizado": {
                    "nombre": datos.nombre, 
                    "descripcion": datos.descripcion,
                    "tipo_industria": datos.tipo_industria 
                }
            })
            await registrar_actividad_db(
                usuario_id=usuario_id,
                proyecto_id=id,
                tipo_evento='PROYECTO_MODIFICADO',
                titulo=datos.nombre, # El nuevo nombre del proyecto
                fuente="Módulo de Proyectos"
            )
        else:
            procesado.append({"status": "warning", "message": "No se proporcionaron datos para actualizar"})
            
    except Exception as e:
        if conn: conn.rollback()
        procesado.append({"status": "error", "message": f"Error: {str(e)}"})
    finally:
        if conn: conn.close()
        
    return procesado


async def eliminar_proyecto_db(id: Optional[int], usuario_id: int) -> Dict:
    conn = None
    nombre_proyecto_eliminado = "" # Variable para guardar el nombre
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor) 
        

        # Obtenemos el nombre ANTES de borrarlo
        cursor.execute("SELECT nombre, usuario_id FROM proyectos WHERE id = %s", (id,))
        proyecto_row = cursor.fetchone() 
        
        if not proyecto_row:
             raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
        if proyecto_row['usuario_id'] != usuario_id:
             raise HTTPException(status_code=403, detail="No autorizado para eliminar este proyecto.")

        # Guardamos el nombre para el log
        nombre_proyecto_eliminado = proyecto_row['nombre']


        proyecto_id = id # Usamos el ID directamente del query
        
        # Obtener los datos necesarios para el bucle (Lógica original)
        cursor.execute("SELECT id FROM proyectos WHERE id = %s AND usuario_id = %s", (proyecto_id, usuario_id))
        proyectos = cursor.fetchall()
        
        # 3. ELIMINACIÓN EN CASCADA (Tu lógica original)
        for proyecto in proyectos:
            proyecto_id_actual = proyecto["id"] 

            # Eliminar proyecto_usuarios primero
            cursor.execute("DELETE FROM proyecto_usuarios WHERE proyecto_id = %s", (proyecto_id_actual,)) 

            # Obtener dispositivos
            cursor.execute("SELECT id FROM dispositivos WHERE proyecto_id = %s", (proyecto_id_actual,))
            dispositivos = cursor.fetchall()

            for dispositivo in dispositivos:
                dispositivo_id = dispositivo["id"]
                
                # Obtener sensores
                cursor.execute("SELECT id FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
                sensores = cursor.fetchall()

                for sensor in sensores:
                    sensor_id = sensor["id"]
                    
                    # Obtener campos
                    cursor.execute("SELECT id FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))
                    campos = cursor.fetchall()

                    for campo in campos:
                       
                        pass

                    # Eliminar campos del sensor
                    cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))

                # Eliminar sensores del dispositivo
                cursor.execute("DELETE FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))

            # Eliminar dispositivos del proyecto
            cursor.execute("DELETE FROM dispositivos WHERE proyecto_id = %s", (proyecto_id_actual,))

            # Eliminar el proyecto
            cursor.execute("DELETE FROM proyectos WHERE id = %s", (proyecto_id_actual,))

        conn.commit() 
        
       
        await registrar_actividad_db(
            usuario_id=usuario_id,
            proyecto_id=None, # El ID ya no existe en la DB
            tipo_evento='PROYECTO_ELIMINADO',
            titulo=nombre_proyecto_eliminado, # El nombre que guardamos
            fuente="Módulo de Proyectos"
        )
        # -------------------------------------------------
        
        # Mensaje de éxito usando el nombre capturado
        return {"status": "success", "message": f"Proyecto '{nombre_proyecto_eliminado}' (ID: {id}) eliminado exitosamente."}

    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Fallo de DB: {str(e)}")
    finally:
        if conn: conn.close()




# async def eliminar_proyecto_db(id: Optional[int], usuario_id: int) -> Dict:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor) 
        
#         # ... (1. VALIDACIÓN DE PROPIEDAD Y EXISTENCIA - sin cambios) ...
#         cursor.execute("SELECT usuario_id FROM proyectos WHERE id = %s", (id,))
#         proyecto_row = cursor.fetchone() 
     

#         proyecto_id = id # Usamos el ID directamente del query
        
#         # Obtener los datos necesarios para el bucle (solo si vas a usarlo)
#         cursor.execute("SELECT id FROM proyectos WHERE id = %s AND usuario_id = %s", (proyecto_id, usuario_id))
#         proyectos = cursor.fetchall()
        
#         # 🚨 2. ELIMINACIÓN EN CASCADA (ORDEN CORREGIDO)
#         for proyecto in proyectos:
#             proyecto_id_actual = proyecto["id"] 

#             # 🚨 CRÍTICO: ELIMINAR PROYECTO_USUARIOS PRIMERO 🚨
#             # Esto resuelve el error 1451
#             cursor.execute("DELETE FROM proyecto_usuarios WHERE proyecto_id = %s", (proyecto_id_actual,)) 

#             # Obtener dispositivos
#             cursor.execute("SELECT id FROM dispositivos WHERE proyecto_id = %s", (proyecto_id_actual,))
#             dispositivos = cursor.fetchall()

#             for dispositivo in dispositivos:
#                 dispositivo_id = dispositivo["id"]
                
#                 # Obtener sensores
#                 cursor.execute("SELECT id FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
#                 sensores = cursor.fetchall()

#                 for sensor in sensores:
#                     sensor_id = sensor["id"]
                    
#                     # Obtener campos
#                     cursor.execute("SELECT id FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))
#                     campos = cursor.fetchall()

#                     for campo in campos:
#                         # Eliminar valores registrados
#                         cursor.execute("DELETE FROM valores WHERE campo_id = %s", (campo["id"],))

#                     # Eliminar campos del sensor
#                     cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))

#                 # Eliminar sensores del dispositivo
#                 cursor.execute("DELETE FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))

#             # Eliminar dispositivos del proyecto
#             cursor.execute("DELETE FROM dispositivos WHERE proyecto_id = %s", (proyecto_id_actual,))

#             # Eliminar el proyecto (AHORA ES SEGURO ELIMINAR LA FILA PADRE)
#             cursor.execute("DELETE FROM proyectos WHERE id = %s", (proyecto_id_actual,))

#         conn.commit()
        
#         return {"status": "success", "message": f"Proyecto {id} eliminado exitosamente."}

#     except Exception as e:
#         if conn: conn.rollback()
#         # 🚨 Mantenemos el detalle del error para cualquier nuevo fallo
#         raise HTTPException(status_code=500, detail=f"Fallo de DB: {str(e)}")
#     finally:
#         if conn: conn.close()

# # Función de Eliminación de Proyecto (eliminar_proyecto_db)
# async def eliminar_proyecto_db(id: Optional[int], usuario_id: int) -> Dict:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # 🚨 VALIDACIÓN DE PROPIEDAD: Asegurar que el usuario_id puede eliminar el proyecto
#         cursor.execute("SELECT * FROM proyectos WHERE id = %s", (id,))
#         if not cursor.fetchone(): 
#             return {"status": "error", "message": f"El proyecto con id: '{id}' no existe"}
        
#         cursor.execute("SELECT * FROM proyectos WHERE id = %s AND usuario_id = %s", (id, usuario_id))
#         if not cursor.fetchone(): 
#             return {"status": "error", "message": f"El proyecto con id '{id}' no le pertenece al usuario con id '{usuario_id}'"}
        
#         # Obtener proyectos a eliminar
#         if id is not None:
#             cursor.execute("SELECT id FROM proyectos WHERE id = %s AND usuario_id = %s", (id, usuario_id))
#         else:
#             cursor.execute("SELECT id FROM proyectos WHERE usuario_id = %s", (usuario_id))
            
#         proyectos = cursor.fetchall()
#         if not proyectos: 
#             return {"status": "error", "message": "No se encontraron proyectos para eliminar"}

#         # 🚨 Lógica de eliminación en cascada (TU CÓDIGO ORIGINAL)
#         for proyecto in proyectos:
#             proyecto_id = proyecto["id"]
#             cursor.execute("SELECT id FROM dispositivos WHERE proyecto_id = %s", (proyecto_id,))
#             dispositivos = cursor.fetchall()
#             for dispositivo in dispositivos:
#                 dispositivo_id = dispositivo["id"]
#                 cursor.execute("SELECT id FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
#                 sensores = cursor.fetchall()
#                 for sensor in sensores:
#                     sensor_id = sensor["id"]
#                     cursor.execute("SELECT id FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))
#                     campos = cursor.fetchall()
#                     for campo in campos:
#                         cursor.execute("DELETE FROM valores WHERE campo_id = %s", (campo["id"],))
#                     cursor.execute("DELETE FROM campos_sensores WHERE sensor_id = %s", (sensor_id,))
#                 cursor.execute("DELETE FROM sensores WHERE dispositivo_id = %s", (dispositivo_id,))
#             cursor.execute("DELETE FROM dispositivos WHERE proyecto_id = %s", (proyecto_id,))
#             cursor.execute("DELETE FROM proyectos WHERE id = %s", (proyecto_id,))

#         conn.commit()
#         return {"status": "success", "message": f"{len(proyectos)} proyecto(s) eliminado(s) correctamente para el usuario con ID '{usuario_id}'."}
        
#     except Exception as e:
#         if conn: conn.rollback()
#         raise HTTPException(status_code=500, detail=f"Error al eliminar proyecto(s): {str(e)}")
#     finally:
#         if conn: conn.close()




# # ------------------------------------------------------------------
# # 2. ENDPOINT DE GESTIÓN DE ACCESO (NUEVA FUNCIONALIDAD JWT)
# # ------------------------------------------------------------------

# # Endpoint para generar el link de invitación (Protegido)
# @router_proyecto.post("/proyectos/{proyecto_id}/invitar")
# async def generar_link_invitacion(
#     proyecto_id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         invitation_expires = timedelta(hours=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES / 60)
#         invitation_token = create_access_token(
#             data={"sub": str(current_user_id), "project_id": proyecto_id, "type": "INVITE"},
#             expires_delta=invitation_expires
#         )
#        #cuando es para cuando es en tu propia maquina 
#         BASE_FRONTEND_URL = "http://localhost:8081" 
        
#         #cuando es para que lo puedan ver en la misma red local
#         # BASE_FRONTEND_URL = "http://172.21.235.58:8080" 
 

#         link_completo = f"{BASE_FRONTEND_URL}/join?token={invitation_token}"

#         return {"status": "success", "link": link_completo, "expira_en_horas": invitation_expires.total_seconds() / 3600}
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al generar link: {str(e)}")


# # app/api/rutas/proyectos/proyectos.py (Añadir a la sección de Endpoints de Gestión)

# @router_proyecto.delete("/proyectos/{proyecto_id}/miembros/{usuario_id_a_remover}")
# async def remove_project_member(
#     proyecto_id: int,
#     usuario_id_a_remover: int,
#     current_user_id: int = Depends(get_current_user_id) # El usuario que realiza la acción
# ):
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()

#         # 🚨 1. AUTORIZACIÓN (CRÍTICO): Verificar si el current_user_id es el propietario/admin del proyecto
#         # NOTA: En un sistema real, aquí harías una consulta para verificar el rol.
#         # Por simplicidad, verificaremos que el current_user_id sea el propietario registrado del proyecto.
#         cursor.execute("SELECT usuario_id FROM proyectos WHERE id = %s", (proyecto_id,))
#         project_owner = cursor.fetchone()
        
#         if not project_owner or project_owner['usuario_id'] != current_user_id:
#              raise HTTPException(status_code=403, detail="Solo el propietario del proyecto puede remover miembros.")

#         # 🚨 2. PROPIEDAD: No permitir que el propietario se auto-elimine
#         if usuario_id_a_remover == current_user_id:
#              raise HTTPException(status_code=400, detail="No puedes remover al propietario del proyecto.")

#         # 🚨 3. ELIMINACIÓN DE LA MEMBRESÍA
#         cursor.execute(
#             "DELETE FROM proyecto_usuarios WHERE proyecto_id = %s AND usuario_id = %s",
#             (proyecto_id, usuario_id_a_remover)
#         )
#         conn.commit()

#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="El usuario no era miembro de este proyecto.")

#         return {"status": "success", "message": f"Usuario {usuario_id_a_remover} removido del proyecto {proyecto_id}."}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
#     finally:
#         if conn: conn.close()

# # Endpoint para procesar la unión al proyecto
# @router_proyecto.post("/join-project/{invitation_token}")
# async def process_join_project(
#     invitation_token: str,
#     current_user_id: int = Depends(get_current_user_id), 
# ):
#     conn = None
#     try:
#         invitation_data = validate_invitation_token(invitation_token)
#         project_id = invitation_data.get("project_id")
#         ROL_OBSERVADOR_ID = 3 
        
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         cursor.execute(
#             """
#             INSERT INTO proyecto_usuarios (proyecto_id, usuario_id, rol_id) 
#             VALUES (%s, %s, %s)
#             ON DUPLICATE KEY UPDATE rol_id = rol_id;
#             """, 
#             (project_id, current_user_id, ROL_OBSERVADOR_ID)
#         )
#         conn.commit()
        
#         return {"status": "success", "message": "Te has unido al proyecto exitosamente.", "project_id": project_id}

#     except pymysql.Error as e:
#         if e.args[0] == 1062:
#             return {"status": "warning", "message": "Ya eres miembro de este proyecto."}
#         raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
#     finally:
#         if conn: conn.close()
# # app/api/rutas/proyectos/proyectos.py


# #  Endpoint para obtener miembros de un proyecto específico (AÑADIDO)
# @router_proyecto.get("/proyectos/{proyecto_id}/miembros")
# async def get_project_members(
#     proyecto_id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     conn = None
#     try:
#         # 🚨 USAMOS get_db_connection (que está importada arriba)
#         # El warning debería desaparecer al llamar la función correctamente
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # Lógica de DB
#         cursor.execute(
#             """
#             SELECT 
#                 u.id AS usuario_id,
#                 u.nombre_usuario, 
#                 r.nombre_rol
#             FROM proyecto_usuarios pu
#             JOIN usuarios u ON pu.usuario_id = u.id
#             JOIN roles r ON pu.rol_id = r.id
#             WHERE pu.proyecto_id = %s;
#             """, 
#             (proyecto_id,)
#         )
#         members = cursor.fetchall()

#         # Nota: Aquí se añadiría la validación de permisos de vista si fuera necesario
        
#         return members

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al obtener miembros: {str(e)}")
#     finally:
#         if conn: conn.close()
