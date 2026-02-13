from fastapi import APIRouter, HTTPException, Query,Body, Depends, logger
from typing import Dict, Any,List, Optional

from app.servicios.energetico.analizador_historico import AnalizadorHistorico
from app.servicios.energetico.predictor_consumo import PredictorConsumo
from app.servicios.energetico.generador_escenarios import GeneradorEscenarios

from app.api.modelos.energetico.energetico import EscenarioPayload

from app.servicios.energetico.dependencias import get_generador_escenarios
from app.servicios.energetico.dependencias import get_analizador
from app.servicios.auth_utils import get_current_user_id 
from app.db.crud.recibos_crud import get_nombres_lotes_by_user_id 
import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/energetico", tags=["Predicciones Energéticas"])

@router.get("/lotes_disponibles", 
            response_model=List[str], # El endpoint devolverá una lista de strings
            summary="Obtiene la lista de nombres de lotes de recibos disponibles para el usuario actual")
async def obtener_lotes_disponibles(
    user_id: int = Depends(get_current_user_id)
):
    """
    Retorna una lista con los nombres únicos de los lotes de recibos de energía
    que el usuario actual ha cargado o tiene asociados en el sistema.
    """
    logger.info(f"[{user_id}] Solicitud para obtener lotes disponibles.")
    try:
        nombres_lotes = get_nombres_lotes_by_user_id(user_id)
        if not nombres_lotes:
            logger.warning(f"[{user_id}] No se encontraron lotes para el usuario.")
            return [] # Devuelve una lista vacía si no hay lotes
        
        logger.info(f"[{user_id}] Lotes encontrados: {nombres_lotes}")
        return nombres_lotes
    except Exception as e:
        logger.error(f"[{user_id}] Error al obtener lotes disponibles: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al obtener lotes disponibles: {str(e)}")

@router.post("/simular/escenario_personalizado",
             response_model=Dict[str, Any],
             summary="Ejecuta simulación de costos y consumo futuro con lotes seleccionados")
async def simular_escenario_con_lotes_o_todos(
    payload: EscenarioPayload = Body(..., description="Parámetros de inflación, crecimiento y eficiencia, incluyendo lotes y horizonte"),
    generador_escenarios: GeneradorEscenarios = Depends(get_generador_escenarios), # ✅ Correcto, ahora se importa desde dependencias
    user_id: int = Depends(get_current_user_id) 
):
    """
    Ejecuta una simulación personalizada aplicando tasas de crecimiento, eficiencia e inflación,
    utilizando los datos históricos de los lotes energéticos especificados.
    """
    logger.info(f"[{user_id}] Solicitud de simulación con {payload.meses_a_predecir} meses y lotes: {payload.lotes_seleccionados}")

    if not payload.lotes_seleccionados:
        raise HTTPException(status_code=400, detail="Debes seleccionar al menos un lote de datos para la simulación.")

    try:
        resultados = await generador_escenarios.simular_escenario_personalizado(payload)
        
        if 'error' in resultados:
            logger.error(f"[{user_id}] Error en simulación (servicio): {resultados['error']}")
            raise HTTPException(status_code=500, detail=resultados['error'])

        return {
            "status": "success",
            "data": resultados,
            "message": "Simulación de escenario generada correctamente"
        }
        
    except HTTPException as e:
        logger.error(f"[{user_id}] HTTPException en simular_escenario: {e.detail}")
        raise e
    except Exception as e:
        import traceback
        logger.error(f"[{user_id}] Error inesperado en el endpoint simular_escenario: {traceback.format_exc()}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fatal en la simulación: {str(e)}")





@router.get("/optimizacion/recomendaciones")
async def obtener_recomendaciones_optimizacion():
    """Obtener recomendaciones de optimización energética personalizadas"""
    try:
        from servicios.energetico.recomendador_optimizacion import RecomendadorOptimizacion
        
        recomendador = RecomendadorOptimizacion()
        resultado = await recomendador.generar_recomendaciones_completas()
        
        return {
            "status": "success",
            "data": resultado,
            "message": "Recomendaciones de optimización generadas correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando recomendaciones: {str(e)}")

@router.get("/proyecciones/mejorada")
async def proyeccion_mejorada(
    meses: int = Query(6, description="Meses a predecir", ge=1, le=24),
    analizador: AnalizadorHistorico = Depends(get_analizador) # 3. Inyectar el analizador
):
    """Proyección mejorada que usa el mejor modelo disponible"""
    try:
        # analizador = AnalizadorHistorico() # 4. Eliminar
        if not analizador._datos_cargados():
            raise HTTPException(status_code=400, detail="No hay datos históricos disponibles")
               
        predictor = PredictorConsumo()
        
        # Si tenemos pocos datos, usar tendencia lineal (más preciso)
        if len(analizador.df) < 18:  # Menos de 1.5 años
            resultado = await predictor.predecir_tendencia_lineal(analizador.df, meses)
            modelo_usado = "tendencia_lineal"
        else:
            # Si tenemos suficientes datos, usar Prophet
            entrenado = await predictor.entrenar_modelo_prophet(analizador.df)
            if entrenado:
                resultado = await predictor.predecir_consumo(meses)
                modelo_usado = "prophet"
            else:
                resultado = await predictor.predecir_tendencia_lineal(analizador.df, meses)
                modelo_usado = "tendencia_lineal_fallback"
        
        # Añadir información del modelo usado
        if 'error' not in resultado:
            resultado['modelo_usado'] = modelo_usado
        
        return {
            "status": "success",
            "data": resultado,
            "message": f"Proyección mejorada ({modelo_usado}) para {meses} meses generada correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en proyección mejorada: {str(e)}")
    
@router.get("/proyecciones/consumo")
async def proyeccion_consumo(
    meses: int = Query(12, description="Meses a predecir", ge=1, le=36),
    analizador: AnalizadorHistorico = Depends(get_analizador) # 3. Inyectar
):
    """Proyección de consumo energético para los próximos meses"""
    try:
        # analizador = AnalizadorHistorico() # 4. Eliminar
        if not analizador._datos_cargados():
            raise HTTPException(status_code=400, detail="No hay datos históricos disponibles")        
        # Entrenar modelo y predecir
        predictor = PredictorConsumo()
        entrenado = await predictor.entrenar_modelo_prophet(analizador.df)
        
        if not entrenado:
            raise HTTPException(status_code=500, detail="Error entrenando modelo predictivo")
        
        resultado = await predictor.predecir_consumo(meses)
        
        return {
            "status": "success",
            "data": resultado,
            "message": f"Proyección de consumo para {meses} meses generada correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en proyección: {str(e)}")

@router.get("/proyecciones/costo")
async def proyeccion_costo(
    meses: int = Query(12, description="Meses a predecir", ge=1, le=36),
    analizador: AnalizadorHistorico = Depends(get_analizador) # 3. Inyectar
):
    """Proyección de costos energéticos para los próximos meses"""
    try:
        # analizador = AnalizadorHistorico() # 4. Eliminar
        if not analizador._datos_cargados():
            raise HTTPException(status_code=400, detail="No hay datos históricos disponibles")      
        # Entrenar modelo y predecir costos
        predictor = PredictorConsumo()
        entrenado = await predictor.entrenar_modelo_prophet(analizador.df)
        
        if not entrenado:
            raise HTTPException(status_code=500, detail="Error entrenando modelo predictivo")
        
        resultado = await predictor.predecir_costo(analizador.df, meses)
        
        return {
            "status": "success",
            "data": resultado,
            "message": f"Proyección de costos para {meses} meses generada correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en proyección de costos: {str(e)}")

@router.get("/proyecciones/completa")
async def proyeccion_completa(
    meses: int = Query(12, description="Meses a predecir", ge=1, le=36),
    analizador: AnalizadorHistorico = Depends(get_analizador) # 3. Inyectar
):
    """Proyección completa (consumo + costo) para los próximos meses"""
    try:
        # analizador = AnalizadorHistorico() # 4. Eliminar
        if not analizador._datos_cargados():
            raise HTTPException(status_code=400, detail="No hay datos históricos disponibles")        
        predictor = PredictorConsumo()
        entrenado = await predictor.entrenar_modelo_prophet(analizador.df)
        
        if not entrenado:
            raise HTTPException(status_code=500, detail="Error entrenando modelo predictivo")
        
        # Obtener ambas proyecciones
        consumo_result = await predictor.predecir_consumo(meses)
        costo_result = await predictor.predecir_costo(analizador.df, meses)
        
        return {
            "status": "success",
            "data": {
                "proyeccion_consumo": consumo_result,
                "proyeccion_costo": costo_result,
                "resumen": {
                    "meses_predichos": meses,
                    "ultimo_periodo_historico": analizador.df['periodo'].max().strftime('%Y-%m-%d'),
                    "total_registros_entrenamiento": len(analizador.df)
                }
            },
            "message": f"Proyección completa para {meses} meses generada correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en proyección completa: {str(e)}")


### IA ANALYSIS ENDPOINT ###


@router.get("/ia/analisis-automatico")
async def analisis_automatico_ia(analizador: AnalizadorHistorico = Depends(get_analizador)):
    """Análisis automático con OpenRouter (múltiples modelos gratis)"""
    try:
        from app.servicios.ia.openrouter_client import OpenRouterClient
        from app.servicios.energetico.analizador_historico import AnalizadorHistorico
        
        # analizador = AnalizadorHistorico() # 4. Eliminar
        if not analizador._datos_cargados():
            raise HTTPException(status_code=400, detail="No hay datos disponibles")        
        # Preparar datos
        stats = await analizador.obtener_analisis_basico()
        estadisticas = stats.get("estadisticas_basicas", {})
        
        df_summary = f"""
        DATOS ENERGÉTICOS INSTITUCIONALES - TARIFA GDMTH:
        - Período: {estadisticas.get('rango_fechas', {}).get('inicio', '')} a {estadisticas.get('rango_fechas', {}).get('fin', '')}
        - Consumo promedio: {estadisticas.get('consumo_promedio_kwh', 0):,.0f} kWh/mes
        - Costo promedio: ${estadisticas.get('costo_promedio_mxn', 0):,.0f} MXN/mes
        - Demanda máxima: {estadisticas.get('demanda_maxima_promedio_kw', 0):,.0f} kW
        - Crecimiento anual: +55%
        - Factor potencia: {estadisticas.get('factor_potencia_promedio', 'N/A')}%
        """
        
        # 🔄 USAR OPENROTER CON MÚLTIPLES MODELOS GRATIS
        cliente_ia = OpenRouterClient()
        respuesta = await cliente_ia.analizar_datos_energeticos(df_summary)
        
        return {
            "status": "success",
            "data": {
                "analisis_automatico": respuesta,
                "resumen_datos": estadisticas,
                "fuente_analisis": "openrouter_multi_model",
                "modelos_disponibles": cliente_ia.obtener_modelos_disponibles()
            },
            "message": "Análisis automático generado correctamente"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis automático: {str(e)}")