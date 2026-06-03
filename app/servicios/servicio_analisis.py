
# version 1.5 - 2026-05-16 12:30 funciona correctamente
import pandas as pd
import numpy as np
from scipy import stats
from app.servicios.servicio_simulacion import get_db_connection
import gc
from app.configuracion import configuracion
import pymysql

class MotorAnalisisEnergetico:
    def __init__(self):
        self.factor_costo_kwh = 5.9

    def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
        conexion = get_db_connection()
        try:
            with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
                query_campos = """
                    SELECT cs.id, cs.nombre 
                    FROM campos_sensores cs
                    JOIN sensores s ON cs.sensor_id = s.id
                    WHERE s.dispositivo_id = %s
                """
                cursor_campos.execute(query_campos, (dispositivo_id,))
                campos = cursor_campos.fetchall()

            if not campos:
                return pd.DataFrame()

            campo_ids = [c['id'] for c in campos]
            mapa_nombres = {c['id']: c['nombre'] for c in campos}
            format_strings = ','.join(['%s'] * len(campo_ids))
            
            query_valores = f"""
                SELECT 
                    timestamp_minuto as Timestamp, 
                    campo_id, 
                    valor_avg as valor
                FROM valores_agregados_minuto 
                WHERE campo_id IN ({format_strings})
                  AND timestamp_minuto >= %s 
                  AND timestamp_minuto <= %s
            """
            parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
            with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
                cursor_valores.execute(query_valores, parametros)
                resultados = cursor_valores.fetchall()

        finally:
            conexion.close()

        if not resultados:
            return pd.DataFrame()

        df_raw = pd.DataFrame(resultados)
        df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
        df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
        columnas_esperadas = ['Energia', 'Movimiento', 'Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
        for col in columnas_esperadas:
            if col not in df.columns:
                df[col] = 0.0

        df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
        df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce').fillna(0).astype('float32')
        df['Humedad'] = pd.to_numeric(df['Humedad'], errors='coerce').fillna(0).astype('float32')
        df['Iluminacion'] = pd.to_numeric(df['Iluminacion'], errors='coerce').fillna(0).astype('float32')
        df['Temp_Ext'] = pd.to_numeric(df['Temp_Ext'], errors='coerce').fillna(0).astype('float32')
        df['Hum_Ext'] = pd.to_numeric(df['Hum_Ext'], errors='coerce').fillna(0).astype('float32')
        df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df.sort_values('Timestamp', inplace=True)
        
        df['Fecha_Corta'] = df['Timestamp'].dt.date
        df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
        
        df['Consumo_kWh'] = df.groupby('Fecha_Corta')['Energia'].diff().fillna(df['Energia'])
        df['Consumo_kWh'] = df['Consumo_kWh'].clip(lower=0).astype('float32')
        
        df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
        return df

    def _definir_periodo_cfe(self, ts):
        dia = ts.weekday()
        hora = ts.hour
        if dia < 5:
            if 0 <= hora < 7: return 'Base'
            if 18 <= hora < 22: return 'Punta'
            return 'Intermedia'
        elif dia == 5:
            if 0 <= hora < 7: return 'Base'
            return 'Intermedia'
        else:
            if 0 <= hora < 19: return 'Base'
            return 'Intermedia'

    def _calcular_matriz_correlacion(self, df: pd.DataFrame) -> dict:
        variables = ['Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
        correlaciones = {}
        var_consumo = df['Consumo_kWh'].var() if not df.empty else 0.0
        
        for var in variables:
            if var in df.columns and var_consumo > 0 and df[var].var() > 0:
                corr, _ = stats.pearsonr(df[var], df['Consumo_kWh'])
                correlaciones[var.lower()] = round(float(corr), 3)
            else:
                correlaciones[var.lower()] = 0.0
        return correlaciones

    def generar_analisis_fase(self, dispositivo_id: int, df: pd.DataFrame, factor_norm: float):
        if df.empty:
            return {'error': 'Datos no disponibles'}

        dias_totales = df['Fecha_Corta'].nunique()
        df['Fecha_Corta_Str'] = df['Fecha_Corta'].astype(str)

        consumo_diario_max = df.groupby('Fecha_Corta_Str')['Energia'].max()
        consumo_bruto = consumo_diario_max.sum()
        consumo_normalizado = consumo_bruto * factor_norm
        promedio_diario = consumo_normalizado / dias_totales if dias_totales > 0 else 0

        energia_periodo = df.groupby('Periodo_CFE')['Consumo_kWh'].sum() * factor_norm
        costo_total = consumo_normalizado * self.factor_costo_kwh

        registros_totales = len(df)
        registros_activos = (df['Movimiento'] > 0).sum()
        porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

        mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
        # Filtro de 0.0005 kWh por minuto (Equivale a equipos consumiendo mas de 30 Watts en reposo)
        inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Consumo_kWh'] > 0.0005)]
        energia_desperdiciada = inactividad_total['Consumo_kWh'].sum() * factor_norm

        var_consumo = df['Consumo_kWh'].var()
        corr_pir = 0.0
        if var_consumo > 0:
            corr_pir, _ = stats.pearsonr(df['Movimiento'], df['Consumo_kWh'])

        temp_promedio = df['Temperatura'].mean()
        hum_promedio = df['Humedad'].mean()

        consumo_horario_kwh = (df.groupby('Hora_Int')['Consumo_kWh'].sum() * factor_norm).to_dict()
        grafica_consumo_hora = [round(float(consumo_horario_kwh.get(h, 0.0)), 2) for h in range(24)]
        
        # Multiplicamos por 1000 para enviar Watts. El frontend lo espera para trazar el perfil termico correcto
        grafica_perfil_demanda = [round((float(consumo_horario_kwh.get(h, 0.0)) / dias_totales) * 1000.0, 2) if dias_totales > 0 else 0.0 for h in range(24)]

        agrupado_diario = df.groupby('Fecha_Corta_Str').agg(
            kwh_total=('Energia', 'max'),
            temp_prom=('Temperatura', 'mean'),
            hum_prom=('Humedad', 'mean'),
            temp_ext=('Temp_Ext', 'mean'),
            hum_ext=('Hum_Ext', 'mean')
        ).reset_index()

        tendencia_datos = []
        for _, row in agrupado_diario.iterrows():
            tendencia_datos.append({
                "fecha": row['Fecha_Corta_Str'],
                "kwh": round(float(row['kwh_total'] * factor_norm), 2),
                "temperatura": round(float(row['temp_prom']), 2),
                "humedad": round(float(row['hum_prom']), 2),
                "temp_ext": round(float(row['temp_ext']), 2),
                "hum_ext": round(float(row['hum_ext']), 2)
            })

        correlaciones_mes = self._calcular_matriz_correlacion(df)
        
        dia_tipico_str = "N/A"
        correlaciones_dia = {}
        
        if not consumo_diario_max.empty:
            promedio_bruto = consumo_bruto / dias_totales if dias_totales > 0 else 0
            diferencias = (consumo_diario_max - promedio_bruto).abs()
            dia_tipico_str = diferencias.idxmin()
            df_dia_tipico = df[df['Fecha_Corta_Str'] == dia_tipico_str]
            correlaciones_dia = self._calcular_matriz_correlacion(df_dia_tipico)

        return {
            'dispositivo_id': int(dispositivo_id),
            'consumo_bruto_kwh': round(float(consumo_bruto), 2),
            'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
            'promedio_diario': round(float(promedio_diario), 2),
            'temperatura_promedio': round(float(temp_promedio), 2),
            'humedad_promedio': round(float(hum_promedio), 2),
            'desglose_cfe': {
                'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
                'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
                'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
            },
            'costo_estimado_mxn': round(float(costo_total), 2),
            'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
            'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
            'correlacion_pir_potencia': round(float(corr_pir), 2),
            'grafica_perfil_demanda': grafica_perfil_demanda,
            'grafica_consumo_por_hora': grafica_consumo_hora,
            'grafica_tendencia_diaria': tendencia_datos,
            'correlaciones_ambientales': {
                'mes_completo': correlaciones_mes,
                'dia_tipico': {
                    'fecha': dia_tipico_str,
                    'valores': correlaciones_dia
                }
            }
        }

    def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
        df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
        df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)

        if df_base.empty or df_ctrl.empty:
            return {'error': 'Datos incompletos para procesar la comparativa'}

        dias_base = df_base['Fecha_Corta'].nunique()
        dias_ctrl = df_ctrl['Fecha_Corta'].nunique()
        factor_norm = dias_base / dias_ctrl if dias_ctrl > 0 else 1.0

        res_base = self.generar_analisis_fase(id_base, df_base, 1.0)
        res_ctrl = self.generar_analisis_fase(id_ctrl, df_ctrl, factor_norm)

        ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
        ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
        
        diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

        ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
        ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

        desperdicio_base = res_base['carga_fantasma_kwh']
        desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']

        diario_base = df_base.groupby('Fecha_Corta_Str')['Consumo_kWh'].sum() * 1.0
        diario_ctrl = df_ctrl.groupby('Fecha_Corta_Str')['Consumo_kWh'].sum() * factor_norm

        # Filtramos dias con consumo menor a 1 kWh (fines de semana) para no distorsionar el P-Valor
        dias_activos_base = diario_base[diario_base > 1.0]
        dias_activos_ctrl = diario_ctrl[diario_ctrl > 1.0]

        f_stat, p_val = 0.0, 1.0
        if len(dias_activos_base) > 1 and len(dias_activos_ctrl) > 1:
            f_stat, p_val = stats.f_oneway(dias_activos_base, dias_activos_ctrl)

        return {
            "status": "success",
            "data": {
                "3_1_validacion_funcional": {
                    "estado_analisis": "Completado",
                    "dias_fase_1": dias_base,
                    "dias_fase_2": dias_ctrl,
                    "registros_analizados": len(df_base) + len(df_ctrl)
                },
                "3_2_comportamiento_fase_1": res_base,
                "3_3_comportamiento_fase_2": res_ctrl,
                "3_4_comparacion_energetica": {
                    "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
                    "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
                    "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
                    "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
                    "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
                    "estadistica_anova_p_valor": float(p_val)
                },
                "3_5_evaluacion_confort": {
                    "temperatura_promedio_fase1": res_base['temperatura_promedio'],
                    "temperatura_promedio_fase2": res_ctrl['temperatura_promedio'],
                    "humedad_promedio_fase1": res_base['humedad_promedio'],
                    "humedad_promedio_fase2": res_ctrl['humedad_promedio']
                },
                "3_6_discusion_escalabilidad": {
                    "desperdicio_fase1_kwh": desperdicio_base,
                    "desperdicio_fase2_kwh": desperdicio_ctrl,
                    "analisis": "El sistema IoT requiere energía residual para mantener la conectividad. La Fase 2 documenta una carga fantasma operativa estándar. Este margen aprueba el encendido secuencial programado."
                },
                "dispositivo_base": res_base,
                "dispositivo_control": res_ctrl,
                "comparativa": {
                    "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
                    "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
                    "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
                    "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
                    "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
                    "estadistica_anova": {
                        "f_stat": round(float(f_stat), 2),
                        "p_valor": float(p_val)
                    }
                }
            }
        }

# import pandas as pd
# import numpy as np
# from scipy import stats
# from app.servicios.servicio_simulacion import get_db_connection
# import gc
# from app.configuracion import configuracion
# import pymysql

# class MotorAnalisisEnergetico:
#     def __init__(self):
#         self.factor_costo_kwh = 5.8

#     def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
#         conexion = get_db_connection()
#         try:
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
#                 query_campos = """
#                     SELECT cs.id, cs.nombre 
#                     FROM campos_sensores cs
#                     JOIN sensores s ON cs.sensor_id = s.id
#                     WHERE s.dispositivo_id = %s
#                 """
#                 cursor_campos.execute(query_campos, (dispositivo_id,))
#                 campos = cursor_campos.fetchall()

#             if not campos:
#                 return pd.DataFrame()

#             campo_ids = [c['id'] for c in campos]
#             mapa_nombres = {c['id']: c['nombre'] for c in campos}
#             format_strings = ','.join(['%s' for _ in campo_ids])
            
#             query_valores = f"""
#                 SELECT 
#                     timestamp_minuto as Timestamp, 
#                     campo_id, 
#                     valor_avg as valor
#                 FROM valores_agregados_minuto 
#                 WHERE campo_id IN ({format_strings})
#                   AND timestamp_minuto >= %s 
#                   AND timestamp_minuto <= %s
#             """
#             parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
#                 cursor_valores.execute(query_valores, parametros)
#                 resultados = cursor_valores.fetchall()

#         finally:
#             conexion.close()

#         if not resultados:
#             return pd.DataFrame()

#         df_raw = pd.DataFrame(resultados)
#         df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
#         df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
#         columnas_esperadas = ['Energia', 'Movimiento', 'Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
#         for col in columnas_esperadas:
#             if col not in df.columns:
#                 df[col] = 0.0

#         df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
#         df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce').fillna(0).astype('float32')
#         df['Humedad'] = pd.to_numeric(df['Humedad'], errors='coerce').fillna(0).astype('float32')
#         df['Iluminacion'] = pd.to_numeric(df['Iluminacion'], errors='coerce').fillna(0).astype('float32')
#         df['Temp_Ext'] = pd.to_numeric(df['Temp_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Hum_Ext'] = pd.to_numeric(df['Hum_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
#         df['Timestamp'] = pd.to_datetime(df['Timestamp'])
#         df.sort_values('Timestamp', inplace=True)
        
#         df['Fecha_Corta'] = df['Timestamp'].dt.date
#         df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
        
#         df['Consumo_kWh'] = df.groupby('Fecha_Corta')['Energia'].diff().fillna(df['Energia'])
#         df['Consumo_kWh'] = df['Consumo_kWh'].clip(lower=0).astype('float32')
        
#         df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
#         return df

#     def _definir_periodo_cfe(self, ts):
#         dia = ts.weekday()
#         hora = ts.hour
#         if dia < 5:
#             if 0 <= hora < 7: return 'Base'
#             if 18 <= hora < 22: return 'Punta'
#             return 'Intermedia'
#         elif dia == 5:
#             if 0 <= hora < 7: return 'Base'
#             return 'Intermedia'
#         else:
#             if 0 <= hora < 19: return 'Base'
#             return 'Intermedia'

#     def _calcular_matriz_correlacion(self, df: pd.DataFrame) -> dict:
#         variables = ['Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
#         correlaciones = {}
#         var_consumo = df['Consumo_kWh'].var() if not df.empty else 0.0
        
#         for var in variables:
#             if var in df.columns and var_consumo > 0 and df[var].var() > 0:
#                 corr, _ = stats.pearsonr(df[var], df['Consumo_kWh'])
#                 correlaciones[var.lower()] = round(float(corr), 3)
#             else:
#                 correlaciones[var.lower()] = 0.0
#         return correlaciones

#     def generar_analisis_fase(self, dispositivo_id: int, df: pd.DataFrame, factor_norm: float):
#         if df.empty:
#             return {'error': 'Datos no disponibles'}

#         dias_totales = df['Fecha_Corta'].nunique()
#         df['Fecha_Corta_Str'] = df['Fecha_Corta'].astype(str)

#         consumo_diario_max = df.groupby('Fecha_Corta_Str')['Energia'].max()
#         consumo_bruto = consumo_diario_max.sum()
#         consumo_normalizado = consumo_bruto * factor_norm
#         promedio_diario = consumo_normalizado / dias_totales if dias_totales > 0 else 0

#         energia_periodo = df.groupby('Periodo_CFE')['Consumo_kWh'].sum() * factor_norm
#         costo_total = consumo_normalizado * self.factor_costo_kwh

#         registros_totales = len(df)
#         registros_activos = (df['Movimiento'] > 0).sum()
#         porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

#         mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
#         inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Consumo_kWh'] > 0.0005)]
#         energia_desperdiciada = inactividad_total['Consumo_kWh'].sum() * factor_norm

#         var_consumo = df['Consumo_kWh'].var()
#         corr_pir = 0.0
#         if var_consumo > 0:
#             corr_pir, _ = stats.pearsonr(df['Movimiento'], df['Consumo_kWh'])

#         temp_promedio = df['Temperatura'].mean()
#         hum_promedio = df['Humedad'].mean()

#         consumo_horario_kwh = (df.groupby('Hora_Int')['Consumo_kWh'].sum() * factor_norm).to_dict()
#         grafica_consumo_hora = [round(float(consumo_horario_kwh.get(h, 0.0)), 2) for h in range(24)]
        
#         grafica_perfil_demanda = [round((float(consumo_horario_kwh.get(h, 0.0)) / dias_totales) * 1000.0, 2) if dias_totales > 0 else 0.0 for h in range(24)]

#         agrupado_diario = df.groupby('Fecha_Corta_Str').agg(
#             kwh_total=('Energia', 'max'),
#             temp_prom=('Temperatura', 'mean'),
#             hum_prom=('Humedad', 'mean'),
#             temp_ext=('Temp_Ext', 'mean'),
#             hum_ext=('Hum_Ext', 'mean')
#         ).reset_index()

#         tendencia_datos = []
#         for _, row in agrupado_diario.iterrows():
#             tendencia_datos.append({
#                 "fecha": row['Fecha_Corta_Str'],
#                 "kwh": round(float(row['kwh_total'] * factor_norm), 2),
#                 "temperatura": round(float(row['temp_prom']), 2),
#                 "humedad": round(float(row['hum_prom']), 2),
#                 "temp_ext": round(float(row['temp_ext']), 2),
#                 "hum_ext": round(float(row['hum_ext']), 2)
#             })

#         correlaciones_mes = self._calcular_matriz_correlacion(df)
        
#         dia_tipico_str = "N/A"
#         correlaciones_dia = {}
        
#         if not consumo_diario_max.empty:
#             promedio_bruto = consumo_bruto / dias_totales if dias_totales > 0 else 0
#             diferencias = (consumo_diario_max - promedio_bruto).abs()
#             dia_tipico_str = diferencias.idxmin()
#             df_dia_tipico = df[df['Fecha_Corta_Str'] == dia_tipico_str]
#             correlaciones_dia = self._calcular_matriz_correlacion(df_dia_tipico)

#         return {
#             'dispositivo_id': int(dispositivo_id),
#             'consumo_bruto_kwh': round(float(consumo_bruto), 2),
#             'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
#             'promedio_diario': round(float(promedio_diario), 2),
#             'temperatura_promedio': round(float(temp_promedio), 2),
#             'humedad_promedio': round(float(hum_promedio), 2),
#             'desglose_cfe': {
#                 'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
#                 'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
#                 'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
#             },
#             'costo_estimado_mxn': round(float(costo_total), 2),
#             'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
#             'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
#             'correlacion_pir_potencia': round(float(corr_pir), 2),
#             'grafica_perfil_demanda': grafica_perfil_demanda,
#             'grafica_consumo_por_hora': grafica_consumo_hora,
#             'grafica_tendencia_diaria': tendencia_datos,
#             'correlaciones_ambientales': {
#                 'mes_completo': correlaciones_mes,
#                 'dia_tipico': {
#                     'fecha': dia_tipico_str,
#                     'valores': correlaciones_dia
#                 }
#             }
#         }

#     def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
#         df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
#         df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)

#         if df_base.empty or df_ctrl.empty:
#             return {'error': 'Datos incompletos para procesar la comparativa'}

#         dias_base = df_base['Fecha_Corta'].nunique()
#         dias_ctrl = df_ctrl['Fecha_Corta'].nunique()
#         factor_norm = dias_base / dias_ctrl if dias_ctrl > 0 else 1.0

#         res_base = self.generar_analisis_fase(id_base, df_base, 1.0)
#         res_ctrl = self.generar_analisis_fase(id_ctrl, df_ctrl, factor_norm)

#         ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
#         ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
        
#         diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

#         ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
#         ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

#         desperdicio_base = res_base['carga_fantasma_kwh']
#         desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']

#         diario_base = df_base.groupby('Fecha_Corta_Str')['Consumo_kWh'].sum() * 1.0
#         diario_ctrl = df_ctrl.groupby('Fecha_Corta_Str')['Consumo_kWh'].sum() * factor_norm

#         dias_activos_base = diario_base[diario_base > 1.0]
#         dias_activos_ctrl = diario_ctrl[diario_ctrl > 1.0]

#         f_stat, p_val = 0.0, 1.0
#         if len(dias_activos_base) > 1 and len(dias_activos_ctrl) > 1:
#             f_stat, p_val = stats.f_oneway(dias_activos_base, dias_activos_ctrl)

#         return {
#             "status": "success",
#             "data": {
#                 "3_1_validacion_funcional": {
#                     "estado_analisis": "Completado",
#                     "dias_fase_1": dias_base,
#                     "dias_fase_2": dias_ctrl,
#                     "registros_analizados": len(df_base) + len(df_ctrl)
#                 },
#                 "3_2_comportamiento_fase_1": res_base,
#                 "3_3_comportamiento_fase_2": res_ctrl,
#                 "3_4_comparacion_energetica": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "estadistica_anova_p_valor": float(p_val)
#                 },
#                 "3_5_evaluacion_confort": {
#                     "temperatura_promedio_fase1": res_base['temperatura_promedio'],
#                     "temperatura_promedio_fase2": res_ctrl['temperatura_promedio'],
#                     "humedad_promedio_fase1": res_base['humedad_promedio'],
#                     "humedad_promedio_fase2": res_ctrl['humedad_promedio']
#                 },
#                 "3_6_discusion_escalabilidad": {
#                     "desperdicio_fase1_kwh": desperdicio_base,
#                     "desperdicio_fase2_kwh": desperdicio_ctrl,
#                     "analisis": "El sistema IoT requiere energia residual para mantener la conectividad. La Fase 2 documenta una carga fantasma operativa estandar. Este margen aprueba el encendido secuencial programado."
#                 },
#                 "dispositivo_base": res_base,
#                 "dispositivo_control": res_ctrl,
#                 "comparativa": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "estadistica_anova": {
#                         "f_stat": round(float(f_stat), 2),
#                         "p_valor": float(p_val)
#                     }
#                 }
#             }
#         }




# import pandas as pd
# import numpy as np
# from scipy import stats
# from app.servicios.servicio_simulacion import get_db_connection
# import gc
# from app.configuracion import configuracion
# import pymysql

# class MotorAnalisisEnergetico:
#     def __init__(self):
#         self.factor_costo_kwh = 3.75

#     def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
#         conexion = get_db_connection()
#         try:
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
#                 query_campos = """
#                     SELECT cs.id, cs.nombre 
#                     FROM campos_sensores cs
#                     JOIN sensores s ON cs.sensor_id = s.id
#                     WHERE s.dispositivo_id = %s
#                 """
#                 cursor_campos.execute(query_campos, (dispositivo_id,))
#                 campos = cursor_campos.fetchall()

#             if not campos:
#                 return pd.DataFrame()

#             campo_ids = [c['id'] for c in campos]
#             mapa_nombres = {c['id']: c['nombre'] for c in campos}
#             format_strings = ','.join(['%s'] * len(campo_ids))
            
#             query_valores = f"""
#                 SELECT 
#                     timestamp_minuto as Timestamp, 
#                     campo_id, 
#                     valor_avg as valor
#                 FROM valores_agregados_minuto 
#                 WHERE campo_id IN ({format_strings})
#                   AND timestamp_minuto >= %s 
#                   AND timestamp_minuto <= %s
#             """
#             parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
#                 cursor_valores.execute(query_valores, parametros)
#                 resultados = cursor_valores.fetchall()

#         finally:
#             conexion.close()

#         if not resultados:
#             return pd.DataFrame()

#         df_raw = pd.DataFrame(resultados)
#         df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
#         df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
#         columnas_esperadas = ['Energia', 'Movimiento', 'Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
#         for col in columnas_esperadas:
#             if col not in df.columns:
#                 df[col] = 0.0

#         df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
#         df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce').fillna(0).astype('float32')
#         df['Humedad'] = pd.to_numeric(df['Humedad'], errors='coerce').fillna(0).astype('float32')
#         df['Iluminacion'] = pd.to_numeric(df['Iluminacion'], errors='coerce').fillna(0).astype('float32')
#         df['Temp_Ext'] = pd.to_numeric(df['Temp_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Hum_Ext'] = pd.to_numeric(df['Hum_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
#         df['Timestamp'] = pd.to_datetime(df['Timestamp'])
#         df.sort_values('Timestamp', inplace=True)
        
#         df['Fecha_Corta'] = df['Timestamp'].dt.date
#         df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
        
#         df['Consumo_kWh'] = df.groupby('Fecha_Corta')['Energia'].diff().fillna(df['Energia'])
#         df['Consumo_kWh'] = df['Consumo_kWh'].clip(lower=0).astype('float32')
        
#         df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
#         return df

#     def _definir_periodo_cfe(self, ts):
#         dia = ts.weekday()
#         hora = ts.hour
#         if dia < 5:
#             if 0 <= hora < 7: return 'Base'
#             if 18 <= hora < 22: return 'Punta'
#             return 'Intermedia'
#         elif dia == 5:
#             if 0 <= hora < 7: return 'Base'
#             return 'Intermedia'
#         else:
#             if 0 <= hora < 19: return 'Base'
#             return 'Intermedia'

#     def _calcular_matriz_correlacion(self, df: pd.DataFrame) -> dict:
#         variables = ['Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
#         correlaciones = {}
#         var_consumo = df['Consumo_kWh'].var() if not df.empty else 0.0
        
#         for var in variables:
#             if var in df.columns and var_consumo > 0 and df[var].var() > 0:
#                 corr, _ = stats.pearsonr(df[var], df['Consumo_kWh'])
#                 correlaciones[var.lower()] = round(float(corr), 3)
#             else:
#                 correlaciones[var.lower()] = 0.0
#         return correlaciones

#     def generar_analisis_fase(self, dispositivo_id: int, df: pd.DataFrame, factor_norm: float):
#         if df.empty:
#             return {'error': 'Datos no disponibles'}

#         dias_totales = df['Fecha_Corta'].nunique()
#         df['Fecha_Corta_Str'] = df['Fecha_Corta'].astype(str)

#         consumo_diario_max = df.groupby('Fecha_Corta_Str')['Energia'].max()
#         consumo_bruto = consumo_diario_max.sum()
#         consumo_normalizado = consumo_bruto * factor_norm
#         promedio_diario = consumo_normalizado / dias_totales if dias_totales > 0 else 0

#         energia_periodo = df.groupby('Periodo_CFE')['Consumo_kWh'].sum() * factor_norm
#         costo_total = consumo_normalizado * self.factor_costo_kwh

#         registros_totales = len(df)
#         registros_activos = (df['Movimiento'] > 0).sum()
#         porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

#         mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
#         inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Consumo_kWh'] > 0)]
#         energia_desperdiciada = inactividad_total['Consumo_kWh'].sum() * factor_norm

#         var_consumo = df['Consumo_kWh'].var()
#         corr_pir = 0.0
#         if var_consumo > 0:
#             corr_pir, _ = stats.pearsonr(df['Movimiento'], df['Consumo_kWh'])

#         temp_promedio = df['Temperatura'].mean()
#         hum_promedio = df['Humedad'].mean()

#         consumo_horario_kwh = (df.groupby('Hora_Int')['Consumo_kWh'].sum() * factor_norm).to_dict()
#         grafica_consumo_hora = [round(float(consumo_horario_kwh.get(h, 0.0)), 2) for h in range(24)]
        
#         grafica_perfil_demanda = [round(float(consumo_horario_kwh.get(h, 0.0)) / dias_totales, 2) if dias_totales > 0 else 0.0 for h in range(24)]

#         agrupado_diario = df.groupby('Fecha_Corta_Str').agg(
#             kwh_total=('Energia', 'max'),
#             temp_prom=('Temperatura', 'mean'),
#             hum_prom=('Humedad', 'mean'),
#             temp_ext=('Temp_Ext', 'mean'),
#             hum_ext=('Hum_Ext', 'mean')
#         ).reset_index()

#         tendencia_datos = []
#         for _, row in agrupado_diario.iterrows():
#             tendencia_datos.append({
#                 "fecha": row['Fecha_Corta_Str'],
#                 "kwh": round(float(row['kwh_total'] * factor_norm), 2),
#                 "temperatura": round(float(row['temp_prom']), 2),
#                 "humedad": round(float(row['hum_prom']), 2),
#                 "temp_ext": round(float(row['temp_ext']), 2),
#                 "hum_ext": round(float(row['hum_ext']), 2)
#             })

#         correlaciones_mes = self._calcular_matriz_correlacion(df)
        
#         dia_tipico_str = "N/A"
#         correlaciones_dia = {}
        
#         if not consumo_diario_max.empty:
#             promedio_bruto = consumo_bruto / dias_totales if dias_totales > 0 else 0
#             diferencias = (consumo_diario_max - promedio_bruto).abs()
#             dia_tipico_str = diferencias.idxmin()
#             df_dia_tipico = df[df['Fecha_Corta_Str'] == dia_tipico_str]
#             correlaciones_dia = self._calcular_matriz_correlacion(df_dia_tipico)

#         return {
#             'dispositivo_id': int(dispositivo_id),
#             'consumo_bruto_kwh': round(float(consumo_bruto), 2),
#             'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
#             'promedio_diario': round(float(promedio_diario), 2),
#             'temperatura_promedio': round(float(temp_promedio), 2),
#             'humedad_promedio': round(float(hum_promedio), 2),
#             'desglose_cfe': {
#                 'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
#                 'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
#                 'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
#             },
#             'costo_estimado_mxn': round(float(costo_total), 2),
#             'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
#             'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
#             'correlacion_pir_potencia': round(float(corr_pir), 2),
#             'grafica_perfil_demanda': grafica_perfil_demanda,
#             'grafica_consumo_por_hora': grafica_consumo_hora,
#             'grafica_tendencia_diaria': tendencia_datos,
#             'correlaciones_ambientales': {
#                 'mes_completo': correlaciones_mes,
#                 'dia_tipico': {
#                     'fecha': dia_tipico_str,
#                     'valores': correlaciones_dia
#                 }
#             }
#         }

#     def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
#         df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
#         df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)

#         if df_base.empty or df_ctrl.empty:
#             return {'error': 'Datos incompletos para procesar la comparativa'}

#         dias_base = df_base['Fecha_Corta'].nunique()
#         dias_ctrl = df_ctrl['Fecha_Corta'].nunique()
#         factor_norm = dias_base / dias_ctrl if dias_ctrl > 0 else 1.0

#         res_base = self.generar_analisis_fase(id_base, df_base, 1.0)
#         res_ctrl = self.generar_analisis_fase(id_ctrl, df_ctrl, factor_norm)

#         ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
#         ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
        
#         diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

#         ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
#         ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

#         desperdicio_base = res_base['carga_fantasma_kwh']
#         desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']

#         diario_base = df_base.groupby('Fecha_Corta_Str')['Consumo_kWh'].sum() * 1.0
#         diario_ctrl = df_ctrl.groupby('Fecha_Corta_Str')['Consumo_kWh'].sum() * factor_norm

#         f_stat, p_val = 0.0, 1.0
#         if len(diario_base) > 1 and len(diario_ctrl) > 1:
#             f_stat, p_val = stats.f_oneway(diario_base, diario_ctrl)

#         return {
#             "status": "success",
#             "data": {
#                 "3_1_validacion_funcional": {
#                     "estado_analisis": "Completado",
#                     "dias_fase_1": dias_base,
#                     "dias_fase_2": dias_ctrl,
#                     "registros_analizados": len(df_base) + len(df_ctrl)
#                 },
#                 "3_2_comportamiento_fase_1": res_base,
#                 "3_3_comportamiento_fase_2": res_ctrl,
#                 "3_4_comparacion_energetica": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "estadistica_anova_p_valor": float(p_val)
#                 },
#                 "3_5_evaluacion_confort": {
#                     "temperatura_promedio_fase1": res_base['temperatura_promedio'],
#                     "temperatura_promedio_fase2": res_ctrl['temperatura_promedio'],
#                     "humedad_promedio_fase1": res_base['humedad_promedio'],
#                     "humedad_promedio_fase2": res_ctrl['humedad_promedio']
#                 },
#                 "3_6_discusion_escalabilidad": {
#                     "desperdicio_fase1_kwh": desperdicio_base,
#                     "desperdicio_fase2_kwh": desperdicio_ctrl,
#                     "analisis": "El sistema IoT mantiene un consumo de reposo para sostener la conectividad. La Fase 2 requiere energía continua para el microcontrolador. Este margen operativo permite erradicar picos destructivos y gestionar el encendido secuencial."
#                 },
#                 "dispositivo_base": res_base,
#                 "dispositivo_control": res_ctrl,
#                 "comparativa": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "estadistica_anova": {
#                         "f_stat": round(float(f_stat), 2),
#                         "p_valor": float(p_val)
#                     }
#                 }
#             }
#         }

# import pandas as pd
# import numpy as np
# from scipy import stats
# from app.servicios.servicio_simulacion import get_db_connection
# import gc
# from app.configuracion import configuracion
# import pymysql

# class MotorAnalisisEnergetico:
#     def __init__(self):
#         self.factor_costo_kwh = 3.75

#     def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
#         conexion = get_db_connection()
#         try:
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
#                 query_campos = """
#                     SELECT cs.id, cs.nombre 
#                     FROM campos_sensores cs
#                     JOIN sensores s ON cs.sensor_id = s.id
#                     WHERE s.dispositivo_id = %s
#                 """
#                 cursor_campos.execute(query_campos, (dispositivo_id,))
#                 campos = cursor_campos.fetchall()

#             if not campos:
#                 return pd.DataFrame()

#             campo_ids = [c['id'] for c in campos]
#             mapa_nombres = {c['id']: c['nombre'] for c in campos}
#             format_strings = ','.join(['%s'] * len(campo_ids))
            
#             query_valores = f"""
#                 SELECT 
#                     timestamp_minuto as Timestamp, 
#                     campo_id, 
#                     valor_avg as valor
#                 FROM valores_agregados_minuto 
#                 WHERE campo_id IN ({format_strings})
#                   AND timestamp_minuto >= %s 
#                   AND timestamp_minuto <= %s
#             """
#             parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
#                 cursor_valores.execute(query_valores, parametros)
#                 resultados = cursor_valores.fetchall()

#         finally:
#             conexion.close()

#         if not resultados:
#             return pd.DataFrame()

#         df_raw = pd.DataFrame(resultados)
#         df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
#         df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
#         columnas_esperadas = ['Energia', 'Movimiento', 'Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
#         for col in columnas_esperadas:
#             if col not in df.columns:
#                 df[col] = 0.0

#         df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
#         df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce').fillna(0).astype('float32')
#         df['Humedad'] = pd.to_numeric(df['Humedad'], errors='coerce').fillna(0).astype('float32')
#         df['Iluminacion'] = pd.to_numeric(df['Iluminacion'], errors='coerce').fillna(0).astype('float32')
#         df['Temp_Ext'] = pd.to_numeric(df['Temp_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Hum_Ext'] = pd.to_numeric(df['Hum_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
#         df['Timestamp'] = pd.to_datetime(df['Timestamp'])
#         df.sort_values('Timestamp', inplace=True)
        
#         df['Fecha_Corta'] = df['Timestamp'].dt.date
#         df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
        
#         df['Consumo_kWh'] = df.groupby('Fecha_Corta')['Energia'].diff().fillna(df['Energia'])
#         df['Consumo_kWh'] = df['Consumo_kWh'].clip(lower=0).astype('float32')
        
#         df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
#         return df

#     def _definir_periodo_cfe(self, ts):
#         dia = ts.weekday()
#         hora = ts.hour
#         if dia < 5:
#             if 0 <= hora < 7: return 'Base'
#             if 18 <= hora < 22: return 'Punta'
#             return 'Intermedia'
#         elif dia == 5:
#             if 0 <= hora < 7: return 'Base'
#             return 'Intermedia'
#         else:
#             if 0 <= hora < 19: return 'Base'
#             return 'Intermedia'

#     def _calcular_matriz_correlacion(self, df: pd.DataFrame) -> dict:
#         variables = ['Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext']
#         correlaciones = {}
#         var_consumo = df['Consumo_kWh'].var() if not df.empty else 0.0
        
#         for var in variables:
#             if var in df.columns and var_consumo > 0 and df[var].var() > 0:
#                 corr, _ = stats.pearsonr(df[var], df['Consumo_kWh'])
#                 correlaciones[var.lower()] = round(float(corr), 3)
#             else:
#                 correlaciones[var.lower()] = 0.0
#         return correlaciones

#     def generar_analisis_fase(self, dispositivo_id: int, df: pd.DataFrame, factor_norm: float):
#         if df.empty:
#             return {'error': 'Datos no disponibles'}

#         dias_totales = df['Fecha_Corta'].nunique()
#         df['Fecha_Corta_Str'] = df['Fecha_Corta'].astype(str)

#         consumo_diario_max = df.groupby('Fecha_Corta_Str')['Energia'].max()
#         consumo_bruto = consumo_diario_max.sum()
#         consumo_normalizado = consumo_bruto * factor_norm
#         promedio_diario = consumo_normalizado / dias_totales if dias_totales > 0 else 0

#         energia_periodo = df.groupby('Periodo_CFE')['Consumo_kWh'].sum() * factor_norm
#         costo_total = consumo_normalizado * self.factor_costo_kwh

#         registros_totales = len(df)
#         registros_activos = (df['Movimiento'] > 0).sum()
#         porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

#         mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
#         inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Consumo_kWh'] > 0)]
#         energia_desperdiciada = inactividad_total['Consumo_kWh'].sum() * factor_norm

#         var_consumo = df['Consumo_kWh'].var()
#         corr_pir = 0.0
#         if var_consumo > 0:
#             corr_pir, _ = stats.pearsonr(df['Movimiento'], df['Consumo_kWh'])

#         temp_promedio = df['Temperatura'].mean()
#         hum_promedio = df['Humedad'].mean()

#         consumo_horario_kwh = (df.groupby('Hora_Int')['Consumo_kWh'].sum() * factor_norm).round(2).to_dict()
#         grafica_consumo_hora = [float(consumo_horario_kwh.get(h, 0.0)) for h in range(24)]
        
#         perfil_horario_promedio = df.groupby('Hora_Int')['Consumo_kWh'].mean().round(2).to_dict()
#         grafica_perfil_demanda = [float(perfil_horario_promedio.get(h, 0.0)) for h in range(24)]

#         agrupado_diario = df.groupby('Fecha_Corta_Str').agg(
#             kwh_total=('Energia', 'max'),
#             temp_prom=('Temperatura', 'mean'),
#             hum_prom=('Humedad', 'mean'),
#             temp_ext=('Temp_Ext', 'mean'),
#             hum_ext=('Hum_Ext', 'mean')
#         ).reset_index()

#         tendencia_datos = []
#         for _, row in agrupado_diario.iterrows():
#             tendencia_datos.append({
#                 "fecha": row['Fecha_Corta_Str'],
#                 "kwh": round(float(row['kwh_total'] * factor_norm), 2),
#                 "temperatura": round(float(row['temp_prom']), 2),
#                 "humedad": round(float(row['hum_prom']), 2),
#                 "temp_ext": round(float(row['temp_ext']), 2),
#                 "hum_ext": round(float(row['hum_ext']), 2)
#             })

#         correlaciones_mes = self._calcular_matriz_correlacion(df)
        
#         dia_tipico_str = "N/A"
#         correlaciones_dia = {}
        
#         if not consumo_diario_max.empty:
#             promedio_bruto = consumo_bruto / dias_totales if dias_totales > 0 else 0
#             diferencias = (consumo_diario_max - promedio_bruto).abs()
#             dia_tipico_str = diferencias.idxmin()
#             df_dia_tipico = df[df['Fecha_Corta_Str'] == dia_tipico_str]
#             correlaciones_dia = self._calcular_matriz_correlacion(df_dia_tipico)

#         return {
#             'dispositivo_id': int(dispositivo_id),
#             'consumo_bruto_kwh': round(float(consumo_bruto), 2),
#             'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
#             'promedio_diario': round(float(promedio_diario), 2),
#             'temperatura_promedio': round(float(temp_promedio), 2),
#             'humedad_promedio': round(float(hum_promedio), 2),
#             'desglose_cfe': {
#                 'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
#                 'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
#                 'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
#             },
#             'costo_estimado_mxn': round(float(costo_total), 2),
#             'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
#             'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
#             'correlacion_pir_potencia': round(float(corr_pir), 2),
#             'grafica_perfil_demanda': grafica_perfil_demanda,
#             'grafica_consumo_por_hora': grafica_consumo_hora,
#             'grafica_tendencia_diaria': tendencia_datos,
#             'correlaciones_ambientales': {
#                 'mes_completo': correlaciones_mes,
#                 'dia_tipico': {
#                     'fecha': dia_tipico_str,
#                     'valores': correlaciones_dia
#                 }
#             }
#         }

#     def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
#         df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
#         df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)

#         if df_base.empty or df_ctrl.empty:
#             return {'error': 'Datos incompletos para procesar la comparativa'}

#         dias_base = df_base['Fecha_Corta'].nunique()
#         dias_ctrl = df_ctrl['Fecha_Corta'].nunique()
#         factor_norm = dias_base / dias_ctrl if dias_ctrl > 0 else 1.0

#         res_base = self.generar_analisis_fase(id_base, df_base, 1.0)
#         res_ctrl = self.generar_analisis_fase(id_ctrl, df_ctrl, factor_norm)

#         ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
#         ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
        
#         diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

#         ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
#         ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

#         desperdicio_base = res_base['carga_fantasma_kwh']
#         desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']

#         f_stat, p_val = 0.0, 1.0
#         if df_base['Consumo_kWh'].var() > 0 and df_ctrl['Consumo_kWh'].var() > 0:
#             f_stat, p_val = stats.f_oneway(df_base['Consumo_kWh'], df_ctrl['Consumo_kWh'])

#         return {
#             "status": "success",
#             "data": {
#                 "3_1_validacion_funcional": {
#                     "estado_analisis": "Completado",
#                     "dias_fase_1": dias_base,
#                     "dias_fase_2": dias_ctrl,
#                     "registros_analizados": len(df_base) + len(df_ctrl)
#                 },
#                 "3_2_comportamiento_fase_1": res_base,
#                 "3_3_comportamiento_fase_2": res_ctrl,
#                 "3_4_comparacion_energetica": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "estadistica_anova_p_valor": float(p_val)
#                 },
#                 "3_5_evaluacion_confort": {
#                     "temperatura_promedio_fase1": res_base['temperatura_promedio'],
#                     "temperatura_promedio_fase2": res_ctrl['temperatura_promedio'],
#                     "humedad_promedio_fase1": res_base['humedad_promedio'],
#                     "humedad_promedio_fase2": res_ctrl['humedad_promedio']
#                 },
#                 "3_6_discusion_escalabilidad": {
#                     "desperdicio_fase1_kwh": desperdicio_base,
#                     "desperdicio_fase2_kwh": desperdicio_ctrl,
#                     "analisis": "El sistema IoT mantiene un consumo de reposo para sostener la conectividad. La Fase 2 requiere energía continua para el microcontrolador. Este margen operativo permite erradicar picos destructivos y gestionar el encendido secuencial."
#                 },
#                 "dispositivo_base": res_base,
#                 "dispositivo_control": res_ctrl,
#                 "comparativa": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "estadistica_anova": {
#                         "f_stat": round(float(f_stat), 2),
#                         "p_valor": float(p_val)
#                     }
#                 }
#             }
#         }

# version 1.1 - 2026-05-10 12:30 funciona correctamente
# import pandas as pd
# import numpy as np
# from scipy import stats
# from app.servicios.servicio_simulacion import get_db_connection
# import gc
# from app.configuracion import configuracion
# import pymysql

# class MotorAnalisisEnergetico:
#     def __init__(self):
#         self.factor_costo_kwh = 3.75

#     def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
#         conexion = get_db_connection()
#         try:
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
#                 query_campos = """
#                     SELECT cs.id, cs.nombre 
#                     FROM campos_sensores cs
#                     JOIN sensores s ON cs.sensor_id = s.id
#                     WHERE s.dispositivo_id = %s
#                 """
#                 cursor_campos.execute(query_campos, (dispositivo_id,))
#                 campos = cursor_campos.fetchall()

#             if not campos:
#                 return pd.DataFrame()

#             campo_ids = [c['id'] for c in campos]
#             mapa_nombres = {c['id']: c['nombre'] for c in campos}
#             format_strings = ','.join(['%s'] * len(campo_ids))
            
#             query_valores = f"""
#                 SELECT 
#                     timestamp_minuto as Timestamp, 
#                     campo_id, 
#                     valor_avg as valor,
#                     valor_texto
#                 FROM valores_agregados_minuto 
#                 WHERE campo_id IN ({format_strings})
#                   AND timestamp_minuto >= %s 
#                   AND timestamp_minuto <= %s
#             """
#             parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
#                 cursor_valores.execute(query_valores, parametros)
#                 resultados = cursor_valores.fetchall()

#         finally:
#             conexion.close()

#         if not resultados:
#             return pd.DataFrame()

#         df_raw = pd.DataFrame(resultados)
#         df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
#         df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
#         columnas_esperadas = ['Potencia', 'Corriente', 'Energia', 'Movimiento', 'Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext', 'Estado_Luz_Ideal']
#         for col in columnas_esperadas:
#             if col not in df.columns:
#                 df[col] = 0.0

#         df['Potencia'] = pd.to_numeric(df['Potencia'], errors='coerce').fillna(0).astype('float32')
#         df['Corriente'] = pd.to_numeric(df['Corriente'], errors='coerce').fillna(0).astype('float32')
#         df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
#         df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce').fillna(0).astype('float32')
#         df['Humedad'] = pd.to_numeric(df['Humedad'], errors='coerce').fillna(0).astype('float32')
#         df['Iluminacion'] = pd.to_numeric(df['Iluminacion'], errors='coerce').fillna(0).astype('float32')
#         df['Temp_Ext'] = pd.to_numeric(df['Temp_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Hum_Ext'] = pd.to_numeric(df['Hum_Ext'], errors='coerce').fillna(0).astype('float32')
#         df['Estado_Luz_Ideal'] = pd.to_numeric(df['Estado_Luz_Ideal'], errors='coerce').fillna(0).astype('float32')
#         df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
#         df['Timestamp'] = pd.to_datetime(df['Timestamp'])
#         df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
#         df['Minuto'] = df['Timestamp'].dt.minute.astype('int8')
#         df['Calculo_Potencia_kWh'] = ((df['Potencia'] / 1000.0) * (60.0 / 3600.0)).astype('float32')
#         df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
#         return df

#     def _definir_periodo_cfe(self, ts):
#         dia = ts.weekday()
#         hora = ts.hour
#         if dia < 5:
#             if 0 <= hora < 7: return 'Base'
#             if 18 <= hora < 22: return 'Punta'
#             return 'Intermedia'
#         elif dia == 5:
#             if 0 <= hora < 7: return 'Base'
#             return 'Intermedia'
#         else:
#             if 0 <= hora < 19: return 'Base'
#             return 'Intermedia'

#     def _calcular_matriz_correlacion(self, df: pd.DataFrame) -> dict:
#         variables = ['Temperatura', 'Humedad', 'Iluminacion', 'Temp_Ext', 'Hum_Ext', 'Estado_Luz_Ideal']
#         correlaciones = {}
#         var_potencia = df['Potencia'].var() if not df.empty else 0.0
        
#         for var in variables:
#             if var in df.columns and var_potencia > 0 and df[var].var() > 0:
#                 corr, _ = stats.pearsonr(df[var], df['Potencia'])
#                 correlaciones[var.lower()] = round(float(corr), 3)
#             else:
#                 correlaciones[var.lower()] = 0.0
#         return correlaciones

#     def generar_analisis_individual(self, dispositivo_id: int, df: pd.DataFrame, factor_norm: float):
#         if df.empty:
#             return {'error': 'No hay datos para este dispositivo'}

#         df['Fecha_Corta'] = df['Timestamp'].dt.date
#         dias_totales = df['Fecha_Corta'].nunique()
#         df['Fecha_Corta_Str'] = df['Fecha_Corta'].astype(str)

#         energia_periodo = df.groupby('Periodo_CFE')['Calculo_Potencia_kWh'].sum() * factor_norm
#         consumo_normalizado = energia_periodo.sum()
#         promedio_diario = consumo_normalizado / dias_totales if dias_totales > 0 else 0
#         consumo_bruto = df['Calculo_Potencia_kWh'].sum()

#         costo_total = consumo_normalizado * self.factor_costo_kwh

#         registros_totales = len(df)
#         registros_activos = (df['Movimiento'] > 0).sum()
#         porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

#         mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
#         inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Potencia'] > 15)]
#         energia_desperdiciada = inactividad_total['Calculo_Potencia_kWh'].sum() * factor_norm

#         corriente_watts = df['Potencia'].max()
        
#         var_potencia = df['Potencia'].var()
#         corr_pir = 0.0
#         if var_potencia > 0:
#             corr_pir, _ = stats.pearsonr(df['Movimiento'], df['Potencia'])

#         temp_promedio = df['Temperatura'].mean()
#         hum_promedio = df['Humedad'].mean()

#         perfil_horario = df.groupby('Hora_Int')['Potencia'].mean().round(2).to_dict()
#         perfil_demanda_watts = [float(perfil_horario.get(h, 0.0)) for h in range(24)]

#         consumo_horario_kwh = (df.groupby('Hora_Int')['Calculo_Potencia_kWh'].sum() * factor_norm).round(2).to_dict()
#         grafica_consumo_hora = [float(consumo_horario_kwh.get(h, 0.0)) for h in range(24)]

#         agrupado_diario = df.groupby('Fecha_Corta_Str').agg(
#             kwh_total=('Calculo_Potencia_kWh', 'sum'),
#             temp_prom=('Temperatura', 'mean'),
#             hum_prom=('Humedad', 'mean')
#         ).reset_index()

#         tendencia_datos = []
#         for _, row in agrupado_diario.iterrows():
#             tendencia_datos.append({
#                 "fecha": row['Fecha_Corta_Str'],
#                 "kwh": round(float(row['kwh_total'] * factor_norm), 2),
#                 "temperatura": round(float(row['temp_prom']), 2),
#                 "humedad": round(float(row['hum_prom']), 2)
#             })

#         correlaciones_mes = self._calcular_matriz_correlacion(df)
        
#         dia_tipico_str = "N/A"
#         correlaciones_dia = {}
#         consumo_por_dia = df.groupby('Fecha_Corta_Str')['Calculo_Potencia_kWh'].sum()
        
#         if not consumo_por_dia.empty:
#             promedio_bruto = consumo_bruto / dias_totales if dias_totales > 0 else 0
#             diferencias = (consumo_por_dia - promedio_bruto).abs()
#             dia_tipico_str = diferencias.idxmin()
#             df_dia_tipico = df[df['Fecha_Corta_Str'] == dia_tipico_str]
#             correlaciones_dia = self._calcular_matriz_correlacion(df_dia_tipico)

#         return {
#             'dispositivo_id': int(dispositivo_id),
#             'consumo_bruto_kwh': round(float(consumo_bruto), 2),
#             'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
#             'promedio_diario': round(float(promedio_diario), 2),
#             'temperatura_promedio': round(float(temp_promedio), 2),
#             'humedad_promedio': round(float(hum_promedio), 2),
#             'desglose_cfe': {
#                 'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
#                 'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
#                 'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
#             },
#             'costo_estimado_mxn': round(float(costo_total), 2),
#             'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
#             'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
#             'corriente_maxima_watts': round(float(corriente_watts), 2),
#             'correlacion_pir_potencia': round(float(corr_pir), 2),
#             'grafica_perfil_demanda': perfil_demanda_watts,
#             'grafica_consumo_por_hora': grafica_consumo_hora,
#             'grafica_tendencia_diaria': tendencia_datos,
#             'correlaciones_ambientales': {
#                 'mes_completo': correlaciones_mes,
#                 'dia_tipico': {
#                     'fecha': dia_tipico_str,
#                     'valores': correlaciones_dia
#                 }
#             }
#         }

#     def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
#         df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
#         df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)

#         errores = []
#         if df_base.empty:
#             errores.append(f'Base ID {id_base} sin datos')
#         if df_ctrl.empty:
#             errores.append(f'Control ID {id_ctrl} sin datos')

#         if errores:
#             return {'error': ' | '.join(errores)}

#         df_base['Fecha_Corta'] = df_base['Timestamp'].dt.date
#         df_ctrl['Fecha_Corta'] = df_ctrl['Timestamp'].dt.date

#         dias_base = df_base['Fecha_Corta'].nunique()
#         dias_ctrl = df_ctrl['Fecha_Corta'].nunique()

#         factor_norm = dias_base / dias_ctrl if dias_ctrl > 0 else 1.0

#         res_base = self.generar_analisis_individual(id_base, df_base, 1.0)
#         res_ctrl = self.generar_analisis_individual(id_ctrl, df_ctrl, factor_norm)

#         ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
#         ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
        
#         diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

#         ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
#         ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

#         desperdicio_base = res_base['carga_fantasma_kwh']
#         desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']
#         mitigacion_desperdicio = 100.0
#         if desperdicio_base > 0:
#             mitigacion_desperdicio = ((desperdicio_base - desperdicio_ctrl) / desperdicio_base) * 100.0

#         diferencia_temp = res_base['temperatura_promedio'] - res_ctrl['temperatura_promedio']
#         diferencia_hum = res_base['humedad_promedio'] - res_ctrl['humedad_promedio']

#         f_stat = 0.0
#         p_val = 1.0
#         if df_base['Potencia'].var() > 0 and df_ctrl['Potencia'].var() > 0:
#             f_stat, p_val = stats.f_oneway(df_base['Potencia'], df_ctrl['Potencia'])

#         return {
#             "status": "success",
#             "data": {
#                 "dispositivo_base": res_base,
#                 "dispositivo_control": res_ctrl,
#                 "comparativa": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "eliminacion_desperdicio_pct": round(float(mitigacion_desperdicio), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "diferencia_temperatura": round(float(diferencia_temp), 2),
#                     "diferencia_humedad": round(float(diferencia_hum), 2),
#                     "estadistica_anova": {
#                         "f_stat": round(float(f_stat), 2),
#                         "p_valor": float(p_val)
#                     }
#                 }
#             }
#         }



#version 1.0 - 2026-05-10 12:30 funciona correctamente 
# import pandas as pd
# import numpy as np
# from scipy import stats
# from app.servicios.servicio_simulacion import get_db_connection
# import gc
# from app.configuracion import configuracion
# import pymysql

# class MotorAnalisisEnergetico:
#     def __init__(self):
#         self.factor_costo_kwh = 3.75

#     def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
#         conexion = get_db_connection()
#         try:
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
#                 query_campos = """
#                     SELECT cs.id, cs.nombre 
#                     FROM campos_sensores cs
#                     JOIN sensores s ON cs.sensor_id = s.id
#                     WHERE s.dispositivo_id = %s
#                 """
#                 cursor_campos.execute(query_campos, (dispositivo_id,))
#                 campos = cursor_campos.fetchall()

#             if not campos:
#                 return pd.DataFrame()

#             campo_ids = [c['id'] for c in campos]
#             mapa_nombres = {c['id']: c['nombre'] for c in campos}
#             format_strings = ','.join(['%s'] * len(campo_ids))
            
#             query_valores = f"""
#                 SELECT 
#                     timestamp_minuto as Timestamp, 
#                     campo_id, 
#                     valor_avg as valor,
#                     valor_texto
#                 FROM valores_agregados_minuto 
#                 WHERE campo_id IN ({format_strings})
#                   AND timestamp_minuto >= %s 
#                   AND timestamp_minuto <= %s
#             """
#             parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
#                 cursor_valores.execute(query_valores, parametros)
#                 resultados = cursor_valores.fetchall()

#         finally:
#             conexion.close()

#         if not resultados:
#             return pd.DataFrame()

#         df_raw = pd.DataFrame(resultados)
#         df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
#         df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
#         columnas_esperadas = ['Potencia', 'Corriente', 'Energia', 'Movimiento', 'Temperatura', 'Humedad']
#         for col in columnas_esperadas:
#             if col not in df.columns:
#                 df[col] = 0.0

#         df['Potencia'] = pd.to_numeric(df['Potencia'], errors='coerce').fillna(0).astype('float32')
#         df['Corriente'] = pd.to_numeric(df['Corriente'], errors='coerce').fillna(0).astype('float32')
#         df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
#         df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce').fillna(0).astype('float32')
#         df['Humedad'] = pd.to_numeric(df['Humedad'], errors='coerce').fillna(0).astype('float32')
#         df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
#         df['Timestamp'] = pd.to_datetime(df['Timestamp'])
#         df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
#         df['Minuto'] = df['Timestamp'].dt.minute.astype('int8')
#         df['Calculo_Potencia_kWh'] = ((df['Potencia'] / 1000.0) * (60.0 / 3600.0)).astype('float32')
#         df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
#         return df

#     def _definir_periodo_cfe(self, ts):
#         dia = ts.weekday()
#         hora = ts.hour
#         if dia < 5:
#             if 0 <= hora < 7: return 'Base'
#             if 18 <= hora < 22: return 'Punta'
#             return 'Intermedia'
#         elif dia == 5:
#             if 0 <= hora < 7: return 'Base'
#             return 'Intermedia'
#         else:
#             if 0 <= hora < 19: return 'Base'
#             return 'Intermedia'

#     def generar_analisis_individual(self, dispositivo_id: int, df: pd.DataFrame, factor_norm: float):
#         if df.empty:
#             return {'error': 'No hay datos para este dispositivo'}

#         df['Fecha_Corta'] = df['Timestamp'].dt.date
#         dias_totales = df['Fecha_Corta'].nunique()
#         df['Fecha_Corta_Str'] = df['Fecha_Corta'].astype(str)

#         energia_periodo = df.groupby('Periodo_CFE')['Calculo_Potencia_kWh'].sum() * factor_norm
#         consumo_normalizado = energia_periodo.sum()
#         promedio_diario = consumo_normalizado / dias_totales if dias_totales > 0 else 0
#         consumo_bruto = df['Calculo_Potencia_kWh'].sum()

#         costo_total = consumo_normalizado * self.factor_costo_kwh

#         registros_totales = len(df)
#         registros_activos = (df['Movimiento'] > 0).sum()
#         porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

#         mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
#         inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Potencia'] > 15)]
#         energia_desperdiciada = inactividad_total['Calculo_Potencia_kWh'].sum() * factor_norm

#         corriente_watts = df['Potencia'].max()
        
#         var_potencia = df['Potencia'].var()
#         corr_pir = 0.0
#         if var_potencia > 0:
#             corr_pir, _ = stats.pearsonr(df['Movimiento'], df['Potencia'])

#         temp_promedio = df['Temperatura'].mean()
#         hum_promedio = df['Humedad'].mean()

#         perfil_horario = df.groupby('Hora_Int')['Potencia'].mean().round(2).to_dict()
#         perfil_demanda_watts = [float(perfil_horario.get(h, 0.0)) for h in range(24)]

#         consumo_horario_kwh = (df.groupby('Hora_Int')['Calculo_Potencia_kWh'].sum() * factor_norm).round(2).to_dict()
#         grafica_consumo_hora = [float(consumo_horario_kwh.get(h, 0.0)) for h in range(24)]

#         agrupado_diario = df.groupby('Fecha_Corta_Str').agg(
#             kwh_total=('Calculo_Potencia_kWh', 'sum'),
#             temp_prom=('Temperatura', 'mean'),
#             hum_prom=('Humedad', 'mean')
#         ).reset_index()

#         tendencia_datos = []
#         for _, row in agrupado_diario.iterrows():
#             tendencia_datos.append({
#                 "fecha": row['Fecha_Corta_Str'],
#                 "kwh": round(float(row['kwh_total'] * factor_norm), 2),
#                 "temperatura": round(float(row['temp_prom']), 2),
#                 "humedad": round(float(row['hum_prom']), 2)
#             })

#         return {
#             'dispositivo_id': int(dispositivo_id),
#             'consumo_bruto_kwh': round(float(consumo_bruto), 2),
#             'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
#             'promedio_diario': round(float(promedio_diario), 2),
#             'temperatura_promedio': round(float(temp_promedio), 2),
#             'humedad_promedio': round(float(hum_promedio), 2),
#             'desglose_cfe': {
#                 'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
#                 'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
#                 'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
#             },
#             'costo_estimado_mxn': round(float(costo_total), 2),
#             'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
#             'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
#             'corriente_maxima_watts': round(float(corriente_watts), 2),
#             'correlacion_pir_potencia': round(float(corr_pir), 2),
#             'grafica_perfil_demanda': perfil_demanda_watts,
#             'grafica_consumo_por_hora': grafica_consumo_hora,
#             'grafica_tendencia_diaria': tendencia_datos
#         }

#     def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
#         df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
#         df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)

#         errores = []
#         if df_base.empty:
#             errores.append(f'Base ID {id_base} sin datos')
#         if df_ctrl.empty:
#             errores.append(f'Control ID {id_ctrl} sin datos')

#         if errores:
#             return {'error': ' | '.join(errores)}

#         df_base['Fecha_Corta'] = df_base['Timestamp'].dt.date
#         df_ctrl['Fecha_Corta'] = df_ctrl['Timestamp'].dt.date

#         dias_base = df_base['Fecha_Corta'].nunique()
#         dias_ctrl = df_ctrl['Fecha_Corta'].nunique()

#         factor_norm = dias_base / dias_ctrl if dias_ctrl > 0 else 1.0

#         res_base = self.generar_analisis_individual(id_base, df_base, 1.0)
#         res_ctrl = self.generar_analisis_individual(id_ctrl, df_ctrl, factor_norm)

#         ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
#         ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
        
#         diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

#         ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
#         ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

#         desperdicio_base = res_base['carga_fantasma_kwh']
#         desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']
#         mitigacion_desperdicio = 100.0
#         if desperdicio_base > 0:
#             mitigacion_desperdicio = ((desperdicio_base - desperdicio_ctrl) / desperdicio_base) * 100.0

#         diferencia_temp = res_base['temperatura_promedio'] - res_ctrl['temperatura_promedio']
#         diferencia_hum = res_base['humedad_promedio'] - res_ctrl['humedad_promedio']

#         f_stat = 0.0
#         p_val = 1.0
#         if df_base['Potencia'].var() > 0 and df_ctrl['Potencia'].var() > 0:
#             f_stat, p_val = stats.f_oneway(df_base['Potencia'], df_ctrl['Potencia'])

#         return {
#             "status": "success",
#             "data": {
#                 "dispositivo_base": res_base,
#                 "dispositivo_control": res_ctrl,
#                 "comparativa": {
#                     "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
#                     "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
#                     "diferencia_bruta_kwh": round(float(diferencia_bruta), 2),
#                     "eliminacion_desperdicio_pct": round(float(mitigacion_desperdicio), 2),
#                     "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
#                     "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
#                     "diferencia_temperatura": round(float(diferencia_temp), 2),
#                     "diferencia_humedad": round(float(diferencia_hum), 2),
#                     "estadistica_anova": {
#                         "f_stat": round(float(f_stat), 2),
#                         "p_valor": float(p_val)
#                     }
#                 },
#                 "metodologia": {
#                     "costo_estimado": "El algoritmo multiplica el consumo total de cada salon por un factor ponderado de 3.75 pesos por kilowatt hora. Este numero incluye la proporcion justa del costo de energia base, intermedia y punta, asi como el porcentaje correspondiente a los cargos fijos y la demanda maxima compartida del campus.",
#                     "normalizacion": "Los datos se ajustan matematicamente segun los dias exactos de medicion de cada equipo. Esto garantiza una comparativa justa independientemente de la duracion del mes analizado.",
#                     "fuga_energetica": "El filtro de inactividad detecta fallas al identificar potencias superiores a 15 watts cuando el sensor indica cero ocupantes fuera del horario oficial."
#                 }
#             }
#         }
# import pandas as pd
# import numpy as np
# from scipy import stats
# from app.servicios.servicio_simulacion import get_db_connection
# import gc
# from app.configuracion import configuracion

# import pymysql

# class MotorAnalisisEnergetico:
#     def __init__(self):
#         # Tarifas CFE (puedes moverlas a la base de datos después)
#         self.tarifa = {
#             'cargo_fijo': 421.57,
#             'distribucion': 94.61,
#             'capacidad': 435.42,
#             'energia': {'Base': 1.3527, 'Intermedia': 2.2898, 'Punta': 2.5573}
#         }

#     def _obtener_dataframe_dispositivo(self, dispositivo_id: int, fecha_inicio: str, fecha_fin: str) -> pd.DataFrame:
#         conexion = get_db_connection()
#         try:
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_campos:
#                 query_campos = """
#                     SELECT cs.id, cs.nombre 
#                     FROM campos_sensores cs
#                     JOIN sensores s ON cs.sensor_id = s.id
#                     WHERE s.dispositivo_id = %s
#                 """
#                 cursor_campos.execute(query_campos, (dispositivo_id,))
#                 campos = cursor_campos.fetchall()

#             if not campos:
#                 return pd.DataFrame()

#             campo_ids = [c['id'] for c in campos]
#             mapa_nombres = {c['id']: c['nombre'] for c in campos}
#             format_strings = ','.join(['%s'] * len(campo_ids))
            
#             query_valores = f"""
#                 SELECT 
#                     timestamp_minuto as Timestamp, 
#                     campo_id, 
#                     valor_avg as valor,
#                     valor_texto
#                 FROM valores_agregados_minuto 
#                 WHERE campo_id IN ({format_strings})
#                   AND timestamp_minuto >= %s 
#                   AND timestamp_minuto <= %s
#             """
#             parametros = tuple(campo_ids) + (fecha_inicio, fecha_fin)
            
#             with conexion.cursor(pymysql.cursors.DictCursor) as cursor_valores:
#                 cursor_valores.execute(query_valores, parametros)
#                 resultados = cursor_valores.fetchall()

#         finally:
#             conexion.close()

#         if not resultados:
#             return pd.DataFrame()

#         df_raw = pd.DataFrame(resultados)
        
#         df_raw['parametro'] = df_raw['campo_id'].map(mapa_nombres)
        
#         df = df_raw.pivot_table(index='Timestamp', columns='parametro', values='valor', aggfunc='first').reset_index()
        
#         columnas_esperadas = ['Potencia', 'Corriente', 'Energia', 'Movimiento']
#         for col in columnas_esperadas:
#             if col not in df.columns:
#                 df[col] = 0.0

#         df['Potencia'] = pd.to_numeric(df['Potencia'], errors='coerce').fillna(0).astype('float32')
#         df['Corriente'] = pd.to_numeric(df['Corriente'], errors='coerce').fillna(0).astype('float32')
#         df['Energia'] = pd.to_numeric(df['Energia'], errors='coerce').fillna(0).astype('float32')
        
#         df['Movimiento'] = (pd.to_numeric(df['Movimiento'], errors='coerce').fillna(0) > 0).astype('int8')
        
#         df['Timestamp'] = pd.to_datetime(df['Timestamp'])
#         df['Hora_Int'] = df['Timestamp'].dt.hour.astype('int8')
#         df['Minuto'] = df['Timestamp'].dt.minute.astype('int8')
        
#         df['Calculo_Potencia_kWh'] = ((df['Potencia'] / 1000) * (60 / 3600)).astype('float32')
        
#         df['Periodo_CFE'] = df['Timestamp'].apply(self._definir_periodo_cfe).astype('category')
        
#         return df

#     def _definir_periodo_cfe(self, ts):
#         dia = ts.weekday()
#         hora = ts.hour
#         if dia < 5:
#             if 0 <= hora < 7: return 'Base'
#             if 18 <= hora < 22: return 'Punta'
#             return 'Intermedia'
#         elif dia == 5:
#             if 0 <= hora < 7: return 'Base'
#             return 'Intermedia'
#         else:
#             if 0 <= hora < 19: return 'Base'
#             return 'Intermedia'


    
#     def generar_analisis_individual(self, dispositivo_id: int, fecha_ini: str, fecha_fin: str, dias_totales: int, dias_mes_oficial: int = 30):
#         df = self._obtener_dataframe_dispositivo(dispositivo_id, fecha_ini, fecha_fin)
#         if df.empty:
#             return {'error': 'No hay datos para este dispositivo'}

#         energia_periodo = df.groupby('Periodo_CFE')['Calculo_Potencia_kWh'].sum()
#         consumo_bruto = energia_periodo.sum()

#         factor_normalizacion = dias_mes_oficial / dias_totales if dias_totales > 0 else 1.0
#         consumo_normalizado = consumo_bruto * factor_normalizacion
#         promedio_diario = consumo_normalizado / dias_mes_oficial

#         df_indexado = df.set_index('Timestamp')
#         demanda_1h = df_indexado['Calculo_Potencia_kWh'].resample('1h').sum()
#         demanda_total = demanda_1h.max() if not demanda_1h.empty else 0.0

#         df_punta = df[df['Periodo_CFE'] == 'Punta']
#         demanda_punta = df_punta.set_index('Timestamp')['Calculo_Potencia_kWh'].resample('1h').sum().max() if not df_punta.empty else 0.0

#         precios = self.tarifa['energia']
#         costo_energia = sum(energia_periodo.get(p, 0) * precios[p] for p in precios)
#         costo_total = self.tarifa['cargo_fijo'] + costo_energia + (demanda_total * self.tarifa['distribucion']) + (demanda_punta * self.tarifa['capacidad'])

#         registros_totales = len(df)
#         registros_activos = (df['Movimiento'] > 0).sum()
#         porcentaje_ocupacion = (registros_activos / registros_totales) * 100.0 if registros_totales > 0 else 0.0

#         mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
#         inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Potencia'] > 15)]
#         energia_desperdiciada = inactividad_total['Calculo_Potencia_kWh'].sum()

#         corriente_watts = df['Potencia'].max()
#         corr_pir, p_val = stats.pearsonr(df['Movimiento'], df['Potencia']) if df['Potencia'].var() > 0 else (0.0, 1.0)
        
#         # Generar datos para la gráfica de Perfil de Demanda Térmica (Promedio de Watts por hora 0-23)
#         perfil_horario = df.groupby('Hora_Int')['Potencia'].mean().round(2).to_dict()
#         perfil_demanda_watts = [float(perfil_horario.get(h, 0.0)) for h in range(24)]

#         # Generar datos para la gráfica de Tendencia de Consumo (Suma de kWh por día)
#         df['Fecha_Corta'] = df['Timestamp'].dt.date
#         tendencia_diaria = df.groupby('Fecha_Corta')['Calculo_Potencia_kWh'].sum().round(2).to_dict()
#         tendencia_consumo_kwh = [{'fecha': str(k), 'kwh': float(v)} for k, v in tendencia_diaria.items()]
        
        
#         return {
#             'dispositivo_id': int(dispositivo_id),
#             'consumo_bruto_kwh': round(float(consumo_bruto), 2),
#             'consumo_normalizado_kwh': round(float(consumo_normalizado), 2),
#             'promedio_diario': round(float(promedio_diario), 2),
#             'desglose_cfe': {
#                 'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
#                 'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
#                 'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
#             },
#             'costo_estimado_mxn': round(float(costo_total), 2),
#             'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
#             'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
#             'corriente_maxima_watts': round(float(corriente_watts), 2),
#             'correlacion_pir_potencia': round(float(corr_pir), 2),
#             'grafica_perfil_demanda': perfil_demanda_watts,
#             'grafica_tendencia_diaria': tendencia_consumo_kwh
#         }


#     def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
#             res_base = self.generar_analisis_individual(id_base, fecha_ini, fecha_fin, 31)
#             res_ctrl = self.generar_analisis_individual(id_ctrl, fecha_ini, fecha_fin, 31)

#             errores = []
#             if 'error' in res_base:
#                 errores.append(f'Base ID {id_base} sin datos')
#             if 'error' in res_ctrl:
#                 errores.append(f'Control ID {id_ctrl} sin datos')

#             if errores:
#                 return {'error': ' | '.join(errores)}

#             ahorro_kwh = res_base['consumo_normalizado_kwh'] - res_ctrl['consumo_normalizado_kwh']
#             ahorro_kwh_pct = (ahorro_kwh / res_base['consumo_normalizado_kwh']) * 100.0 if res_base['consumo_normalizado_kwh'] > 0 else 0.0
            
#             diferencia_bruta = res_base['consumo_bruto_kwh'] - res_ctrl['consumo_bruto_kwh']

#             ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
#             ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100.0 if res_base['costo_estimado_mxn'] > 0 else 0.0

#             desperdicio_base = res_base['carga_fantasma_kwh']
#             desperdicio_ctrl = res_ctrl['carga_fantasma_kwh']
#             mitigacion_desperdicio = 100.0
#             if desperdicio_base > 0:
#                 mitigacion_desperdicio = ((desperdicio_base - desperdicio_ctrl) / desperdicio_base) * 100.0

#             df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
#             df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)
#             f_stat, p_val = stats.f_oneway(df_base['Potencia'], df_ctrl['Potencia'])

#             return {
#                 'dispositivo_base': res_base,
#                 'dispositivo_control': res_ctrl,
#                 'comparativa': {
#                     'ahorro_energia_kwh': round(float(ahorro_kwh), 2),
#                     'ahorro_energia_pct': round(float(ahorro_kwh_pct), 2),
#                     'diferencia_bruta_kwh': round(float(diferencia_bruta), 2),
#                     'eliminacion_desperdicio_pct': round(float(mitigacion_desperdicio), 2),
#                     'ahorro_financiero_mxn': round(float(ahorro_mxn), 2),
#                     'ahorro_financiero_pct': round(float(ahorro_mxn_pct), 2),
#                     'estadistica_anova': {
#                         'f_stat': round(float(f_stat), 2),
#                         'p_valor': float(p_val)
#                     }
#                 }
#             }



    # def generar_analisis_individual(self, dispositivo_id: int, fecha_ini: str, fecha_fin: str, dias_totales: int):
    #     df = self._obtener_dataframe_dispositivo(dispositivo_id, fecha_ini, fecha_fin)
    #     if df.empty:
    #         return {"error": "No hay datos para este dispositivo en el rango seleccionado"}

    #     energia_periodo = df.groupby('Periodo_CFE')['Calculo_Potencia_kWh'].sum()
    #     energia_total = energia_periodo.sum()
    #     promedio_diario = energia_total / dias_totales if dias_totales > 0 else 0
        
    #     df_indexado = df.set_index('Timestamp')
    #     demanda_1h = df_indexado['Calculo_Potencia_kWh'].resample('1h').sum()
    #     demanda_total = demanda_1h.max() if not demanda_1h.empty else 0.0

    #     df_punta = df[df['Periodo_CFE'] == 'Punta']
    #     demanda_punta = df_punta.set_index('Timestamp')['Calculo_Potencia_kWh'].resample('1h').sum().max() if not df_punta.empty else 0.0

    #     precios = self.tarifa['energia']
    #     costo_energia = sum(energia_periodo.get(p, 0) * precios[p] for p in precios)
    #     costo_total = self.tarifa['cargo_fijo'] + costo_energia + (demanda_total * self.tarifa['distribucion']) + (demanda_punta * self.tarifa['capacidad'])

    #     registros_totales = len(df)
    #     registros_activos = (df['Movimiento'] > 0).sum()
    #     porcentaje_ocupacion = (registros_activos / registros_totales) * 100 if registros_totales > 0 else 0

    #     # Lógica de carga fantasma simplificada (fuera de horario 7am-10pm sin movimiento)
    #     mask_fuera_horario = (df['Hora_Int'] < 7) | (df['Hora_Int'] >= 22)
    #     inactividad_total = df[mask_fuera_horario & (df['Movimiento'] == 0) & (df['Potencia'] > 100)]
    #     energia_desperdiciada = inactividad_total['Calculo_Potencia_kWh'].sum()

    #     corriente_watts = df['Potencia'].max()
    #     corr_pir, p_val = stats.pearsonr(df['Movimiento'], df['Potencia']) if df['Potencia'].var() > 0 else (0, 1)

    #     return {
    #         'dispositivo_id': int(dispositivo_id),
    #         'potencia_kwh_total': round(float(energia_total), 2),
    #         'promedio_diario': round(float(promedio_diario), 2),
    #         'desglose_cfe': {
    #             'energia_base': round(float(energia_periodo.get('Base', 0)), 2),
    #             'energia_intermedia': round(float(energia_periodo.get('Intermedia', 0)), 2),
    #             'energia_punta': round(float(energia_periodo.get('Punta', 0)), 2),
    #         },
    #         'costo_estimado_mxn': round(float(costo_total), 2),
    #         'porcentaje_ocupacion': round(float(porcentaje_ocupacion), 2),
    #         'carga_fantasma_kwh': round(float(energia_desperdiciada), 2),
    #         'pico_demanda_watts': round(float(corriente_watts), 2),
    #         'correlacion_pir_potencia': round(float(corr_pir), 2)
    #     }
    



    # def generar_analisis_comparativo(self, id_base: int, id_ctrl: int, fecha_ini: str, fecha_fin: str):
    #     res_base = self.generar_analisis_individual(id_base, fecha_ini, fecha_fin, 30)
    #     res_ctrl = self.generar_analisis_individual(id_ctrl, fecha_ini, fecha_fin, 30)

    #     errores = []
    #     if "error" in res_base:
    #         errores.append(f"Base ID {id_base}: {res_base['error']}")
    #     if "error" in res_ctrl:
    #         errores.append(f"Control ID {id_ctrl}: {res_ctrl['error']}")

    #     if errores:
    #         return {"error": " | ".join(errores)}

    #     ahorro_kwh = res_base['potencia_kwh_total'] - res_ctrl['potencia_kwh_total']
    #     ahorro_kwh_pct = (ahorro_kwh / res_base['potencia_kwh_total']) * 100 if res_base['potencia_kwh_total'] > 0 else 0
        
    #     ahorro_mxn = res_base['costo_estimado_mxn'] - res_ctrl['costo_estimado_mxn']
    #     ahorro_mxn_pct = (ahorro_mxn / res_base['costo_estimado_mxn']) * 100 if res_base['costo_estimado_mxn'] > 0 else 0

    #     df_base = self._obtener_dataframe_dispositivo(id_base, fecha_ini, fecha_fin)
    #     df_ctrl = self._obtener_dataframe_dispositivo(id_ctrl, fecha_ini, fecha_fin)
    #     f_stat, p_val = stats.f_oneway(df_base['Potencia'], df_ctrl['Potencia'])

    #     return {
    #         "dispositivo_base": res_base,
    #         "dispositivo_control": res_ctrl,
    #         "comparativa": {
    #             "ahorro_energia_kwh": round(float(ahorro_kwh), 2),
    #             "ahorro_energia_pct": round(float(ahorro_kwh_pct), 2),
    #             "ahorro_financiero_mxn": round(float(ahorro_mxn), 2),
    #             "ahorro_financiero_pct": round(float(ahorro_mxn_pct), 2),
    #             "estadistica_anova": {
    #                 "f_stat": round(float(f_stat), 2),
    #                 "p_valor": float(p_val)
    #             }
    #         }
    #     }
        
        