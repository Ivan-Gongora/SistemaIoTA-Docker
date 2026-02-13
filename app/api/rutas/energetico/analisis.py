from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, List, Optional
import pandas as pd

from app.servicios.energetico.analizador_historico import AnalizadorHistorico
from app.servicios.energetico.dependencias import get_analizador
from app.api.modelos.energetico.energetico import AnalisisPayload # 🎯 Importar el modelo

router = APIRouter(prefix="/energetico", tags=["Simulador Energético - Análisis"])

# --- ENDPOINT 1: Análisis Histórico (Básico) ---
@router.post("/analisis/historico") # 🎯 CAMBIADO A POST
async def analisis_historico(
    payload: AnalisisPayload = Body(...), # 🎯 Recibe los lotes en el cuerpo
    analizador: AnalizadorHistorico = Depends(get_analizador)
):
    """
    Endpoint básico para análisis descriptivo del histórico para lotes específicos.
    """
    try:
        if not analizador._datos_cargados():
            raise HTTPException(status_code=503, detail="Datos históricos no disponibles o no pudieron cargarse.")
        
        # 🎯 FILTRADO: Obtener el DataFrame filtrado por los lotes seleccionados
        df_filtrado = analizador.get_filtered_df_by_lotes(payload.lotes_seleccionados)

        if df_filtrado.empty:
            raise HTTPException(status_code=404, detail="No se encontraron datos para los lotes seleccionados.")

        # 🎯 Pasar el DataFrame filtrado al método de análisis
        resultado = await analizador.obtener_analisis_basico(df_para_analizar=df_filtrado)
        
        # Añadir lotes a la respuesta para confirmación
        resultado["lotes_analizados"] = payload.lotes_seleccionados if payload.lotes_seleccionados else ["Todos"]
        
        return {
            "status": "success",
            "data": resultado,
            "message": "Análisis histórico generado correctamente"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis histórico: {str(e)}")


# --- ENDPOINT 2: Estadísticas Detalladas ---
@router.post("/analisis/estadisticas")
async def estadisticas_detalladas(
    payload: AnalisisPayload = Body(...), # Recibe los lotes en el cuerpo
    analizador: AnalizadorHistorico = Depends(get_analizador)
):
    """Estadísticas detalladas (anuales, mensuales, correlaciones) para lotes específicos."""
    try:
        if not analizador._datos_cargados():
            raise HTTPException(status_code=503, detail="Datos históricos no disponibles.")
        
        # FILTRADO: Obtener el DataFrame filtrado por los lotes seleccionados
        df_filtrado = analizador.get_filtered_df_by_lotes(payload.lotes_seleccionados)
        
        if df_filtrado.empty:
            raise HTTPException(status_code=404, detail="No se encontraron datos para los lotes seleccionados.")

        # Pasar el DataFrame filtrado al método de análisis
        resultado = await analizador.obtener_estadisticas_detalladas(df_para_analizar=df_filtrado)
        
        resultado["lotes_analizados"] = payload.lotes_seleccionados if payload.lotes_seleccionados else ["Todos"]

        return {
            "status": "success", 
            "data": resultado,
            "message": "Estadísticas calculadas correctamente"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculando estadísticas: {str(e)}")


# --- ENDPOINT 3: Muestra de Datos )---
@router.post("/datos/muestra") #  CAMBIADO A POST
async def obtener_muestra_datos(
    payload: AnalisisPayload = Body(...), # Recibe los lotes en el cuerpo
    limite: int = 12, 
    analizador: AnalizadorHistorico = Depends(get_analizador)
):
    """Obtener una muestra de los datos para lotes específicos."""
    try:
        if not analizador._datos_cargados():
            raise HTTPException(status_code=503, detail="Datos históricos no disponibles.")
        
        # Obtener el DataFrame filtrado por los lotes seleccionados
        df_filtrado = analizador.get_filtered_df_by_lotes(payload.lotes_seleccionados)
        
        if df_filtrado.empty:
             raise HTTPException(status_code=404, detail="No se encontraron datos para los lotes seleccionados.")
        
        #  Obtener muestra del DataFrame filtrado
        resultado = await analizador.obtener_muestra_datos(limite, df_para_analizar=df_filtrado)
        
        return {
            "status": "success",
            "data": resultado,
            "message": f"Muestra de {len(resultado)} registros obtenida correctamente",
            "lotes_analizados": payload.lotes_seleccionados if payload.lotes_seleccionados else ["Todos"]
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo muestra: {str(e)}")