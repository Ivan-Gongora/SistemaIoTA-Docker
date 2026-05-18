import pandas as pd
import pymysql
from typing import Optional
from app.servicios.servicio_simulacion import get_db_connection
import logging

logger = logging.getLogger("servicio_extraccion_analitica")

def extraer_datos_dispositivo_df(dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
    """
    Consulta la base de datos y formatea los registros en una matriz estructurada.
    Cruza los valores numéricos y de texto en columnas individuales por cada segundo de lectura.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Filtramos por dispositivo y unimos campos, sensores y valores
        sql = """
        SELECT 
            v.fecha_hora_lectura,
            cs.nombre as campo,
            COALESCE(v.valor, v.valor_texto) as valor_final
        FROM valores v
        JOIN campos_sensores cs ON v.campo_id = cs.id
        JOIN sensores s ON cs.sensor_id = s.id
        WHERE s.dispositivo_id = %s 
          AND v.fecha_hora_lectura BETWEEN %s AND %s
        ORDER BY v.fecha_hora_lectura ASC
        """
        
        cursor.execute(sql, (dispositivo_id, f"{fecha_inicio} 00:00:00", f"{fecha_fin} 23:59:59"))
        registros = cursor.fetchall()
        
        if not registros:
            return pd.DataFrame()
            
        df_crudo = pd.DataFrame(registros)
        
        # Transformamos las filas en columnas según el nombre del campo
        df_pivoteado = df_crudo.pivot_table(
            index='fecha_hora_lectura', 
            columns='campo', 
            values='valor_final', 
            aggfunc='first'
        ).reset_index()
        
        # Aseguramos que los campos matemáticos sean detectados como números
        columnas_numericas = [
            'Energia', 'Potencia', 'Corriente', 'Temperatura', 
            'Humedad', 'Iluminacion', 'Movimiento', 
            'Estado_Luz_Ideal', 'Estado_Clima_Ideal'
        ]
        
        for col in columnas_numericas:
            if col in df_pivoteado.columns:
                df_pivoteado[col] = pd.to_numeric(df_pivoteado[col], errors='coerce').fillna(0.0)
                
        # Los campos de texto como Motivo_Luz mantienen su formato original
        return df_pivoteado
        
    except Exception as e:
        logger.error(f"Falla en extracción de datos para análisis: {str(e)}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()