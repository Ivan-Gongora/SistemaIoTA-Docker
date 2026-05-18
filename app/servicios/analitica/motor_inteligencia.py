import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
from statsmodels.tsa.seasonal import STL
from sklearn.preprocessing import OneHotEncoder
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("motor_inteligencia_iot")

class MotorInteligenciaIoT:
    """
    Motor analítico de grado industrial.
    Ejecuta limpieza de series temporales, pruebas de hipótesis y detección de anomalías.
    """

    def __init__(self):
        self.intervalo_muestreo = '15min'
        self.nivel_significancia = 0.05
        self.umbral_contaminacion = 0.02

    # ==========================================
    # CAPA 1: PRE-PROCESAMIENTO Y FILTRADO
    # ==========================================
    def limpiar_serie_temporal(self, datos_crudos: List[Dict]) -> pd.DataFrame:
        """
        Remuestrea datos de alta frecuencia para eliminar ruido.
        Convierte lecturas de 5s en bloques de 15 minutos.
        """
        if not datos_crudos:
            return pd.DataFrame()

        df = pd.DataFrame(datos_crudos)
        df['fecha_hora'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'])
        df.set_index('fecha_hora', inplace=True)

        columnas_base = ['Temperatura', 'Humedad', 'Iluminacion', 'Potencia', 'Energia', 'Movimiento']
        for col in columnas_base:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        reglas_agregacion = {}
        if 'Potencia' in df.columns: reglas_agregacion['Potencia'] = 'mean'
        if 'Energia' in df.columns: reglas_agregacion['Energia'] = 'sum'
        if 'Temperatura' in df.columns: reglas_agregacion['Temperatura'] = 'mean'
        if 'Iluminacion' in df.columns: reglas_agregacion['Iluminacion'] = 'mean'
        if 'Movimiento' in df.columns: reglas_agregacion['Movimiento'] = 'max'

        df_limpio = df.resample(self.intervalo_muestreo).agg(reglas_agregacion).ffill().fillna(0)
        return df_limpio

    # ==========================================
    # CAPA 2: MOTOR ESTADÍSTICO Y CAUSALIDAD
    # ==========================================
    def validar_ahorro_t_student(self, df_base: pd.DataFrame, df_comparacion: pd.DataFrame) -> Dict[str, Any]:
        """
        Aplica Prueba T de Welch.
        Verifica si el ahorro energético tiene respaldo estadístico.
        """
        if df_base.empty or df_comparacion.empty or 'Energia' not in df_base.columns:
            return {"error": "Insuficientes datos de energía."}

        energia_base = df_base['Energia'].values
        energia_comp = df_comparacion['Energia'].values

        t_stat, p_valor = stats.ttest_ind(energia_base, energia_comp, equal_var=False, nan_policy='omit')
        
        media_base = np.nanmean(energia_base)
        media_comp = np.nanmean(energia_comp)
        reduccion_kwh = media_base - media_comp
        porcentaje = (reduccion_kwh / media_base * 100) if media_base > 0 else 0

        es_valido = bool(p_valor < self.nivel_significancia)

        return {
            "media_base": round(float(media_base), 3),
            "media_evaluada": round(float(media_comp), 3),
            "ahorro_porcentual": round(float(porcentaje), 2),
            "p_valor": float(p_valor),
            "estadisticamente_significativo": es_valido,
            "conclusion": "Ahorro validado científicamente." if es_valido and reduccion_kwh > 0 else "Fluctuación normal. No hay ahorro real."
        }

    def calcular_influencia_pearson(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Ejecuta Correlación de Pearson.
        Determina la fuerza de conexión entre clima, luz, movimiento y potencia.
        """
        if df.empty or len(df) < 5:
            return {"error": "Datos escasos para Pearson."}

        cols_objetivo = ['Movimiento', 'Iluminacion', 'Temperatura', 'Potencia']
        cols = [c for c in cols_objetivo if c in df.columns]

        matriz_corr = df[cols].corr(method='pearson')
        
        relaciones = {}
        if 'Potencia' in matriz_corr.columns:
            relaciones = matriz_corr['Potencia'].drop('Potencia').to_dict()

        diagnostico = {}
        for var, coef in relaciones.items():
            if pd.isna(coef):
                diagnostico[var] = "Varianza nula."
            elif coef > 0.6:
                diagnostico[var] = "Impacto directo fuerte."
            elif coef < -0.6:
                diagnostico[var] = "Impacto inverso fuerte."
            else:
                diagnostico[var] = "Impacto débil."

        return {
            "coeficientes": relaciones,
            "interpretacion": diagnostico
        }

    # ==========================================
    # CAPA 3: MACHINE LEARNING Y ANOMALÍAS
    # ==========================================
    def detectar_anomalias_isolation_forest(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Aplica Isolation Forest para encontrar picos inusuales.
        Aísla comportamientos fuera del patrón general del salón.
        """
        columnas_ml = ['Potencia', 'Corriente']
        df_modelo = df.dropna(subset=[c for c in columnas_ml if c in df.columns])

        if len(df_modelo) < 50:
            return {"error": "Se requieren 50 periodos mínimos para Machine Learning."}

        modelo_if = IsolationForest(contamination=self.umbral_contaminacion, random_state=42)
        df_modelo['anomalia'] = modelo_if.fit_predict(df_modelo[columnas_ml])
        
        # Filtramos donde anomalia == -1
        alertas = df_modelo[df_modelo['anomalia'] == -1]

        lista_anomalias = []
        for index, row in alertas.iterrows():
            lista_anomalias.append({
                "tiempo": str(index),
                "potencia_anomala_w": float(row.get('Potencia', 0))
            })

        return {
            "total_eventos_criticos": len(alertas),
            "nivel_contaminacion": self.umbral_contaminacion,
            "registro_eventos": lista_anomalias
        }

    def procesar_causalidad_textual(self, df_crudo: pd.DataFrame) -> Dict[str, Any]:
        """
        Procesa motivos de texto para cuantificar el costo de decisiones humanas.
        Cruza los campos de 'Motivo' con el consumo de energía.
        """
        if df_crudo.empty or 'Motivo_Luz' not in df_crudo.columns or 'Energia' not in df_crudo.columns:
            return {"error": "Faltan campos de texto o energía."}

        # Agrupamos la energía total gastada bajo cada motivo
        resumen_motivos = df_crudo.groupby('Motivo_Luz')['Energia'].sum().sort_values(ascending=False)

        top_motivos = resumen_motivos.head(5).to_dict()

        return {
            "motivos_mayor_impacto_kwh": top_motivos
        }