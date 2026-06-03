from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel 

from app.servicios.auth_utils import get_current_user_id
from app.servicios.servicio_valores import (
    obtener_ultimo_valor_db,
    obtener_historico_campo_db,
    obtener_rango_fechas_db,
    obtener_valores_ventana_db,
    aplicar_analisis_anomalias, 
    detectar_anomalia_individual, 
aplicar_analisis_historico
)

router = APIRouter()

class ValorGrafico(BaseModel):
    valor: float
    fecha_hora_lectura: datetime
    campo_id: Optional[int] = None
    nombre_campo: Optional[str] = None
    magnitud_tipo: Optional[str] = None
    simbolo_unidad: Optional[str] = None
    
    anomalia: bool = False
    mensaje_alerta: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------------------------------------------------------------
# 1. VENTANA DE TIEMPO (CON ANÁLISIS)
# ----------------------------------------------------------------------
@router.get("/valores/ventana/{campo_id}", response_model=List[ValorGrafico])
async def get_valores_ventana(
    campo_id: int,
    minutos: int = Query(5, description="Minutos hacia atrás"),
    # 🚨 Default True: El análisis inicia encendido
    analisis_activo: bool = Query(True, description="Activar detección"), 
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        valores = await obtener_valores_ventana_db(campo_id, minutos)
        if not valores: return []
        
        # Solo aplicamos el análisis si el usuario (frontend) lo solicita
        if analisis_activo:
            valores = aplicar_analisis_anomalias(valores)
            
        return valores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error DB: {str(e)}")


# ----------------------------------------------------------------------
# 2. HISTÓRICO (REPORTES)
# ----------------------------------------------------------------------
@router.get("/valores/historico-campo/{campo_id}", response_model=List[ValorGrafico])
async def get_valores_historicos(
    campo_id: int,
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    metodo_carga: str = Query("optimizado"), 
    incluir_analisis: bool = Query(False),
    
    # 🟢 NUEVOS PARÁMETROS (Con valores por defecto seguros)
    temp_min: float = Query(20.0),
    temp_max: float = Query(26.0),
    hum_min: float = Query(30.0),
    hum_max: float = Query(60.0),
    
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        if not fecha_fin: fecha_fin = datetime.now()
        if not fecha_inicio: fecha_inicio = fecha_fin - timedelta(days=7)

        # 1. Obtener datos
        valores = await obtener_historico_campo_db(campo_id, fecha_inicio, fecha_fin, metodo_carga)
        
        # 2. Aplicar Análisis HISTÓRICO con CONFIGURACIÓN
        if valores and incluir_analisis:
            try:
                # 🟢 Preparamos el diccionario de configuración
                config_analisis = {
                    'temp_min': temp_min,
                    'temp_max': temp_max,
                    'hum_min': hum_min,
                    'hum_max': hum_max
                }
                
                # 🟢 Pasamos la configuración a la función
                valores = aplicar_analisis_historico(valores, config=config_analisis)
                
            except Exception as analysis_error:
                print(f"Advertencia: Falló el análisis histórico: {analysis_error}")

        return valores or []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error histórico: {str(e)}")
    
    
    
# @router.get("/valores/historico-campo/{campo_id}", response_model=List[ValorGrafico])
# async def get_valores_historicos(
#     campo_id: int,
#     fecha_inicio: Optional[datetime] = Query(None),
#     fecha_fin: Optional[datetime] = Query(None),
#     metodo_carga: str = Query("optimizado"), 
#     incluir_analisis: bool = Query(False), 
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         if not fecha_fin: fecha_fin = datetime.now()
#         if not fecha_inicio: fecha_inicio = fecha_fin - timedelta(days=7)

#         # 1. Obtener datos de DB (Recuerda que ya corregimos la SQL aquí para traer el nombre)
#         valores = await obtener_historico_campo_db(campo_id, fecha_inicio, fecha_fin, metodo_carga)
        
#         # 2. Aplicar Análisis HISTÓRICO
#         if valores and incluir_analisis:
#             try:
#                 # 🟢 CAMBIO: Usamos la función especializada para históricos
#                 valores = aplicar_analisis_historico(valores)
#             except Exception as analysis_error:
#                 print(f"Advertencia: Falló el análisis histórico: {analysis_error}")

#         return valores or []
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error histórico: {str(e)}")

# @router.get("/valores/historico-campo/{campo_id}", response_model=List[ValorGrafico])
# async def get_valores_historicos(
#     campo_id: int,
#     fecha_inicio: Optional[datetime] = Query(None),
#     fecha_fin: Optional[datetime] = Query(None),
#     metodo_carga: str = Query("optimizado"), 
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         if not fecha_fin: fecha_fin = datetime.now()
#         if not fecha_inicio: fecha_inicio = fecha_fin - timedelta(days=7)

#         # 1. Obtener datos crudos/agregados de la DB
#         valores = await obtener_historico_campo_db(campo_id, fecha_inicio, fecha_fin, metodo_carga)
        
 
#         if valores:
#             valores = aplicar_analisis_anomalias(valores)

#         return valores or []
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error histórico: {str(e)}")

# ----------------------------------------------------------------------
# 3. ÚLTIMO VALOR (TIEMPO REAL)
# ----------------------------------------------------------------------
@router.get("/valores/ultimo/{campo_id}", response_model=ValorGrafico)
async def get_ultimo_valor(
    campo_id: int,
    # 🚨 Default True: También por defecto encendido para el polling
    analisis_activo: bool = Query(True), 
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        valor = await obtener_ultimo_valor_db(campo_id)
        if not valor:
            raise HTTPException(status_code=404, detail="Sin datos.")
            
        # Solo analizamos si el switch está activo en el frontend
        if analisis_activo:
            es_anomalia, mensaje = await detectar_anomalia_individual(campo_id, float(valor['valor']))
            valor['anomalia'] = es_anomalia
            valor['mensaje_alerta'] = mensaje
        else:
            # Limpiamos flags por seguridad
            valor['anomalia'] = False
            valor['mensaje_alerta'] = None
            
        return valor
    except HTTPException: raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------
# 4. METADATOS
# ----------------------------------------------------------------------
@router.get("/valores/rango-fechas-dispositivo/{dispositivo_id}")
async def get_rango_fechas(
    dispositivo_id: int,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await obtener_rango_fechas_db(dispositivo_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))