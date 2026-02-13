import pymysql
from typing import Optional
from app.servicios.servicio_simulacion import get_db_connection

async def registrar_actividad_db(
    usuario_id: int,
    tipo_evento: str,
    titulo: str,
    fuente: str,
    proyecto_id: Optional[int] = None
):
    """
    Inserta un nuevo registro en la tabla de actividad reciente.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO actividad_reciente 
                (usuario_id, proyecto_id, tipo_evento, titulo, fuente, fecha)
            VALUES 
                (%s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (usuario_id, proyecto_id, tipo_evento, titulo, fuente))
        conn.commit()
        
    except Exception as e:
        # Si el log falla, no queremos que la operación principal (ej. crear proyecto) falle.
        # Así que solo imprimimos el error.
        print(f"Error al registrar actividad (usuario: {usuario_id}, evento: {tipo_evento}): {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()