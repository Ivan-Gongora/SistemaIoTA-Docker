# app/api/rutas/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List,Dict,Any
import pymysql

from app.servicios.auth_utils import get_current_user_id
from app.servicios.servicio_simulacion import get_db_connection
from app.api.modelos.dashboard import ResumenKPIs,EstadoDispositivos,ActividadRecienteItem # Importa el nuevo modelo

# Crea un nuevo router
router_dashboard = APIRouter()

# -----------------------------------------------------------
# ENDPOINT: Resumen de KPIs para el Dashboard
# -----------------------------------------------------------
@router_dashboard.get("/plataforma/resumen-kpis", response_model=ResumenKPIs)
async def get_resumen_kpis(
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene los conteos agregados de los módulos IoT y Energía
    para las tarjetas del panel de control principal.
    """
    try:
        kpis = await obtener_conteo_kpis_db(current_user_id)
        return kpis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener KPIs del dashboard: {str(e)}")


@router_dashboard.get("/dashboard/actividad-reciente", response_model=List[ActividadRecienteItem])
async def get_actividad_reciente(
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Obtiene los 5 eventos más recientes de ambos módulos (IoT y Energía)
    para el feed de actividad del panel de control.
    """
    try:
        actividad = await obtener_actividad_reciente_db(current_user_id)
        return actividad
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener actividad: {str(e)}")


# -----------------------------------------------------------
# FUNCIÓN DE SERVICIO (Lógica de Base de Datos)
# -----------------------------------------------------------


async def obtener_actividad_reciente_db(usuario_id: int) -> List[Dict[str, Any]]:
    """
    Obtiene los 5 eventos más recientes DIRECTAMENTE de la tabla de actividad.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
        SELECT 
            tipo_evento as tipo,
            titulo,
            fuente,
            fecha
        FROM actividad_reciente
        WHERE usuario_id = %s
        ORDER BY fecha DESC
        LIMIT 5;
        """
        
        cursor.execute(sql, (usuario_id,))
        return cursor.fetchall()
        
    except Exception as e:
        print(f"Error en DB (obtener_actividad_reciente_db): {e}")
        raise e
    finally:
        if conn: conn.close()

# (Añadir a tu router_dashboard)
@router_dashboard.get("/dashboard/estado-dispositivos", response_model=EstadoDispositivos)
async def get_estado_dispositivos(
    current_user_id: int = Depends(get_current_user_id)
):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        sql = """
        SELECT 
            COUNT(CASE WHEN d.habilitado = 1 THEN 1 END) as activos,
            COUNT(d.id) as total
        FROM dispositivos d
        JOIN proyectos p ON d.proyecto_id = p.id
        WHERE p.usuario_id = %s;
        """
        cursor.execute(sql, (current_user_id,))
        data = cursor.fetchone()
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en DB: {str(e)}")
    finally:
        if conn: conn.close()
# -----------------------------------------------------------
# FUNCIÓN DE SERVICIO (Lógica de Base de Datos)
# -----------------------------------------------------------
async def obtener_conteo_kpis_db(usuario_id: int) -> Dict[str, Any]:
    """
    Ejecuta múltiples consultas COUNT para obtener los KPIs del dashboard.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 1. Conteo de Proyectos IoT
        sql_proyectos = "SELECT COUNT(*) as conteo FROM proyectos WHERE usuario_id = %s"
        cursor.execute(sql_proyectos, (usuario_id,))
        conteo_proyectos = cursor.fetchone()['conteo']

        # 2. Conteo de Dispositivos IoT (basado en los proyectos del usuario)
        sql_dispositivos = """
            SELECT COUNT(d.id) as conteo 
            FROM dispositivos d
            JOIN proyectos p ON d.proyecto_id = p.id
            WHERE p.usuario_id = %s
        """
        cursor.execute(sql_dispositivos, (usuario_id,))
        conteo_dispositivos = cursor.fetchone()['conteo']

        # 3. Conteo de Lotes de Energía (basado en recibos)
        sql_lotes = """
            SELECT COUNT(DISTINCT lote_nombre) as conteo 
            FROM recibos_energia 
            WHERE usuario_id = %s
        """
        cursor.execute(sql_lotes, (usuario_id,))
        conteo_lotes = cursor.fetchone()['conteo']

        conteo_simulaciones = 0 
        return {
            "conteo_proyectos_iot": conteo_proyectos,
            "conteo_dispositivos_iot": conteo_dispositivos,
            "conteo_lotes_energia": conteo_lotes,
            "conteo_simulaciones": conteo_simulaciones
        }
        
    except Exception as e:
        print(f"Error en DB (obtener_conteo_kpis_db): {e}")
        raise e
    finally:
        if conn: conn.close()