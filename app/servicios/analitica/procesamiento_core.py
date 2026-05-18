import pandas as pd
import numpy as np
from scipy import stats
import logging
from typing import Dict, Any, List

logger = logging.getLogger("motor_estadistico")

class MotorAnalisisAvanzado:
    def __init__(self):
        # Nivel de significancia estándar en investigación (95% de confianza)
        self.alfa = 0.05 

    def limpiar_y_remuestrear(self, datos_crudos: List[Dict], intervalo: str = '15T') -> pd.DataFrame:
        """
        Capa 1: Transforma datos ruidosos de 5 segundos en bloques de tiempo estructurados (ej. 15 minutos).
        Esto es vital para que las matemáticas posteriores sean precisas.
        """
        if not datos_crudos:
            return pd.DataFrame()

        df = pd.DataFrame(datos_crudos)
        df['fecha_hora'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'])
        df.set_index('fecha_hora', inplace=True)

        # Extraemos solo las métricas que nos interesan para este análisis
        columnas_numericas = ['Temperatura', 'Humedad', 'Iluminacion', 'Potencia', 'Energia', 'Movimiento']
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Remuestreo inteligente: Promedio para sensores ambientales, suma para energía, max para movimiento
        diccionario_agregacion = {}
        if 'Potencia' in df.columns: diccionario_agregacion['Potencia'] = 'mean'
        if 'Energia' in df.columns: diccionario_agregacion['Energia'] = 'sum'
        if 'Temperatura' in df.columns: diccionario_agregacion['Temperatura'] = 'mean'
        if 'Iluminacion' in df.columns: diccionario_agregacion['Iluminacion'] = 'mean'
        if 'Movimiento' in df.columns: diccionario_agregacion['Movimiento'] = 'max' # Si hubo movimiento en esos 15 min, es 1

        # Ejecuta el remuestreo y rellena vacíos (Forward Fill)
        df_resampled = df.resample(intervalo).agg(diccionario_agregacion).ffill().fillna(0)
        return df_resampled

    def analisis_pearson_influencia(self, df_resampled: pd.DataFrame) -> Dict[str, Any]:
        """
        Capa 2a: Aplica el Coeficiente de Correlación de Pearson.
        Mide la fuerza de la conexión entre Movimiento, Luz Ambiental y Potencia Eléctrica.
        """
        if df_resampled.empty or len(df_resampled) < 3:
            return {"error": "Datos insuficientes para calcular Pearson."}

        columnas_objetivo = ['Movimiento', 'Iluminacion', 'Potencia']
        cols_presentes = [c for c in columnas_objetivo if c in df_resampled.columns]

        # Calcula la matriz de correlación de Pearson (-1 a 1)
        matriz_pearson = df_resampled[cols_presentes].corr(method='pearson')

        # Extraemos cómo se relacionan los factores específicamente con la Potencia
        if 'Potencia' in matriz_pearson.columns:
            relacion_potencia = matriz_pearson['Potencia'].to_dict()
            del relacion_potencia['Potencia'] # Quitamos la auto-correlación (siempre es 1)
        else:
            relacion_potencia = {}

        return {
            "coeficientes_pearson": relacion_potencia,
            "interpretacion": self._interpretar_pearson(relacion_potencia)
        }

    def _interpretar_pearson(self, relaciones: Dict[str, float]) -> Dict[str, str]:
        interpretacion = {}
        for variable, coeficiente in relaciones.items():
            if pd.isna(coeficiente):
                interpretacion[variable] = "No hay varianza suficiente para medir."
            elif coeficiente > 0.7:
                interpretacion[variable] = "Fuerte conexión positiva (Suben juntos)."
            elif coeficiente < -0.7:
                interpretacion[variable] = "Fuerte conexión negativa (Uno sube, otro baja)."
            elif 0.3 < abs(coeficiente) <= 0.7:
                interpretacion[variable] = "Conexión moderada."
            else:
                interpretacion[variable] = "Conexión débil o nula."
        return interpretacion

    def prueba_t_student_comparativa(self, df_a: pd.DataFrame, df_b: pd.DataFrame) -> Dict[str, Any]:
        """
        Capa 2b: Prueba T de Welch (T-Student para varianzas desiguales).
        Determina si la diferencia de consumo entre dos periodos/salones es estadísticamente real o mera coincidencia.
        """
        if df_a.empty or df_b.empty or 'Energia' not in df_a.columns or 'Energia' not in df_b.columns:
            return {"error": "Faltan datos de Energía para la comparativa."}

        energia_a = df_a['Energia'].values
        energia_b = df_b['Energia'].values

        # Prueba T de Welch
        t_stat, p_valor = stats.ttest_ind(energia_a, energia_b, equal_var=False, nan_policy='omit')
        
        media_a = np.nanmean(energia_a)
        media_b = np.nanmean(energia_b)
        ahorro = media_a - media_b
        porcentaje_ahorro = (ahorro / media_a * 100) if media_a > 0 else 0

        # Si p_valor < 0.05, rechazamos la hipótesis nula (la diferencia es real)
        diferencia_estadistica = bool(p_valor < self.alfa)

        return {
            "consumo_promedio_A": round(float(media_a), 4),
            "consumo_promedio_B": round(float(media_b), 4),
            "reduccion_porcentual": round(float(porcentaje_ahorro), 2),
            "estadistico_t": round(float(t_stat), 4),
            "p_valor": float(p_valor),
            "certeza_cientifica": "Alta (Diferencia Real)" if diferencia_estadistica else "Baja (Posible coincidencia climática/azar)"
        }