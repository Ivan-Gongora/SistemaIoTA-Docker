from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import logging

# Importación de modelos y servicios con lógica de blindaje
from app.api.modelos.recepcion_datos import PayloadDispositivo
from app.servicios.servicio_recepcion import (
    procesar_lectura_individual_db,
    procesar_lote_datos_db
)

logger = logging.getLogger("recepcion_api")
router_recepcion = APIRouter()

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
    Punto de acceso para sincronización masiva de archivos CSV.
    Procesa bloques de datos en una sola transacción SQL.
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
        logger.error(f"Falla crítica en procesamiento de lote: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": "El proceso de carga masiva se interrumpió."}
        )

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