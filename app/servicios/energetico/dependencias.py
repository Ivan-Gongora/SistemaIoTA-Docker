# app/servicios/energetico/dependencias.py
# app/servicios/energetico/dependencias.py

import pandas as pd
from fastapi import Depends, HTTPException, status
from typing import Dict, Optional, Any
import logging
from datetime import datetime, timedelta # <-- Añadir estas importaciones

# 🎯 Importa la función de acceso a datos de PyMySQL
from app.db.crud.recibos_crud import get_all_recibos_by_lotes 

from app.servicios.energetico.analizador_historico import AnalizadorHistorico
from app.servicios.energetico.predictor_consumo import PredictorConsumo
from app.servicios.energetico.generador_escenarios import GeneradorEscenarios

# 🎯 Importa el ID de usuario para la carga inicial del Analizador
from app.servicios.auth_utils import get_current_user_id 

logger = logging.getLogger(__name__)

# --- Instancias Singleton (por usuario) ---
# Almacena una instancia de servicio por cada user_id para evitar recargas constantes del DataFrame de la DB
# También almacenaremos el DF completo aquí para el AnalizadorHistorico
analizador_instances: Dict[int, AnalizadorHistorico] = {}
predictor_instances: Dict[int, PredictorConsumo] = {}
generador_instances: Dict[int, GeneradorEscenarios] = {}

# Cache para el DataFrame de cada usuario (si decides usar el cache en get_analizador)
_df_cache: Dict[int, Dict[str, Any]] = {}
CACHE_EXPIRATION_MINUTES = 5 # Tiempo que el cache es válido

# ----------------------------------------------------
# FUNCIONES DE CACHE Y DEPENDENCIAS DE FASTAPI
# ----------------------------------------------------

# --- Función para invalidar la caché ---
def invalidate_user_dataframe_cache(user_id: int):
    """
    Invalida el DataFrame del usuario en el caché de `get_analizador`.
    Debe llamarse cuando los datos de un usuario en la DB cambian (ej. al cargar un nuevo CSV).
    """
    if user_id in _df_cache: # Si estás usando el _df_cache en get_analizador
        del _df_cache[user_id]
        logger.info(f"DEBUG: Caché del DataFrame invalidado para el user_id: {user_id}.")
    
    # También es crucial eliminar la instancia del analizador si la caché es por instancia
    # Si `get_analizador` SIEMPRE crea una nueva instancia con un DF fresco, esta parte es menos crítica.
    # Pero si se basa en `analizador_instances` directamente, necesitamos eliminarlo.
    if user_id in analizador_instances:
        del analizador_instances[user_id]
        logger.info(f"DEBUG: Instancia de AnalizadorHistorico eliminada para user_id: {user_id}.")
    # También para predictor y generador si estos también dependen de datos cargados de la DB
    if user_id in predictor_instances:
        del predictor_instances[user_id]
        logger.info(f"DEBUG: Instancia de PredictorConsumo eliminada para user_id: {user_id}.")
    if user_id in generador_instances:
        del generador_instances[user_id]
        logger.info(f"DEBUG: Instancia de GeneradorEscenarios eliminada para user_id: {user_id}.")


async def get_analizador(user_id: int = Depends(get_current_user_id)) -> AnalizadorHistorico:
    """
    Dependencia que provee una instancia (Singleton por usuario) del AnalizadorHistorico.
    Carga todos los recibos de energía del usuario desde la DB una sola vez por sesión,
    utilizando un caché con expiración.
    """
    current_time = datetime.now()

    # --- Lógica de caché para el DataFrame ---
    # Comprobar si el DataFrame está en caché y no ha expirado
    if user_id in _df_cache and (current_time - _df_cache[user_id]["timestamp"]) < timedelta(minutes=CACHE_EXPIRATION_MINUTES):
        logger.debug(f"DEBUG: Usando DataFrame de caché para el usuario {user_id}.")
        # Si el DataFrame está en caché, usamos esa versión para crear la instancia
        # Es importante devolver una COPIA del DF almacenado para evitar modificaciones no deseadas
        if user_id not in analizador_instances or analizador_instances[user_id].df_completo.empty: # Si la instancia no existe o su DF está vacío, la recreamos
             analizador_instances[user_id] = AnalizadorHistorico(_df_cache[user_id]["df"].copy())
        return analizador_instances[user_id]

    # Si no está en caché o ha expirado, o si la instancia no existe/está vacía, recargar de la DB
    logger.info(f"DEBUG: Recargando DataFrame de la DB para el usuario {user_id} (cache expirado o no encontrado).")
    
    try:
        # Cargar los datos del usuario desde la DB (sin filtrar lotes inicialmente)
        datos_db_raw = get_all_recibos_by_lotes(user_id=user_id, lotes=None)
        
        if not datos_db_raw:
            logger.warning(f"No se encontraron recibos de energía para el user_id: {user_id}. Inicializando Analizador con DF vacío.")
            df_completo_usuario = pd.DataFrame()
        else:
            df_completo_usuario = pd.DataFrame(datos_db_raw)
            logger.info(f"✅ [Dependencia] {len(df_completo_usuario)} recibos cargados para user_id: {user_id}.")
        
        # Actualizar caché
        _df_cache[user_id] = {"df": df_completo_usuario.copy(), "timestamp": current_time}
        
        # Crear la instancia del Analizador con el DataFrame cargado
        analizador_instances[user_id] = AnalizadorHistorico(df_completo=df_completo_usuario)
        
    except Exception as e:
        logger.error(f"❌ [Dependencia] Error crítico al cargar datos energéticos para user_id {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al inicializar el servicio de análisis energético: {e}"
        )
        
    return analizador_instances[user_id]


async def get_predictor(user_id: int = Depends(get_current_user_id)) -> PredictorConsumo:
    """
    Dependencia de FastAPI que provee una instancia (Singleton por usuario) del PredictorConsumo.
    """
    if user_id not in predictor_instances:
        logger.info(f"Iniciando instancia Singleton de PredictorConsumo para user_id: {user_id}...")
        predictor_instances[user_id] = PredictorConsumo()
    return predictor_instances[user_id]


async def get_generador_escenarios(
    analizador: AnalizadorHistorico = Depends(get_analizador),
    predictor: PredictorConsumo = Depends(get_predictor),
    user_id: int = Depends(get_current_user_id)
) -> GeneradorEscenarios:
    """
    Dependencia de FastAPI que provee una instancia (Singleton por usuario) del GeneradorEscenarios.
    Inyecta las instancias de Analizador y Predictor.
    """
    if user_id not in generador_instances:
        logger.info(f"Iniciando instancia Singleton de GeneradorEscenarios para user_id: {user_id}...")
        generador_instances[user_id] = GeneradorEscenarios(analizador=analizador, predictor=predictor)
    return generador_instances[user_id]
# import pandas as pd
# from fastapi import Depends, HTTPException, status
# from typing import Dict, Optional

# from app.servicios.energetico.analizador_historico import AnalizadorHistorico
# from app.servicios.energetico.predictor_consumo import PredictorConsumo
# from app.servicios.energetico.generador_escenarios import GeneradorEscenarios

# # 🎯 Importa la función de acceso a datos de PyMySQL
# from app.db.crud.recibos_crud import get_all_recibos_by_lotes 

# # 🎯 Importa el ID de usuario para la carga inicial del Analizador
# from app.servicios.auth_utils import get_current_user_id 

# import logging

# logger = logging.getLogger(__name__)

# # --- Instancias Singleton (por usuario) ---
# # Usaremos un diccionario para almacenar una instancia de AnalizadorHistorico por cada user_id
# # Esto es esencial porque AnalizadorHistorico ahora carga datos específicos de un usuario
# analizador_instances: Dict[int, AnalizadorHistorico] = {}
# predictor_instances: Dict[int, PredictorConsumo] = {} # También por usuario
# generador_instances: Dict[int, GeneradorEscenarios] = {} # Y el generador

# # ----------------------------------------------------
# # DEPENDENCIAS DE FASTAPI
# # ----------------------------------------------------

# async def get_analizador(user_id: int = Depends(get_current_user_id)) -> AnalizadorHistorico:
#     """
#     Dependencia de FastAPI que provee una instancia (Singleton por usuario) del AnalizadorHistorico.
#     Carga los datos de recibos de energía del usuario desde la DB una sola vez.
#     """
#     if user_id not in analizador_instances:
#         logger.info(f"Iniciando instancia Singleton de AnalizadorHistorico para user_id: {user_id}...")
        
#         try:
#             # Cargar los datos del usuario desde la DB usando PyMySQL
#             # Se pasan lotes=None para cargar TODOS los recibos del usuario inicialmente
#             datos_db_raw = get_all_recibos_by_lotes(user_id=user_id, lotes=None)
            
#             if not datos_db_raw:
#                 logger.warning(f"No se encontraron recibos de energía para el user_id: {user_id}. Inicializando Analizador con DF vacío.")
#                 df_completo_usuario = pd.DataFrame()
#             else:
#                 df_completo_usuario = pd.DataFrame(datos_db_raw)
#                 logger.info(f"✅ [Singleton] {len(df_completo_usuario)} recibos cargados para user_id: {user_id}.")
            
#             # Crear la instancia del Analizador con el DataFrame cargado
#             analizador_instances[user_id] = AnalizadorHistorico(df_completo=df_completo_usuario)
            
#         except Exception as e:
#             logger.error(f"❌ [Singleton] Error crítico al cargar datos energéticos para user_id {user_id}: {e}", exc_info=True)
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"Fallo al inicializar el servicio de análisis energético: {e}"
#             )
            
#     return analizador_instances[user_id]


# async def get_predictor(user_id: int = Depends(get_current_user_id)) -> PredictorConsumo:
#     """
#     Dependencia de FastAPI que provee una instancia (Singleton por usuario) del PredictorConsumo.
#     """
#     if user_id not in predictor_instances:
#         logger.info(f"Iniciando instancia Singleton de PredictorConsumo para user_id: {user_id}...")
#         predictor_instances[user_id] = PredictorConsumo()
#     return predictor_instances[user_id]


# async def get_generador_escenarios(
#     analizador: AnalizadorHistorico = Depends(get_analizador),
#     predictor: PredictorConsumo = Depends(get_predictor),
#     user_id: int = Depends(get_current_user_id) # Solo para registro, las sub-dependencias ya lo usan
# ) -> GeneradorEscenarios:
#     """
#     Dependencia de FastAPI que provee una instancia (Singleton por usuario) del GeneradorEscenarios.
#     Inyecta las instancias de Analizador y Predictor.
#     """
#     if user_id not in generador_instances:
#         logger.info(f"Iniciando instancia Singleton de GeneradorEscenarios para user_id: {user_id}...")
#         generador_instances[user_id] = GeneradorEscenarios(analizador=analizador, predictor=predictor)
#     return generador_instances[user_id]