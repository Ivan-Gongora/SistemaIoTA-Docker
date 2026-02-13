import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import logging
from app.servicios.energetico.analizador_historico import AnalizadorHistorico
from app.servicios.energetico.predictor_consumo import PredictorConsumo

logger = logging.getLogger(__name__)

class RecomendadorOptimizacion:
    def __init__(self):
        self.analizador = AnalizadorHistorico()
        self.predictor = PredictorConsumo()
    
    async def generar_recomendaciones_completas(self) -> Dict[str, Any]:
        """Generar recomendaciones completas basadas en análisis de datos"""
        try:
            if not self.analizador._datos_cargados():
                return {"error": "No hay datos disponibles para análisis"}
            
            df = self.analizador.df
            
            # Obtener proyección para contexto futuro
            proyeccion = await self.predictor.predecir_tendencia_lineal(df, 6)
            
            # Generar diferentes tipos de recomendaciones
            recomendaciones = {
                "recomendaciones_eficiencia": await self._recomendaciones_eficiencia(df),
                "recomendaciones_costos": await self._recomendaciones_costos(df),
                "recomendaciones_operativas": await self._recomendaciones_operativas(df),
                "recomendaciones_inversion": await self._recomendaciones_inversion(df, proyeccion),
                "alertas_urgentes": await self._alertas_urgentes(df)
            }
            
            # Calcular ahorro potencial total
            ahorro_potencial = self._calcular_ahorro_potencial(recomendaciones)
            
            return {
                "recomendaciones": recomendaciones,
                "resumen": {
                    "total_recomendaciones": sum(len(rec) for rec in recomendaciones.values()),
                    "ahorro_potencial_anual_mxn": ahorro_potencial,
                    "impacto_estimado": self._evaluar_impacto(recomendaciones),
                    "prioridad_global": self._calcular_prioridad_global(recomendaciones)
                },
                "contexto_analitico": await self._generar_contexto_analitico(df, proyeccion)
            }
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {str(e)}")
            return {"error": f"Error generando recomendaciones: {str(e)}"}
    
    async def _recomendaciones_eficiencia(self, df: pd.DataFrame) -> List[Dict]:
        """Recomendaciones específicas para mejorar eficiencia energética"""
        recomendaciones = []
        
        # Análisis de factor de potencia
        if 'factor_potencia' in df.columns:
            fp_promedio = df['factor_potencia'].mean()
            if fp_promedio < 90:
                recomendaciones.append({
                    "categoria": "Eficiencia",
                    "titulo": "Mejorar Factor de Potencia",
                    "descripcion": f"Tu factor de potencia promedio es {fp_promedio:.1f}%. Ideal es >90% para evitar penalizaciones.",
                    "accion": "Instalar bancos de capacitores",
                    "beneficio": "Reducción de penalizaciones por factor de potencia (∼5-10% del costo)",
                    "ahorro_estimado_mxn": 5000,  # Estimado conservador
                    "prioridad": "ALTA" if fp_promedio < 85 else "MEDIA",
                    "dificultad_implementacion": "MEDIA"
                })
        
        # Análisis de consumo en horario punta
        if 'kwh_punta' in df.columns:
            porcentaje_punta = (df['kwh_punta'].sum() / df['consumo_total_kwh'].sum()) * 100
            if porcentaje_punta > 20:
                recomendaciones.append({
                    "categoria": "Operacional",
                    "titulo": "Reducir Consumo en Horario Punta",
                    "descripcion": f"El {porcentaje_punta:.1f}% de tu consumo ocurre en horario punta (tarifa más cara).",
                    "accion": "Reorganizar procesos intensivos a horario intermedio",
                    "beneficio": "Reducción de costos por menor tarifa punta",
                    "ahorro_estimado_mxn": 15000,
                    "prioridad": "MEDIA",
                    "dificultad_implementacion": "BAJA"
                })
        
        # Recomendación basada en crecimiento acelerado
        crecimiento_mensual = 1895.62  # Del modelo lineal
        if crecimiento_mensual > 1000:
            recomendaciones.append({
                "categoria": "Crecimiento",
                "titulo": "Auditoría Energética",
                "descripcion": f"Crecimiento mensual de {crecimiento_mensual:.0f} kWh. Recomendable identificar causas.",
                "accion": "Realizar auditoría energética profesional",
                "beneficio": "Identificar oportunidades de optimización no evidentes",
                "ahorro_estimado_mxn": 25000,
                "prioridad": "MEDIA",
                "dificultad_implementacion": "MEDIA"
            })
        
        return recomendaciones
    
    async def _recomendaciones_costos(self, df: pd.DataFrame) -> List[Dict]:
        """Recomendaciones para optimización de costos"""
        recomendaciones = []
        
        # Análisis de costo por kWh
        costo_por_kwh = df['costo_total'].sum() / df['consumo_total_kwh'].sum()
        
        if costo_por_kwh > 2.8:
            recomendaciones.append({
                "categoria": "Costos",
                "titulo": "Revisar Tarifa Eléctrica",
                "descripcion": f"Costo promedio de ${costo_por_kwh:.3f}/kWh. Evaluar cambio a tarifa más eficiente.",
                "accion": "Consultar con CFE sobre tarifas GDMTO o alternativas",
                "beneficio": "Posible reducción de 5-15% en costo por kWh",
                "ahorro_estimado_mxn": 30000,
                "prioridad": "ALTA",
                "dificultad_implementacion": "MEDIA"
            })
        
        # Análisis de estacionalidad de costos
        costo_max = df['costo_total'].max()
        costo_min = df['costo_total'].min()
        variacion_costo = ((costo_max - costo_min) / costo_min) * 100
        
        if variacion_costo > 50:
            recomendaciones.append({
                "categoria": "Planificación",
                "titulo": "Presupuesto Flexible para Energía",
                "descripcion": f"Variación del {variacion_costo:.1f}% en costos mensuales. Necesita presupuesto adaptable.",
                "accion": "Implementar presupuesto variable basado en estacionalidad",
                "beneficio": "Mejor planeación financiera y evitar déficit",
                "ahorro_estimado_mxn": 20000,
                "prioridad": "MEDIA",
                "dificultad_implementacion": "BAJA"
            })
        
        return recomendaciones
    
    async def _recomendaciones_operativas(self, df: pd.DataFrame) -> List[Dict]:
        """Recomendaciones operativas basadas en patrones de consumo"""
        recomendaciones = []
        
        # Análisis de relación demanda-consumo
        correlacion = df['demanda_maxima_kw'].corr(df['consumo_total_kwh'])
        
        if correlacion > 0.9:
            recomendaciones.append({
                "categoria": "Operacional",
                "titulo": "Optimizar Gestión de Demanda",
                "descripcion": "Alta correlación entre demanda máxima y consumo total. Oportunidad de optimización.",
                "accion": "Implementar sistema de gestión de demanda (DMS)",
                "beneficio": "Reducción de picos de demanda y costos asociados",
                "ahorro_estimado_mxn": 18000,
                "prioridad": "MEDIA",
                "dificultad_implementacion": "ALTA"
            })
        
        # Detección de meses problemáticos
        costo_por_kwh_mensual = df.groupby(df['periodo'].dt.month)['costo_total'].sum() / df.groupby(df['periodo'].dt.month)['consumo_total_kwh'].sum()
        mes_mas_caro = costo_por_kwh_mensual.idxmax()
        
        recomendaciones.append({
            "categoria": "Operacional",
            "titulo": "Atención Especial en Meses Críticos",
            "descripcion": f"El mes {mes_mas_caro} presenta los costos más altos por kWh.",
            "accion": "Implementar medidas especiales de eficiencia en ese período",
            "beneficio": "Mitigación de costos estacionales altos",
            "ahorro_estimado_mxn": 12000,
            "prioridad": "MEDIA",
            "dificultad_implementacion": "BAJA"
        })
        
        return recomendaciones
    
    async def _recomendaciones_inversion(self, df: pd.DataFrame, proyeccion: Dict) -> List[Dict]:
        """Recomendaciones de inversión a mediano/largo plazo"""
        recomendaciones = []
        
        # Basado en la proyección de crecimiento
        if 'predicciones' in proyeccion:
            crecimiento_anual = ((proyeccion['predicciones'][-1]['consumo_predicho_kwh'] - df['consumo_total_kwh'].iloc[-1]) / df['consumo_total_kwh'].iloc[-1]) * 100
            
            if crecimiento_anual > 30:
                recomendaciones.append({
                    "categoria": "Inversión",
                    "titulo": "Evaluar Energías Renovables",
                    "descripcion": f"Crecimiento proyectado del {crecimiento_anual:.1f}% anual. Evaluar paneles solares.",
                    "accion": "Estudio de viabilidad para sistema fotovoltaico",
                    "beneficio": "Reducción de costos a largo plazo y sostenibilidad",
                    "inversion_estimada_mxn": 500000,
                    "payback_estimado_anos": 3.5,
                    "prioridad": "MEDIA",
                    "dificultad_implementacion": "ALTA"
                })
        
        return recomendaciones
    
    async def _alertas_urgentes(self, df: pd.DataFrame) -> List[Dict]:
        """Alertas que requieren atención inmediata"""
        alertas = []
        
        # Alerta por crecimiento acelerado
        if len(df) >= 3:
            ultimos_3 = df.tail(3)
            crecimiento_reciente = ((ultimos_3['consumo_total_kwh'].iloc[-1] - ultimos_3['consumo_total_kwh'].iloc[0]) / ultimos_3['consumo_total_kwh'].iloc[0]) * 100
            
            if crecimiento_reciente > 40:
                alertas.append({
                    "tipo": "ALERTA",
                    "titulo": "Crecimiento Acelerado Detectado",
                    "descripcion": f"Crecimiento del {crecimiento_reciente:.1f}% en los últimos 3 meses.",
                    "accion_inmediata": "Investigar causas del aumento repentino",
                    "impacto": "ALTO",
                    "urgencia": "INMEDIATA"
                })
        
        return alertas
    
    def _calcular_ahorro_potencial(self, recomendaciones: Dict) -> float:
        """Calcular ahorro potencial total de todas las recomendaciones"""
        ahorro_total = 0
        for categoria, recs in recomendaciones.items():
            for rec in recs:
                if 'ahorro_estimado_mxn' in rec:
                    ahorro_total += rec['ahorro_estimado_mxn']
        return round(ahorro_total, 2)
    
    def _evaluar_impacto(self, recomendaciones: Dict) -> str:
        """Evaluar impacto general de las recomendaciones"""
        total_rec = sum(len(rec) for rec in recomendaciones.values())
        if total_rec >= 8:
            return "ALTO"
        elif total_rec >= 4:
            return "MEDIO"
        else:
            return "BAJO"
    
    def _calcular_prioridad_global(self, recomendaciones: Dict) -> str:
        """Calcular prioridad global basada en recomendaciones de alta prioridad"""
        alta_prioridad = 0
        for recs in recomendaciones.values():
            for rec in recs:
                if rec.get('prioridad') == 'ALTA':
                    alta_prioridad += 1
        
        if alta_prioridad >= 3:
            return "ALTA"
        elif alta_prioridad >= 1:
            return "MEDIA"
        else:
            return "BAJA"
    
    async def _generar_contexto_analitico(self, df: pd.DataFrame, proyeccion: Dict) -> Dict:
        """Generar contexto analítico para las recomendaciones"""
        return {
            "consumo_promedio_mensual": round(df['consumo_total_kwh'].mean(), 2),
            "costo_promedio_mensual": round(df['costo_total'].mean(), 2),
            "crecimiento_anual_historico": round(((df['consumo_total_kwh'].iloc[-1] - df['consumo_total_kwh'].iloc[0]) / df['consumo_total_kwh'].iloc[0] * 100), 2),
            "proyeccion_crecimiento_6_meses": proyeccion.get('metricas_modelo', {}).get('cambio_porcentual', 0),
            "meses_analizados": len(df)
        }