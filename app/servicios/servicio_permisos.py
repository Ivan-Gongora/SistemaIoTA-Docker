import pymysql
from fastapi import HTTPException, status
from app.servicios.servicio_simulacion import get_db_connection

# ---------------------------------------------------------
# 1. EL VERIFICADOR MAESTRO
# ---------------------------------------------------------
async def verificar_permiso_proyecto(usuario_id: int, proyecto_id: int, permiso_requerido: str):
    """
    Verifica si el usuario tiene el 'permiso_requerido' dentro del 'proyecto_id'.
    Revisa si es el Dueño O si tiene un Rol asignado con ese permiso.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
        SELECT 1
        FROM proyectos p
        -- Unimos con la tabla de asignación de usuarios
        LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
        -- Unimos con roles y permisos para ver qué puede hacer ese rol
        LEFT JOIN roles r ON pu.rol_id = r.id
        LEFT JOIN rol_permisos rp ON r.id = rp.rol_id
        LEFT JOIN permisos per ON rp.permiso_id = per.id
        WHERE p.id = %s
          AND (
            p.usuario_id = %s       
            OR
            per.nombre_permiso = %s     
            OR 
            per.nombre_permiso = 'GESTION_USUARIOS_SISTEMA' 
          )
        LIMIT 1;
        """
        
        cursor.execute(sql, (usuario_id, proyecto_id, usuario_id, permiso_requerido))
        resultado = cursor.fetchone()
        
        if not resultado:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere el permiso: '{permiso_requerido}' en este proyecto."
            )
            
        return True # Pase concedido

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error verificando permisos: {e}")
        raise HTTPException(status_code=500, detail="Error interno validando permisos.")
    finally:
        if conn: conn.close()


async def obtener_rol_usuario_en_proyecto(usuario_id: int, proyecto_id: int):
    """
    Devuelve el rol del usuario dentro del proyecto:
    - PROPIETARIO (si es dueño)
    - COLABORADOR / OBSERVADOR según proyecto_usuarios
    - None si no tiene rol (pero sí podría ser PROPIETARIO)
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        SELECT 
            p.usuario_id AS propietario_id,
            r.nombre_rol AS rol_nombre
        FROM proyectos p
        LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
        LEFT JOIN roles r ON pu.rol_id = r.id
        WHERE p.id = %s
        """


        cursor.execute(sql, (usuario_id, proyecto_id))
        data = cursor.fetchone()

        if not data:
            return None

        # Dueño del proyecto
        if data["propietario_id"] == usuario_id:
            return "PROPIETARIO"

        # Si es colaborador / observador
        return data["rol_nombre"]

    finally:
        if conn:
            conn.close()

# ---------------------------------------------------------
# 2. AYUDANTES PARA RESOLVER PROYECTO_ID
# (Necesarios para endpoints de eliminar/editar sensor o dispositivo)
# ---------------------------------------------------------

async def obtener_proyecto_id_desde_dispositivo(dispositivo_id: int) -> int:
    conn = get_db_connection()
    #  Aseguramos que usamos DictCursor para consistencia
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT proyecto_id FROM dispositivos WHERE id = %s", (dispositivo_id,))
        row = cursor.fetchone()
    conn.close()
    
    if not row: 
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    
    #  ACCESO POR CLAVE (Correcto para DictCursor)
    return row['proyecto_id']

async def obtener_proyecto_id_desde_sensor(sensor_id: int) -> int:
    conn = get_db_connection()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("""
            SELECT d.proyecto_id 
            FROM sensores s 
            JOIN dispositivos d ON s.dispositivo_id = d.id 
            WHERE s.id = %s
        """, (sensor_id,))
        row = cursor.fetchone()
    conn.close()
    
    if not row: 
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    
    return row['proyecto_id']

#  Corrección 3: Campos
async def obtener_proyecto_id_desde_campo(campo_id: int) -> int:
    conn = get_db_connection()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("""
            SELECT d.proyecto_id 
            FROM campos_sensores cs
            JOIN sensores s ON cs.sensor_id = s.id
            JOIN dispositivos d ON s.dispositivo_id = d.id
            WHERE cs.id = %s
        """, (campo_id,))
        row = cursor.fetchone()
    conn.close()
    
    if not row: 
        raise HTTPException(status_code=404, detail="Campo no encontrado")
    
    return row['proyecto_id']