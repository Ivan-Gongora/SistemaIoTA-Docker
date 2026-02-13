# app/servicios/energetico/gestion_datos_servicio.py (NUEVO ARCHIVO)

import pandas as pd
import io
import numpy as np
import pymysql
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
import logging

from app.api.modelos.energetico.energetico import ReciboEnergiaCrear
from app.db.crud import recibos_crud # Importamos el módulo CRUD para la inserción
from app.servicios.servicio_simulacion import get_db_connection # Asumo que este es el que usas para la DB

logger = logging.getLogger(__name__)

# Columnas requeridas que DEBEN estar en el CSV (Coinciden con ReciboEnergiaBase)
REQUIRED_COLUMNS = [
    'periodo', 'consumo_total_kwh', 'demanda_maxima_kw', 
    'costo_total', 'dias_facturados'
]

# Columnas que mapearemos a la BD
ALL_CSV_COLUMNS = [
    'periodo', 'consumo_total_kwh', 'demanda_maxima_kw', 
    'factor_potencia', 'costo_total', 'dias_facturados', 
    'tarifa', 'kwh_punta'
]

async def procesar_y_guardar_csv_recibos(
    file_contents: bytes, 
    lote_nombre: str, 
    user_id: int
) -> int:
    """
    Función de servicio que lee el contenido de un CSV, lo procesa, valida
    y guarda los registros de recibos de energía en la base de datos.
    
    Args:
        file_contents: Contenido binario del archivo CSV.
        lote_nombre: Nombre del lote para los nuevos registros.
        user_id: ID del usuario que sube los datos.
        
    Returns:
        El número de registros insertados.
        
    Raises:
        ValueError: Si hay errores de validación de datos o de formato CSV.
        pymysql.err.IntegrityError: Si hay un error de clave duplicada en la DB.
        Exception: Para otros errores inesperados.
    """
    if not lote_nombre or lote_nombre.strip() == "":
        raise ValueError("El nombre del lote no puede estar vacío.")

    data_io = io.StringIO(file_contents.decode('utf-8'))
    df = pd.read_csv(data_io)

    # 1. Validación de Columnas y Limpieza de Pandas
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Falta la columna requerida en el CSV: '{col}'")
    
    columnas_a_usar = [col for col in ALL_CSV_COLUMNS if col in df.columns]
    df_limpio = df[columnas_a_usar].copy()

    df_limpio['periodo'] = pd.to_datetime(df_limpio['periodo'], errors='coerce').dt.date
    
    numeric_cols = ['consumo_total_kwh', 'demanda_maxima_kw', 'costo_total', 
                    'factor_potencia', 'kwh_punta', 'dias_facturados']
    
    for col in numeric_cols:
        if col in df_limpio.columns:
            df_limpio[col] = pd.to_numeric(df_limpio[col], errors='coerce')

    # 2. Asignación de Metadatos y Validación con Pydantic
    registros_validos_para_db: List[Tuple] = []
    
    for index, row in df_limpio.iterrows():
        recibo_data = row.replace({np.nan: None, pd.NaT: None}).to_dict()

        recibo_data['usuario_id'] = user_id
        recibo_data['lote_nombre'] = lote_nombre.strip()
        recibo_data['fecha_carga'] = datetime.now() 
        
        try:
            recibo_validado = ReciboEnergiaCrear(**recibo_data)
            
            # Convertir a tupla simple para PyMySQL (orden de columnas DB)
            valores_tuple = (
                recibo_validado.usuario_id,
                recibo_validado.periodo,
                recibo_validado.consumo_total_kwh,
                recibo_validado.demanda_maxima_kw,
                recibo_validado.costo_total,
                recibo_validado.dias_facturados,
                recibo_validado.factor_potencia,
                recibo_validado.tarifa,
                recibo_validado.kwh_punta,
                recibo_validado.fecha_carga,
                recibo_validado.lote_nombre
            )
            registros_validos_para_db.append(valores_tuple)

        except Exception as e:
            logger.error(f"Error de validación Pydantic en fila {index+2} (lote '{lote_nombre}'): {e}")
            raise ValueError(f"Error de formato en la fila {index+2}: {str(e)}")

    if not registros_validos_para_db:
        raise ValueError("El CSV está vacío o no contiene datos válidos para insertar.")

    # 3. Inserción en Base de Datos a través de la capa CRUD
    conn = None
    try:
        conn = get_db_connection()
        num_inserted = recibos_crud.insertar_multiples_recibos(conn, registros_validos_para_db)
        conn.commit()
        return num_inserted
    except pymysql.err.IntegrityError as e:
        if conn: conn.rollback()
        # Puedes relanzar el error o transformarlo en uno más amigable
        if e.args[0] == 1062: 
            raise pymysql.err.IntegrityError(f"Error de duplicado: Ya existen datos para uno o más periodos en el lote '{lote_nombre}'. Intenta con otro nombre o revisa el CSV.")
        raise e # Relanzar otros errores de integridad
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error inesperado en servicio de carga CSV: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()