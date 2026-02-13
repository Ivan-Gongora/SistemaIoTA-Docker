# app/db/crud/recibos_crud.py

import pymysql
from typing import List, Dict, Any, Optional,Tuple
import logging

# Asumo que esta función existe en tu proyecto
from app.servicios.servicio_simulacion import get_db_connection 

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------
# Función para obtener los nombres de lotes (la que necesitas para el frontend)
# --------------------------------------------------------------------------------
def get_nombres_lotes_by_user_id(user_id: int) -> List[str]:
    """
    Obtiene una lista de nombres de lotes únicos para un usuario específico desde la BD.
    Utiliza PyMySQL.
    """
    conn = None
    try:
        conn = get_db_connection()
        # Forzamos DictCursor para acceder por nombre de columna de forma segura,
        # ya que el cursor por defecto parece estar comportándose como tal.
        cursor = conn.cursor(pymysql.cursors.DictCursor) 

        query = "SELECT DISTINCT lote_nombre FROM recibos_energia WHERE usuario_id = %s ORDER BY lote_nombre"
        cursor.execute(query, (user_id,))
        
        # Acceder por nombre de columna ('lote_nombre')
        lotes = [row['lote_nombre'] for row in cursor.fetchall()] 
        
        return lotes

    except pymysql.Error as e:
        logger.error(f"Error de PyMySQL al obtener lotes para usuario {user_id}: {e}")
        # En el contexto de FastAPI, una excepción aquí debe ser manejada por la ruta
        raise
    finally:
        if conn:
            conn.close()

# --------------------------------------------------------------------------------
# La función get_all_recibos_by_lotes (necesaria para get_analizador)
# --------------------------------------------------------------------------------
def get_all_recibos_by_lotes(user_id: int, lotes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Obtiene todos los recibos de energía para un usuario, filtrados por la lista de lotes.
    """
    conn = None
    try:
        conn = get_db_connection()
        # Usamos DictCursor aquí también, ya que es el formato esperado para Pandas/Analizador
        cursor = conn.cursor(pymysql.cursors.DictCursor) 

        # 1. Base de la consulta
        query = "SELECT * FROM recibos_energia WHERE usuario_id = %s"
        params: List[Any] = [user_id]
        
        # 2. Aplicar filtro de lotes si se especifican
        if lotes and len(lotes) > 0:
            placeholders = ', '.join(['%s'] * len(lotes))
            query += f" AND lote_nombre IN ({placeholders})"
            params.extend(lotes)
        
        query += " ORDER BY periodo ASC"
        
        cursor.execute(query, tuple(params))
        resultados_db = cursor.fetchall()
        
        # Aseguramos que se devuelva una lista de diccionarios
        return list(resultados_db)

    except pymysql.Error as e:
        logger.error(f"Error de PyMySQL al obtener recibos para usuario {user_id}: {e}")
        raise
    finally:
        if conn:
            conn.close()
            
            
def insertar_multiples_recibos(
    conn: pymysql.connections.Connection, 
    registros: List[Tuple]
) -> int:
    """
    Inserta una lista de tuplas de datos de recibos de energía en la base de datos.
    
    Args:
        conn: Objeto de conexión a la base de datos PyMySQL.
        registros: Lista de tuplas, donde cada tupla contiene los valores
                   para una fila de recibo en el orden correcto de las columnas.
                   (usuario_id, periodo, consumo_total_kwh, demanda_maxima_kw, 
                    costo_total, dias_facturados, factor_potencia, tarifa, 
                    kwh_punta, fecha_carga, lote_nombre)
    Returns:
        El número de filas insertadas.
    """
    cursor = conn.cursor()
    columnas_db = [
        'usuario_id', 'periodo', 'consumo_total_kwh', 'demanda_maxima_kw', 
        'costo_total', 'dias_facturados', 'factor_potencia', 'tarifa', 
        'kwh_punta', 'fecha_carga', 'lote_nombre'
    ]
    placeholders = ', '.join(['%s'] * len(columnas_db))
    query = f"INSERT INTO recibos_energia ({', '.join(columnas_db)}) VALUES ({placeholders})"
    
    num_inserted = cursor.executemany(query, registros)
    cursor.close()
    return num_inserted