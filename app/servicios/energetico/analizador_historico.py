import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalizadorHistorico:
    """
    Clase para analizar datos históricos de consumo energético.
    Actúa como un contenedor y procesador para el DataFrame (DF) maestro,
    recibido ya cargado desde la base de datos (DB), y provee métodos de filtrado.
    """
    
    COLUMNA_LOTE = 'lote_nombre'
    
    # Columnas críticas que deben existir para que los métodos de análisis funcionen
    REQUIRED_COLS = ['periodo', 'consumo_total_kwh', 'costo_total', 'demanda_maxima_kw', COLUMNA_LOTE]
    
    def __init__(self, df_completo: Optional[pd.DataFrame] = None):
        """
        Inicializa el Analizador. Recibe el DataFrame completo (DF maestro)
        cargado desde la base de datos.
        """
        self._df_completo: pd.DataFrame = df_completo if df_completo is not None else pd.DataFrame()

        # Solo preparar el DF si tiene datos para evitar errores en DF vacío
        if not self._df_completo.empty:
            self._preparar_df_inicial()
        else:
            logger.warning("AnalizadorHistorico inicializado con DataFrame vacío. No se puede analizar.")

    @property
    def df_completo(self) -> pd.DataFrame:
        """Propiedad para acceder al DataFrame completo sin filtrar (el DF maestro)."""
        return self._df_completo

    def _preparar_df_inicial(self):
        """
        Prepara el DataFrame cargado de la base de datos: convierte tipos, 
        calcula columnas derivadas (costo/kWh, mes, año) y limpia datos.
        """
        
        # 1. Validación de columnas críticas
        missing_cols = [col for col in self.REQUIRED_COLS if col not in self._df_completo.columns]
        if missing_cols:
            logger.error(f"Faltan columnas requeridas en el DataFrame: {missing_cols}")
            self._df_completo = pd.DataFrame()
            return
            
        # 2. Conversión y Limpieza
        self._df_completo['periodo'] = pd.to_datetime(self._df_completo['periodo'], errors='coerce')
        self._df_completo[self.COLUMNA_LOTE] = self._df_completo[self.COLUMNA_LOTE].astype(str).str.strip()
        self._df_completo.dropna(subset=['periodo'], inplace=True) 

        if self._df_completo.empty:
            logger.warning("DataFrame vacío después de limpiar fechas.")
            return

        # 3. Limpieza de datos y corrección de anómalos
        self._limpiar_datos(self._df_completo)
        
        # 4. Ordenar y Calcular Métricas Derivadas
        self._df_completo = self._df_completo.sort_values('periodo').reset_index(drop=True)
        
        # Cálculo de costo_por_kwh
        self._df_completo['costo_por_kwh'] = self._df_completo.apply(
            lambda row: (row['costo_total'] / row['consumo_total_kwh']) if row['consumo_total_kwh'] and row['consumo_total_kwh'] > 0 else 0,
            axis=1
        ).astype(float).replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Cálculo de mes y año
        self._df_completo['mes'] = self._df_completo['periodo'].dt.month
        self._df_completo['año'] = self._df_completo['periodo'].dt.year
        
        logger.info(f"DataFrame completo preparado: {len(self._df_completo)} registros.")

    def _limpiar_datos(self, df_target: pd.DataFrame):
        """
        Convierte columnas a numérico, aplica el llenado de NaNs y la lógica de corrección.
        """
        if df_target.empty:
            return

        # Conversión y llenado de NaNs a 0
        for col in ['consumo_total_kwh', 'costo_total', 'demanda_maxima_kw', 'factor_potencia', 'dias_facturados', 'kwh_punta']:
            if col in df_target.columns:
                df_target[col] = pd.to_numeric(df_target[col], errors='coerce').fillna(0)

        consumo_median = df_target['consumo_total_kwh'].median()
        if pd.isna(consumo_median) or consumo_median == 0:
            return
        
        logger.debug(f"Consumo mediano para limpieza: {consumo_median}")
        
        # Lógica de corrección de anómalos (Tu lógica original)
        condicion_correccion = (df_target['consumo_total_kwh'] < consumo_median * 0.2) & \
                               (df_target['consumo_total_kwh'] < 10000) & \
                               (df_target['consumo_total_kwh'] > 1000)
        
        if condicion_correccion.any():
            indices_a_corregir = df_target[condicion_correccion].index
            for idx in indices_a_corregir:
                consumo_original = df_target.loc[idx, 'consumo_total_kwh']
                correccion = consumo_original * 10
                logger.warning(f"⚠️ Posible error en {df_target.loc[idx, 'periodo'].strftime('%Y-%m-%d')} (lote: {df_target.loc[idx, self.COLUMNA_LOTE] if self.COLUMNA_LOTE in df_target.columns else 'N/A'}): Corrigiendo {consumo_original} a {correccion}")
                df_target.loc[idx, 'consumo_total_kwh'] = correccion
    
    def get_filtered_df_by_lotes(self, nombres_lotes: Optional[List[str]]) -> pd.DataFrame:
        """
        Filtra el DataFrame histórico completo por los nombres de lote dados.
        Si no se especifican lotes o la lista está vacía, retorna el DataFrame completo.
        """
        if self._df_completo.empty:
            return pd.DataFrame()

        if not nombres_lotes:
            # Si no hay lotes, devolvemos el DF completo
            return self._df_completo.copy()

        # Filtrar el DF maestro por los lotes especificados
        df_filtrado = self._df_completo[self._df_completo[self.COLUMNA_LOTE].isin(nombres_lotes)].copy()
        
        if df_filtrado.empty:
            logger.warning(f"No se encontraron datos después de filtrar para los lotes: {nombres_lotes}.")
        else:
            logger.debug(f"Filtrado exitoso para lotes {nombres_lotes}. Filas resultantes: {len(df_filtrado)}")

        return df_filtrado

    def _convertir_a_python(self, obj):
        """Convertir tipos de numpy a tipos nativos de Python para JSON."""
        if pd.isna(obj): return None
        elif isinstance(obj, (np.integer, np.int64)): return int(obj)
        elif isinstance(obj, (np.floating, np.float64)): return float(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        elif isinstance(obj, pd.Timestamp): return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, pd.Series): return obj.apply(self._convertir_a_python).tolist()
        else: return obj
    
    def _datos_cargados(self) -> bool:
        """Verificar si hay datos disponibles en el DataFrame completo."""
        return not self._df_completo.empty
    
    # -----------------------------------------------------------------
    # MÉTODOS DE CÁLCULO ESTADÍSTICO (Ahora operan sobre el DF completo o el DF inyectado)
    # -----------------------------------------------------------------
    
    async def obtener_analisis_basico(self, df_para_analizar: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Análisis descriptivo básico del histórico."""
        df_target = df_para_analizar if df_para_analizar is not None else self._df_completo

        if df_target.empty:
            logger.warning("Análisis básico: No hay datos disponibles para analizar.")
            return {"error": "No hay datos disponibles"}
        
        try:
            # Asegurar que las columnas existen antes de intentar acceder a ellas
            if not all(col in df_target.columns for col in ['consumo_total_kwh', 'costo_total', 'demanda_maxima_kw', 'periodo']):
                logger.error("Análisis básico: Faltan columnas críticas en el DataFrame.")
                return {"error": "Faltan columnas críticas para el análisis básico."}

            consumo_stats = {
                "total_registros": len(df_target),
                "rango_fechas": {
                    "inicio": df_target['periodo'].min().strftime('%Y-%m-%d') if not df_target['periodo'].empty else None,
                    "fin": df_target['periodo'].max().strftime('%Y-%m-%d') if not df_target['periodo'].empty else None
                },
                "consumo_promedio_kwh": float(round(df_target['consumo_total_kwh'].mean(), 2)),
                "consumo_max_kwh": float(round(df_target['consumo_total_kwh'].max(), 2)),
                "consumo_min_kwh": float(round(df_target['consumo_total_kwh'].min(), 2)),
                "costo_promedio_mxn": float(round(df_target['costo_total'].mean(), 2)),
                "costo_total_acumulado": float(round(df_target['costo_total'].sum(), 2)),
                "demanda_maxima_promedio_kw": float(round(df_target['demanda_maxima_kw'].mean(), 2)),
            }
            
            if 'factor_potencia' in df_target.columns:
                factor_potencia_mean = df_target['factor_potencia'].mean()
                if not pd.isna(factor_potencia_mean):
                    consumo_stats["factor_potencia_promedio"] = float(round(factor_potencia_mean, 2))
            
            tendencias = []
            if not df_target['periodo'].empty:
                for periodo in df_target['periodo'].dt.to_period('M').unique():
                    mask = df_target['periodo'].dt.to_period('M') == periodo
                    datos_mes = df_target[mask]
                    
                    if len(datos_mes) > 0:
                        tendencias.append({
                            'periodo': str(periodo),
                            'consumo_total_kwh': float(round(datos_mes['consumo_total_kwh'].mean(), 2)),
                            'costo_total': float(round(datos_mes['costo_total'].mean(), 2))
                        })
            
            return {
                "estadisticas_basicas": consumo_stats,
                "tendencias_mensuales": tendencias,
            }
            
        except Exception as e:
            logger.error(f"Error detallado en análisis básico: {str(e)}", exc_info=True)
            return {"error": f"Error en análisis: {str(e)}"}
    
    async def obtener_estadisticas_detalladas(self, df_para_analizar: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Estadísticas detalladas por año y mes."""
        df_target = df_para_analizar if df_para_analizar is not None else self._df_completo

        if df_target.empty:
            logger.warning("Estadísticas detalladas: No hay datos disponibles para analizar.")
            return {"error": "No hay datos disponibles"}
        
        try:
            if not all(col in df_target.columns for col in ['consumo_total_kwh', 'costo_total', 'demanda_maxima_kw', 'periodo']):
                logger.error("Estadísticas detalladas: Faltan columnas críticas en el DataFrame.")
                return {"error": "Faltan columnas críticas para las estadísticas detalladas."}


            stats_anuales = []
            if 'año' not in df_target.columns:
                 df_target['año'] = df_target['periodo'].dt.year
            
            if not df_target['año'].empty:
                for año in df_target['año'].unique():
                    datos_año = df_target[df_target['año'] == año]
                    stats_anuales.append({
                        'año': int(año),
                        'consumo_total_kwh_sum': float(round(datos_año['consumo_total_kwh'].sum(), 2)),
                        'consumo_total_kwh_mean': float(round(datos_año['consumo_total_kwh'].mean(), 2)),
                        'consumo_total_kwh_std': float(round(datos_año['consumo_total_kwh'].std(), 2)) if len(datos_año) > 1 else 0.0,
                        'costo_total_sum': float(round(datos_año['costo_total'].sum(), 2)),
                        'costo_total_mean': float(round(datos_año['costo_total'].mean(), 2)),
                        'demanda_maxima_kw_max': float(round(datos_año['demanda_maxima_kw'].max(), 2)),
                        'demanda_maxima_kw_mean': float(round(datos_año['demanda_maxima_kw'].mean(), 2)),
                    })
            
            patron_mensual = []
            if 'mes' not in df_target.columns:
                df_target['mes'] = df_target['periodo'].dt.month
            
            for mes in range(1, 13):
                datos_mes = df_target[df_target['mes'] == mes]
                if len(datos_mes) > 0:
                    patron_mensual.append({
                        'mes': int(mes),
                        'consumo_total_kwh': float(round(datos_mes['consumo_total_kwh'].mean(), 2)),
                        'costo_total': float(round(datos_mes['costo_total'].mean(), 2))
                    })
            
            correlacion_consumo_costo = float(round(df_target['consumo_total_kwh'].corr(df_target['costo_total']), 3)) if not df_target.empty else 0.0
            correlacion_demanda_consumo = float(round(df_target['demanda_maxima_kw'].corr(df_target['consumo_total_kwh']), 3)) if not df_target.empty else 0.0
            
            return {
                "estadisticas_anuales": stats_anuales,
                "patron_mensual": patron_mensual,
                "correlaciones": {
                    "consumo_costo": correlacion_consumo_costo,
                    "demanda_consumo": correlacion_demanda_consumo
                },
            }
            
        except Exception as e:
            logger.error(f"Error detallado en estadísticas: {str(e)}", exc_info=True)
            return {"error": f"Error en estadísticas detalladas: {str(e)}"}
    
    async def obtener_muestra_datos(self, limite: int = 12, df_para_analizar: Optional[pd.DataFrame] = None) -> List[Dict]:
        """Obtener muestra de datos para verificación."""
        df_target = df_para_analizar if df_para_analizar is not None else self._df_completo

        if df_target.empty:
            logger.warning("Muestra de datos: No hay datos disponibles para mostrar.")
            return []
        
        try:
            muestra = df_target.head(limite).copy()
            if 'periodo' in muestra.columns:
                muestra['periodo'] = muestra['periodo'].dt.strftime('%Y-%m-%d')
            
            resultado = []
            for _, row in muestra.iterrows():
                fila_dict = {columna: self._convertir_a_python(valor) for columna, valor in row.items()}
                resultado.append(fila_dict)
            
            return resultado
        except Exception as e:
            logger.error(f"Error en muestra de datos: {str(e)}", exc_info=True)
            return []