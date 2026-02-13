import pymysql
from typing import Dict, Any
from datetime import datetime
from fastapi import HTTPException
from app.servicios.servicio_simulacion import get_db_connection, simular_datos_json


# -----------------------------------------------------------------------------
# 1. OBTENER DISPOSITIVOS GLOBALES
# -----------------------------------------------------------------------------
async def obtener_dispositivos_globales_paginado_db(
    current_user_id: int, page: int = 1, limit: int = 10, search: str = ""
) -> Dict[str, Any]:
    
    offset = (page - 1) * limit
    search_pattern = f"%{search}%"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql_base = """
        FROM dispositivos d
        JOIN proyectos p ON d.proyecto_id = p.id
        LEFT JOIN proyecto_usuarios pu ON p.id = pu.proyecto_id AND pu.usuario_id = %s
        WHERE (p.usuario_id = %s OR pu.usuario_id = %s)
          AND (d.nombre LIKE %s OR d.tipo LIKE %s OR p.nombre LIKE %s)
        """
        params_count = [current_user_id, current_user_id, current_user_id, search_pattern, search_pattern, search_pattern]
        
        cursor.execute(f"SELECT COUNT(DISTINCT d.id) as total {sql_base}", params_count)
        result_total = cursor.fetchone()
        total_records = result_total['total'] if result_total else 0
        
        sql_final = f"""
        SELECT DISTINCT d.id, d.nombre, d.descripcion, d.tipo, d.latitud, d.longitud, d.habilitado, d.fecha_creacion, d.proyecto_id, 
            p.nombre AS nombre_proyecto, p.usuario_id AS propietario_id
        {sql_base}
        ORDER BY d.id DESC LIMIT %s OFFSET %s
        """
        cursor.execute(sql_final, params_count + [limit, offset])
        dispositivos = cursor.fetchall()
        
        for disp in dispositivos:
            if 'habilitado' in disp: disp['habilitado'] = bool(disp['habilitado'])
            if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
                disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
            if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
            if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
            
        return {"data": dispositivos, "total": total_records, "page": page, "limit": limit}
    except Exception as e:
        print(f"Error DB globales: {e}")
        raise e
    finally:
        if conn: conn.close()

# -----------------------------------------------------------------------------
# 2. OBTENER DISPOSITIVOS POR PROYECTO (VERSIÓN LIMPIA)
# -----------------------------------------------------------------------------
async def obtener_dispositivos_por_proyecto_paginado_db(
    proyecto_id: int, 
    # usuario_id REMOVIDO: Ya no calculamos seguridad aquí
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
        
        # 1. Filtros simples (Solo Proyecto y Búsqueda)
        where_clause = "WHERE d.proyecto_id = %s AND (d.nombre LIKE %s OR d.tipo LIKE %s)"
        params_base = [proyecto_id, search_pattern, search_pattern]
        
        # 2. Total
        sql_count = f"SELECT COUNT(*) as total FROM dispositivos d {where_clause}"
        cursor.execute(sql_count, params_base)
        res_total = cursor.fetchone()
        total_records = res_total['total'] if res_total else 0
        
        # 3. Datos (SIN cálculo de rol)
        sql_data = f"""
        SELECT 
            d.id, d.nombre, d.descripcion, d.tipo, d.latitud, d.longitud, d.habilitado, d.fecha_creacion, d.proyecto_id,
            p.nombre AS nombre_proyecto,
            p.usuario_id AS propietario_id
        FROM dispositivos d
        JOIN proyectos p ON d.proyecto_id = p.id
        {where_clause}
        ORDER BY d.id DESC 
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(sql_data, params_base + [limit, offset])
        dispositivos = cursor.fetchall()
        
        # 4. Procesar datos
        for disp in dispositivos:
            if 'habilitado' in disp: disp['habilitado'] = bool(disp['habilitado'])
            if 'fecha_creacion' in disp and isinstance(disp['fecha_creacion'], datetime):
                disp['fecha_creacion'] = disp['fecha_creacion'].strftime(DATE_FORMAT)
            if disp.get('latitud') is not None: disp['latitud'] = float(disp['latitud'])
            if disp.get('longitud') is not None: disp['longitud'] = float(disp['longitud'])
        
        return {
            "data": dispositivos,
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": (total_records + limit - 1) // limit if limit > 0 else 0
        }

    except Exception as e:
        print(f"Error DB dispositivos paginados: {e}")
        raise e
    finally:
        if conn: conn.close()

# -----------------------------------------------------------------------------
# 3. RESUMEN DE DISPOSITIVO
# -----------------------------------------------------------------------------
async def get_resumen_dispositivo_db(dispositivo_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor) 
        
        # Última Conexión
        sql_ultima = """
        SELECT MAX(v.fecha_hora_lectura) AS ultima_conexion_dt
        FROM valores v
        JOIN campos_sensores cs ON v.campo_id = cs.id
        JOIN sensores s ON cs.sensor_id = s.id
        WHERE s.dispositivo_id = %s
        """
        cursor.execute(sql_ultima, (dispositivo_id,))
        res_conn = cursor.fetchone()
        ultima_conexion = res_conn['ultima_conexion_dt'] if res_conn else None
        
        # Campos Activos
        sql_activos = """
        SELECT COUNT(DISTINCT cs.id) AS count_campos_activos
        FROM campos_sensores cs
        JOIN sensores s ON cs.sensor_id = s.id
        WHERE s.dispositivo_id = %s AND cs.id IN (SELECT DISTINCT campo_id FROM valores)
        """
        cursor.execute(sql_activos, (dispositivo_id,))
        res_campos = cursor.fetchone()
        campos_activos = res_campos['count_campos_activos'] if res_campos else 0

        # Totales
        sql_totales = """
        SELECT 
            (SELECT COUNT(*) FROM dispositivos WHERE proyecto_id = (SELECT proyecto_id FROM dispositivos WHERE id = %s)) AS total_dispositivos,
            (SELECT COUNT(*) FROM sensores WHERE dispositivo_id = %s) AS total_sensores
        """
        cursor.execute(sql_totales, (dispositivo_id, dispositivo_id, dispositivo_id))
        totales = cursor.fetchone() or {}

        return {
            "ultima_conexion": ultima_conexion.isoformat() if ultima_conexion else None,
            "total_dispositivos": totales.get('total_dispositivos', 0),
            "total_sensores": totales.get('total_sensores', 0),
            "campos_activos": campos_activos,
            "estado_dispositivo": "Activo" 
        }
    except Exception as e:
        print(f"Error resumen: {e}")
        raise e
    finally:
        if conn: conn.close()

# -----------------------------------------------------------------------------
# 4. OBTENER UN DISPOSITIVO POR ID
# -----------------------------------------------------------------------------
async def obtener_dispositivo_por_id_db(dispositivo_id: int) -> Dict[str, Any]:
    conn = None
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
        SELECT d.*, p.nombre as nombre_proyecto, p.usuario_id as propietario_id
        FROM dispositivos d JOIN proyectos p ON d.proyecto_id = p.id
        WHERE d.id = %s
        """
        cursor.execute(sql, (dispositivo_id,))
        dispositivo = cursor.fetchone()

        if not dispositivo: return None
        
        if 'fecha_creacion' in dispositivo and isinstance(dispositivo['fecha_creacion'], datetime):
            dispositivo['fecha_creacion'] = dispositivo['fecha_creacion'].strftime(DATE_FORMAT)
        if 'habilitado' in dispositivo: dispositivo['habilitado'] = bool(dispositivo['habilitado'])
        if dispositivo.get('latitud') is not None: dispositivo['latitud'] = float(dispositivo['latitud'])
        if dispositivo.get('longitud') is not None: dispositivo['longitud'] = float(dispositivo['longitud'])

        return dispositivo
    except Exception as e:
        print(f"Error DB id: {e}")
        raise e
    finally:
        if conn: conn.close()