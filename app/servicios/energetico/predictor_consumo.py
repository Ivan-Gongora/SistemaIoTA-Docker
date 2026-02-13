import pandas as pd
import numpy as np
from prophet import Prophet
from typing import Dict, Any, List, Optional
import logging
from sklearn.linear_model import LinearRegression 
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PredictorConsumo:
    """
    Clase para predecir el consumo energético (Prophet/Lineal).
    Opera sobre un DataFrame de datos filtrados pasado en el método train().
    """
    
    def __init__(self):
        self.modelo_prophet: Optional[Prophet] = None
        self.modelo_lineal: Optional[LinearRegression] = None
        self.std_error_lineal: float = 0.0
        
        # Estado interno del entrenamiento
        self.df_entrenado: Optional[pd.DataFrame] = None
        self.modelo_usado: str = "ninguno"
        self.rango_fechas_entrenamiento: Dict[str, str] = {}
        self.ultimo_valor_real: float = 0.0
        self.lotes_del_entrenamiento: Optional[List[str]] = None # Almacenará los lotes usados
        
        logger.debug("PredictorConsumo inicializado.")

    def _convertir_a_python(self, obj):
        """Convertir tipos de numpy a tipos nativos de Python para JSON."""
        if pd.isna(obj): return None
        elif isinstance(obj, (np.integer, np.int64)): return int(obj)
        elif isinstance(obj, (np.floating, np.float64)): return float(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, pd.Timestamp): return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, pd.Series): return obj.apply(self._convertir_a_python).tolist()
        else: return obj

    def _is_trained(self) -> bool:
        """Verifica si algún modelo fue entrenado exitosamente."""
        return self.modelo_prophet is not None or self.modelo_lineal is not None
    
    # ----------------------------------------------------
    # MÉTODOS DE ENTRENAMIENTO (PRIVADOS)
    # ----------------------------------------------------
    
    async def _train_prophet(self, df: pd.DataFrame) -> bool:
        """Lógica de entrenamiento de Prophet."""
        try:
            df_prophet = df[['periodo', 'consumo_total_kwh']].copy()
            df_prophet.columns = ['ds', 'y']
            df_prophet = df_prophet.sort_values('ds')
            
            if df_prophet.empty or len(df_prophet) < 2: 
                self.modelo_prophet = None
                return False

            self.modelo_prophet = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                                          daily_seasonality=False, changepoint_prior_scale=0.05,
                                          seasonality_prior_scale=10.0)
            if len(df_prophet['ds'].dt.to_period('M').unique()) > 1:
                self.modelo_prophet.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            
            self.modelo_prophet.fit(df_prophet)
            self.df_entrenado = df_prophet 
            self.ultimo_valor_real = float(self.df_entrenado['y'].iloc[-1])
            logger.info("Modelo Prophet entrenado exitosamente.")
            return True
        except Exception as e:
            logger.error(f"Error entrenando Prophet: {e}", exc_info=True)
            self.modelo_prophet = None
            return False

    async def _train_linear(self, df: pd.DataFrame) -> bool:
        """Lógica de entrenamiento de Regresión Lineal."""
        try:
            df_temp = df[['periodo', 'consumo_total_kwh']].copy()
            df_temp = df_temp.sort_values('periodo')
            
            if df_temp.empty or len(df_temp) < 2: 
                self.modelo_lineal = None
                self.std_error_lineal = 0.0
                return False

            df_temp['mes_num'] = range(len(df_temp))
            
            X = df_temp[['mes_num']].values
            y = df_temp['consumo_total_kwh'].values
            
            self.modelo_lineal = LinearRegression()
            self.modelo_lineal.fit(X, y)
            
            residuos = y - self.modelo_lineal.predict(X)
            self.std_error_lineal = residuos.std()
            
            self.df_entrenado = df_temp 
            self.ultimo_valor_real = float(y[-1])
            logger.info("Modelo Lineal entrenado exitosamente.")
            return True
        except Exception as e:
            logger.error(f"Error entrenando Regresión Lineal: {e}", exc_info=True)
            self.modelo_lineal = None
            self.std_error_lineal = 0.0
            return False

    async def train(self, df_historico: pd.DataFrame):
        """
        Método principal de entrenamiento. Decide qué modelo usar basado en el DF filtrado.
        """
        if not isinstance(df_historico, pd.DataFrame) or df_historico.empty:
            logger.error("No se proporcionaron datos válidos para el entrenamiento.")
            return {"error": "No se proporcionaron datos válidos para el entrenamiento."}

        # Reiniciar modelos y estado antes de cada entrenamiento
        self.modelo_prophet = None; self.modelo_lineal = None; self.std_error_lineal = 0.0
        self.df_entrenado = None; self.modelo_usado = "ninguno"; self.ultimo_valor_real = 0.0
        
        # Almacenar los lotes del DF actual
        if 'lote_nombre' in df_historico.columns and not df_historico['lote_nombre'].empty:
            self.lotes_del_entrenamiento = df_historico['lote_nombre'].unique().tolist()
            logger.info(f"Predictor entrenándose para lotes: {self.lotes_del_entrenamiento}")
        else:
            self.lotes_del_entrenamiento = ["N/A"]
            logger.warning("Columna 'lote_nombre' no encontrada en el DataFrame. Lotes no registrados.")


        self.rango_fechas_entrenamiento = {
            "inicio": df_historico['periodo'].min().strftime('%Y-%m-%d'),
            "fin": df_historico['periodo'].max().strftime('%Y-%m-%d')
        }

        # Decisión de modelo: Menos de 18 meses -> Usar Lineal
        if len(df_historico) < 18:
            logger.warning(f"Pocos datos ({len(df_historico)} registros). Usando Regresión Lineal.")
            exito = await self._train_linear(df_historico)
            if exito: self.modelo_usado = "tendencia_lineal"
        else:
            logger.info(f"Suficientes datos ({len(df_historico)} registros). Intentando Prophet.")
            exito_prophet = await self._train_prophet(df_historico)
            if exito_prophet:
                self.modelo_usado = "prophet"
            else:
                logger.warning("Prophet falló. Usando Regresión Lineal como fallback.")
                exito_lineal = await self._train_linear(df_historico)
                if exito_lineal:
                    self.modelo_usado = "tendencia_lineal_fallback"
                else:
                    logger.error("¡FALLO CRÍTICO! Ningún modelo pudo ser entrenado.")
                    self.modelo_usado = "fallido"
        
        if self.modelo_usado == "fallido":
            return {"error": "No se pudo entrenar ningún modelo con los datos proporcionados."}
        else:
            return {"status": "success", "modelo_entrenado": self.modelo_usado}

    # ----------------------------------------------------
    # MÉTODOS DE PREDICCIÓN (PÚBLICOS)
    # ----------------------------------------------------

    async def predecir_consumo_kwh(self, meses: int = 12) -> Dict[str, Any]:
        """
        Predice el consumo usando el modelo que se haya entrenado (Prophet o Lineal).
        """
        if not self._is_trained():
            logger.warning("Predicción de consumo: El modelo predictivo no está entrenado.")
            return {"error": "El modelo predictivo no está entrenado. Por favor, entrene primero."}

        predicciones_lista = []
        
        try:
            # Lógica para Prophet o Lineal (Consolidada)
            if self.modelo_usado == "prophet" and self.modelo_prophet and self.df_entrenado is not None:
                if not self.df_entrenado.empty:
                    futuro = self.modelo_prophet.make_future_dataframe(periods=meses, freq='MS', include_history=False)
                    forecast = self.modelo_prophet.predict(futuro)
                    for _, row in forecast.iterrows():
                        predicciones_lista.append({
                            'periodo': self._convertir_a_python(row['ds'].strftime('%Y-%m-%d')),
                            'consumo_predicho_kwh': self._convertir_a_python(max(0, round(row['yhat'], 2))),
                            'limite_inferior': self._convertir_a_python(max(0, round(row['yhat_lower'], 2))),
                            'limite_superior': self._convertir_a_python(max(0, round(row['yhat_upper'], 2))),
                            'tendencia': self._convertir_a_python(round(row['trend'], 2))
                        })
                else:
                    return {"error": "No hay datos de entrenamiento válidos para Prophet."}

            elif self.modelo_usado.startswith("tendencia_lineal") and self.modelo_lineal and self.df_entrenado is not None:
                if not self.df_entrenado.empty:
                    ultimo_mes_num = self.df_entrenado['mes_num'].max()
                    meses_futuros = np.array([[ultimo_mes_num + i + 1] for i in range(meses)])
                    predicciones = self.modelo_lineal.predict(meses_futuros)
                    fecha_base = self.df_entrenado['periodo'].max()
                    
                    for i, pred in enumerate(predicciones):
                        fecha_pred = fecha_base + pd.DateOffset(months=i + 1)
                        predicciones_lista.append({
                            'periodo': self._convertir_a_python(fecha_pred.strftime('%Y-%m-%d')),
                            'consumo_predicho_kwh': self._convertir_a_python(max(0, round(float(pred), 2))),
                            'limite_inferior': self._convertir_a_python(max(0, round(float(pred - 1.96 * self.std_error_lineal), 2))),
                            'limite_superior': self._convertir_a_python(max(0, round(float(pred + 1.96 * self.std_error_lineal), 2))),
                            'tendencia': self._convertir_a_python(round(float(pred), 2))
                        })
                else:
                    return {"error": "No hay datos de entrenamiento válidos para Regresión Lineal."}
            
            else:
                logger.error(f"El modelo está en un estado inconsistente o no se pudo predecir: {self.modelo_usado}")
                return {"error": "El modelo está en un estado inconsistente o no se pudo predecir."}

            # --- Métricas Comunes de Salida ---
            primera_prediccion = predicciones_lista[0]['consumo_predicho_kwh'] if predicciones_lista else 0
            
            return {
                "predicciones": predicciones_lista,
                "metricas_modelo": {
                    "modelo_usado": self.modelo_usado,
                    "registros_entrenamiento": self._convertir_a_python(len(self.df_entrenado)) if self.df_entrenado is not None else 0,
                    "rango_entrenamiento": self.rango_fechas_entrenamiento,
                    "ultimo_valor_real": self._convertir_a_python(self.ultimo_valor_real),
                    "primera_prediccion": self._convertir_a_python(primera_prediccion),
                    "cambio_porcentual": self._convertir_a_python(
                        round(((primera_prediccion - self.ultimo_valor_real) / self.ultimo_valor_real * 100), 2) if self.ultimo_valor_real > 0 else 0
                    ),
                    "horizonte_prediccion": self._convertir_a_python(meses),
                    "lotes_considerados": self.lotes_del_entrenamiento
                }
            }
            
        except Exception as e:
            logger.error(f"Error en predicción de consumo ({self.modelo_usado}): {str(e)}", exc_info=True)
            return {"error": f"Error en predicción de consumo: {str(e)}"}

    async def predecir_costo(self, df_historico: pd.DataFrame, meses: int = 12) -> Dict[str, Any]:
        """
        Predecir costos basado en la relación consumo-costo.
        DF Histórico se pasa para el cálculo del costo.
        """
        try:
            # Calcular relación histórica consumo-costo
            df_reciente = df_historico.tail(12)
            
            # Asegurarse de que las columnas existen y no hay división por cero
            if 'consumo_total_kwh' in df_reciente.columns and 'costo_total' in df_reciente.columns and \
               not df_reciente.empty and df_reciente['consumo_total_kwh'].sum() > 0:
                relacion_promedio = (df_reciente['costo_total'] / df_reciente['consumo_total_kwh']).replace([np.inf, -np.inf], np.nan).dropna().mean()
            else:
                relacion_promedio = 0.0
                logger.warning("No se pudo calcular la relación consumo-costo debido a datos inválidos (consumo cero o nulo) o DataFrame vacío.")

            if pd.isna(relacion_promedio):
                relacion_promedio = 0.0
            
            # Primero, entrenar el modelo de consumo con el df_historico actual
            required_train_cols = ['periodo', 'consumo_total_kwh', 'lote_nombre']
            missing_cols_train = [col for col in required_train_cols if col not in df_historico.columns]
            if missing_cols_train:
                error_msg = f"PredictorConsumo.predecir_costo: Faltan columnas requeridas en el DataFrame histórico para el entrenamiento: {missing_cols_train}."
                logger.error(error_msg)
                return {"error": error_msg}

            entrenamiento_result = await self.train(df_historico)
            if 'error' in entrenamiento_result:
                return entrenamiento_result

            # Luego, obtener las predicciones de consumo
            resultado_consumo = await self.predecir_consumo_kwh(meses)
            
            if 'error' in resultado_consumo:
                return resultado_consumo
            
            predicciones_costo = []
            for pred in resultado_consumo['predicciones']:
                costo_predicho = pred['consumo_predicho_kwh'] * relacion_promedio
                predicciones_costo.append({
                    "periodo": pred['periodo'],
                    "costo_predicho_mxn": self._convertir_a_python(round(costo_predicho, 2)),
                    "consumo_predicho_kwh": pred['consumo_predicho_kwh'],
                    "costo_por_kwh_predicho": self._convertir_a_python(round(relacion_promedio, 4))
                })
            
            return {
                "predicciones_costo": predicciones_costo,
                "relacion_promedio_consumo_costo": self._convertir_a_python(round(relacion_promedio, 4)),
                "basado_en_consumo_predicciones": True,
                "fuente_costo": "Promedio últimos 12 meses",
                "lotes_considerados": self.lotes_del_entrenamiento
            }
            
        except Exception as e:
            logger.error(f"Error prediciendo costos: {str(e)}", exc_info=True)
            return {"error": f"Error prediciendo costos: {str(e)}"}