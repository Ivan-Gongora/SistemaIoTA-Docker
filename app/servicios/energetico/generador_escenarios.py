import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from app.servicios.energetico.analizador_historico import AnalizadorHistorico
from app.servicios.energetico.predictor_consumo import PredictorConsumo
from app.api.modelos.energetico.energetico import EscenarioPayload 

logger = logging.getLogger(__name__)

class GeneradorEscenarios:
    """
    Coordina al Analizador y al Predictor para generar proyecciones de escenarios.
    Aplica las tasas de crecimiento, inflación y eficiencia sobre los datos filtrados.
    """
    
    def __init__(self, analizador: AnalizadorHistorico, predictor: PredictorConsumo):
        self.analizador = analizador
        self.predictor = predictor
        logger.debug("GeneradorEscenarios inicializado.")

    async def _obtener_df_filtrado(self, lotes_seleccionados: Optional[List[str]]) -> pd.DataFrame:
        """
        Obtiene el DataFrame filtrado por los lotes seleccionados desde el AnalizadorHistorico.
        Utiliza el método get_filtered_df_by_lotes del analizador.
        """
        if self.analizador.df_completo.empty:
            logger.warning("AnalizadorHistorico no contiene datos maestros. No se puede filtrar.")
            return pd.DataFrame()
        
        # 🎯 Llama a la función de filtrado ya existente
        df_filtrado = self.analizador.get_filtered_df_by_lotes(lotes_seleccionados)
        
        if df_filtrado.empty:
            logger.warning(f"No se encontraron datos para los lotes seleccionados: {lotes_seleccionados}")
            return pd.DataFrame()
        
        return df_filtrado

    def _get_base_costo_kwh(self, df_filtrado_lotes: pd.DataFrame) -> float:
        """
        Obtiene el costo_por_kwh promedio de los últimos 12 meses del DataFrame filtrado.
        """
        if df_filtrado_lotes.empty:
            logger.warning("DataFrame vacío al calcular costo base por kWh. Usando 0.")
            return 0.0

        df_reciente = df_filtrado_lotes.tail(12)
        
        if 'consumo_total_kwh' in df_reciente.columns and 'costo_total' in df_reciente.columns and df_reciente['consumo_total_kwh'].sum() > 0:
            # Calcula la relación promedio (Total Costo / Total Consumo) en el periodo
            relacion_promedio = (df_reciente['costo_total'] / df_reciente['consumo_total_kwh']).replace([np.inf, -np.inf], np.nan).dropna().mean()
            return float(relacion_promedio) if not pd.isna(relacion_promedio) else 0.0
        
        logger.warning("No se pudo calcular el costo base por kWh, usando 0.")
        return 0.0

    async def simular_escenario_personalizado(self, payload: EscenarioPayload) -> Dict[str, Any]:
        """
        Ejecuta todo el flujo de simulación: filtrado, entrenamiento, predicción, y aplicación de escenario.
        """
        try:
            # 1. Obtener el DataFrame histórico (filtrado por lotes)
            df_historico_filtrado = await self._obtener_df_filtrado(payload.lotes_seleccionados)

            if df_historico_filtrado.empty:
                logger.error("GeneradorEscenarios: No hay datos históricos válidos para la simulación.")
                return {"error": "No hay datos históricos válidos para la simulación con los lotes especificados."}
            
            # 🚨 NUEVO: Convertir los datos históricos usados a formato JSON para el frontend
            # Usamos 'records' para obtener una lista de diccionarios (ideal para Vue/JS)
            datos_historicos_json = df_historico_filtrado.to_dict('records')
            
            # 2. Entrenar el predictor con el DataFrame filtrado
            entrenamiento_result = await self.predictor.train(df_historico_filtrado)
            
            if "error" in entrenamiento_result:
                logger.error(f"GeneradorEscenarios: El predictor falló al entrenar. Detalle: {entrenamiento_result['error']}")
                return {"error": f"El modelo predictivo no está listo o falló al entrenar: {entrenamiento_result['error']}"}

            if not self.predictor._is_trained():
                    logger.error("GeneradorEscenarios: El modelo predictor no se entrenó exitosamente.")
                    return {"error": "El modelo predictivo no está listo o falló al entrenar."}

            # 3. Predecir consumo futuro base
            predicciones_consumo_base = await self.predictor.predecir_consumo_kwh(payload.meses_a_predecir)

            if 'error' in predicciones_consumo_base:
                logger.error(f"GeneradorEscenarios: Error al generar predicciones de consumo base: {predicciones_consumo_base['error']}")
                return {"error": f"Error al generar predicciones de consumo base: {predicciones_consumo_base['error']}"}

            # 4. Obtener costo base y predicción de costo
            costo_kwh_base = self._get_base_costo_kwh(df_historico_filtrado)
            
            predicciones_costo_base = await self.predictor.predecir_costo(df_historico_filtrado, payload.meses_a_predecir)
            
            if 'error' in predicciones_costo_base:
                logger.error(f"GeneradorEscenarios: Error al generar predicciones de costo base: {predicciones_costo_base['error']}")
                return {"error": f"Error al generar predicciones de costo base: {predicciones_costo_base['error']}"}
            
            relacion_promedio_kwh = predicciones_costo_base['relacion_promedio_consumo_costo']

            # 5. Aplicar el escenario
            resultados_escenario = []
            for i, pred_consumo in enumerate(predicciones_consumo_base['predicciones']):
                periodo = pred_consumo['periodo']
                consumo_base = pred_consumo['consumo_predicho_kwh']
                
                # Cálculo de factores acumulativos (años fraccionales)
                años_transcurridos_crecimiento = (i + 1) / 12
                
                # Crecimiento Acumulado
                crecimiento_acumulado = (1 + payload.tasa_crecimiento_consumo)**años_transcurridos_crecimiento
                consumo_despues_eficiencia = consumo_base * (1 - payload.mejora_eficiencia_consumo)
                consumo_escenario = consumo_despues_eficiencia * crecimiento_acumulado
                
                # Inflación Acumulada
                inflacion_acumulada = (1 + payload.tasa_inflacion_energetica)**años_transcurridos_crecimiento
                costo_por_kwh_escenario = relacion_promedio_kwh * inflacion_acumulada
                
                # Cálculo de Costos
                costo_base = predicciones_costo_base['predicciones_costo'][i]['costo_predicho_mxn'] # Costo Base (incluye inflación ya calculada por el predictor)
                costo_escenario = consumo_escenario * costo_por_kwh_escenario

                resultados_escenario.append({
                    "periodo": periodo,
                    "consumo_base_kwh": round(consumo_base, 2),
                    "consumo_escenario_kwh": round(max(0, consumo_escenario), 2),
                    "costo_base_mxn": round(costo_base, 2),
                    "costo_escenario_mxn": round(max(0, costo_escenario), 2),
                    "costo_por_kwh_base": round(relacion_promedio_kwh, 4),
                    "costo_por_kwh_escenario": round(costo_por_kwh_escenario, 4)
                })

            # 6. Calcular métricas resumidas para el escenario
            total_consumo_base = sum(r['consumo_base_kwh'] for r in resultados_escenario)
            total_consumo_escenario = sum(r['consumo_escenario_kwh'] for r in resultados_escenario)
            total_costo_base = sum(r['costo_base_mxn'] for r in resultados_escenario)
            total_costo_escenario = sum(r['costo_escenario_mxn'] for r in resultados_escenario)

            ahorro_consumo_kwh = total_consumo_base - total_consumo_escenario
            ahorro_costo_mxn = total_costo_base - total_costo_escenario
            
            porcentaje_ahorro_consumo = (ahorro_consumo_kwh / total_consumo_base * 100) if total_consumo_base > 0 else 0
            porcentaje_ahorro_costo = (ahorro_costo_mxn / total_costo_base * 100) if total_costo_base > 0 else 0

            # Obtener métricas del modelo (para la respuesta)
            metricas_modelo_base_result = await self.predictor.predecir_consumo_kwh(1)
            metricas_modelo_base = metricas_modelo_base_result.get('metricas_modelo', {})

            # --- Estructura de retorno para el frontend ---
            return {
                "resumen_simulacion": {
                    "total_meses_simulados": payload.meses_a_predecir,
                    "total_costo_base_mxn": round(total_costo_base, 2),
                    "total_costo_simulado_mxn": round(total_costo_escenario, 2),
                    "variacion_costo_total_mxn": round(ahorro_costo_mxn * -1, 2), # Ahorro positivo -> variación negativa
                    "porcentaje_variacion": round(porcentaje_ahorro_costo * -1, 2), # Ahorro positivo -> variación negativa
                    "parametros_escenario": {
                        "tasa_inflacion_energetica": payload.tasa_inflacion_energetica,
                        "tasa_crecimiento_consumo": payload.tasa_crecimiento_consumo,
                        "mejora_eficiencia_consumo": payload.mejora_eficiencia_consumo
                    },
                    "lotes_simulados": self.predictor.lotes_del_entrenamiento
                },
                "predicciones_escenario": resultados_escenario,
                # 👈 NUEVO CAMPO SOLICITADO
                "datos_historicos_usados": datos_historicos_json, 
            }

        except Exception as e:
            logger.error(f"Error generando escenario personalizado: {str(e)}", exc_info=True)
            return {"error": f"Error interno al generar el escenario: {str(e)}"}