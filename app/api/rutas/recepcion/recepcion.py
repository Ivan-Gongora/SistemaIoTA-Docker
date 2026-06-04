from datetime import datetime

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging
from pydantic import BaseModel

# Importación de modelos y servicios con lógica de blindaje
from app.api.modelos.recepcion_datos import PayloadDispositivo
from app.servicios.servicio_recepcion import (
    procesar_lectura_individual_db,
    procesar_lote_datos_db
)
from app.servicios.agregador_historico import procesar_agregaciones_historicas

logger = logging.getLogger("recepcion_api")
router_recepcion = APIRouter()

class SolicitudAgregacion(BaseModel):
    dispositivo_id: int
    fecha_inicio: str
    fecha_fin: str
@router_recepcion.post("/guardar_json/")
async def recibir_datos_dispositivo(datos: PayloadDispositivo):
    """
    Punto de acceso para telemetría en tiempo real.
    Soporta flujo constante de múltiples dispositivos.
    """
    try:
        resultado = await procesar_lectura_individual_db(datos)
        
        if resultado.get("status") == "error":
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=resultado
            )
            
        return resultado

    except Exception as e:
        logger.error(f"Falla inesperada en recepción individual: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Falla interna en el servidor de datos."}
        )


@router_recepcion.post("/guardar_lote_json/")
async def recibir_lote_datos_dispositivo(lote: List[PayloadDispositivo]):
    """
    Guarda los datos crudos a máxima velocidad.
    Evita lanzar tareas de fondo concurrentes para prevenir Deadlocks.
    """
    if not lote:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"status": "error", "message": "El lote enviado no contiene registros."}
        )
    
    try:
        resultado = await procesar_lote_datos_db(lote)
        
        if resultado.get("status") == "error":
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=resultado
            )
            
        return resultado

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "El proceso de carga masiva se interrumpió."}
        )

@router_recepcion.post("/sincronizar_agregaciones/")
async def sincronizar_agregaciones(datos: SolicitudAgregacion, background_tasks: BackgroundTasks):
    """
    Ejecuta la consolidación matemática de las tablas una única vez al final.
    """
    try:
        background_tasks.add_task(
            procesar_agregaciones_historicas, 
            datos.dispositivo_id, 
            datos.fecha_inicio, 
            datos.fecha_fin
        )
        return {"status": "success", "message": "Consolidación de tablas en proceso"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "Falla al programar la consolidación."}
        )

# @router_recepcion.post("/guardar_lote_json/")
# async def recibir_lote_datos_dispositivo(lote: List[PayloadDispositivo], background_tasks: BackgroundTasks):
#     """
#     Punto de acceso para sincronización masiva de archivos CSV.
#     Guarda datos crudos y lanza la agregación en segundo plano.
#     """
#     if not lote:
#         return JSONResponse(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             content={"status": "error", "message": "El lote enviado no contiene registros."}
#         )
    
#     try:
#         # 1. Guardado masivo y rápido de datos crudos
#         resultado = await procesar_lote_datos_db(lote)
        
#         if resultado.get("status") == "error":
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content=resultado
#             )
            
#         # 2. Extracción de límites de fecha del lote actual
#         try:
#             dispositivo_id = int(lote[0].dispositivo)
#             fechas = []
#             for item in lote:
#                 try:
#                     fechas.append(datetime.strptime(f"{item.fecha} {item.hora}", "%Y-%m-%d %H:%M:%S"))
#                 except ValueError:
#                     continue
            
#             if fechas:
#                 fecha_inicio = min(fechas)
#                 fecha_fin = max(fechas)
                
#                 # 3. Disparo silencioso de las matemáticas pesadas
#                 background_tasks.add_task(
#                     procesar_agregaciones_historicas, 
#                     dispositivo_id, 
#                     fecha_inicio, 
#                     fecha_fin
#                 )
#         except Exception as ex_bg:
#             logger.error(f"Falla al programar agregación de fondo: {str(ex_bg)}")

#         return resultado

#     except Exception as e:
#         logger.error(f"Falla crítica en procesamiento de lote: {str(e)}")
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content={"status": "error", "message": "El proceso de carga masiva se interrumpió."}
#         )
# @router_recepcion.post("/guardar_lote_json/")
# async def recibir_lote_datos_dispositivo(lote: List[PayloadDispositivo]):
#     """
#     Punto de acceso para sincronización masiva de archivos CSV.
#     Procesa bloques de datos en una sola transacción SQL.
#     """
#     if not lote:
#         return JSONResponse(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             content={"status": "error", "message": "El lote enviado no contiene registros."}
#         )
    
#     try:
#         resultado = await procesar_lote_datos_db(lote)
        
#         if resultado.get("status") == "error":
#             return JSONResponse(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 content=resultado
#             )
            
#         return resultado

#     except Exception as e:
#         logger.error(f"Falla crítica en procesamiento de lote: {str(e)}")
#         return JSONResponse(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             content={"status": "error", "message": "El proceso de carga masiva se interrumpió."}
#         )

# # app/api/rutas/recepcion.py

# from fastapi import APIRouter, HTTPException
# from fastapi.responses import JSONResponse
# from typing import Dict, Any

# # Importa el modelo de Pydantic y la función de servicio
# from app.api.modelos.recepcion_datos import PayloadDispositivo
# from app.servicios.servicio_recepcion import procesar_datos_dispositivo_db

# router_recepcion = APIRouter()
# #     {
# #   "proyecto": "1",
# #   "dispositivo": "1",
# #   "fecha": "2025-10-21",
# #   "hora": "14:3:00",
# #   "id_paquete": 527,
# #   "sensores": [{
# #       "nombre": "DHT22",
# #       "datos": {
# #         "Temperatura": 29.5,
# #         "Humedad": 87.9
# #       }
# #     },
# #     {
# #       "nombre": "SCT-013-000",
# #       "datos": {
# #         "Energia": 123.7,
# #         "Corriente": 23.45,
# #         "Potencia": 245.1
# #       }
# #     },
# #     {
# #       "nombre": "BH1750",
# #       "datos": {
# #         "Iluminacion": 684
# #       }
# #     },
# #     {
# #       "nombre": "PIR HC-SR501",
# #       "datos": {
# #         "Movimiento": 0
# #       }
# #     }
# #   ]
# # }

# @router_recepcion.post("/guardar_json/")
# async def recibir_datos_dispositivo(datos: PayloadDispositivo) -> Dict[str, Any]:
#     """
#     Endpoint de alta velocidad para la ingesta de datos de dispositivos IoT.
#     No requiere autenticación JWT de usuario.
#     """

#     try:
#         # Llama a la función de servicio que hace el trabajo pesado
#         resultado = await procesar_datos_dispositivo_db(datos)
#         return resultado
        
#     except HTTPException as e:
#         # Si el servicio lanzó una excepción HTTP (ej. 404), la relanza
#         raise e
#     except Exception as e:
#         # Captura cualquier otro error inesperado
#         return JSONResponse(
#             status_code=500,
#             content={"status": "error", "paquete_id": datos.id_paquete, "detail": str(e)}
#         )