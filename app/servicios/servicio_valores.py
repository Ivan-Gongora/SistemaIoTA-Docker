import pymysql
import math
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.servicios.servicio_simulacion import get_db_connection, simular_datos_json

# -----------------------------------------------------------------------------
# 1. OBTENER ÚLTIMO VALOR (POLLING 5s)
# -----------------------------------------------------------------------------
async def obtener_ultimo_valor_db(campo_id: int) -> Optional[Dict[str, Any]]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
        SELECT 
            uv.campo_id,
            uv.ultimo_valor AS valor,
            uv.fecha AS fecha_hora_lectura,
            cs.nombre AS nombre_campo,
            um.magnitud_tipo,
            um.simbolo AS simbolo_unidad
        FROM ultimo_valor_campo uv
        INNER JOIN campos_sensores cs ON uv.campo_id = cs.id
        LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
        WHERE uv.campo_id = %s;
        """
        cursor.execute(sql, (campo_id,))
        resultado = cursor.fetchone()

        if resultado:
            return resultado
            
        return await _fallback_ultimo_valor_maestro(campo_id)

    except Exception as e:
        print(f"❌ [DB Error] obtener_ultimo_valor: {e}")
        return await _fallback_ultimo_valor_maestro(campo_id)
    finally:
        if conn: conn.close()

async def _fallback_ultimo_valor_maestro(campo_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        sql = """
        SELECT v.campo_id, v.valor, v.fecha_hora_lectura, 
               cs.nombre AS nombre_campo, um.magnitud_tipo, um.simbolo AS simbolo_unidad
        FROM valores v
        JOIN campos_sensores cs ON v.campo_id = cs.id
        LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
        WHERE v.campo_id = %s
        ORDER BY v.fecha_hora_lectura DESC LIMIT 1
        """
        cursor.execute(sql, (campo_id,))
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        if conn: conn.close()

# # -----------------------------------------------------------------------------
# #  MOTOR DE ANÁLISIS 1: INDIVIDUAL (Tiempo Real / Polling)
# # -----------------------------------------------------------------------------
# async def detectar_anomalia_individual(campo_id: int, valor_actual: float) -> tuple[bool, Optional[str]]:
#     """
#     Detecta anomalías comparando con la historia reciente.
#     """
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # 300 registros ~ 25 minutos (a 5s/dato). Suficiente para ver la tendencia reciente.
#         sql = """
#         SELECT v.valor, cs.nombre, cs.tipo_valor 
#         FROM valores v 
#         JOIN campos_sensores cs ON v.campo_id = cs.id
#         WHERE v.campo_id = %s 
#         ORDER BY v.fecha_hora_lectura DESC 
#         LIMIT 300
#         """
#         cursor.execute(sql, (campo_id,))
#         rows = cursor.fetchall()
        
#         if not rows or len(rows) < 20:
#             return False, None 

#         # Detección de Tipo
#         tipo = (rows[0].get('tipo_valor') or '').lower()
#         nombre = (rows[0].get('nombre') or '').lower()
#         es_movimiento = 'bool' in tipo or 'movimiento' in nombre or 'estado' in nombre

#         # --- RAMA A: ANÁLISIS DE MOVIMIENTO (FRECUENCIA ADAPTATIVA) ---
#         if es_movimiento:
#             # Ventana "Ahora" (Último minuto ~ 12 registros)
#             ventana_reciente = rows[:12]
#             actividad_actual = sum(float(r['valor']) for r in ventana_reciente) # Suma de 1s
            
#             # Ventana "Base" (Los 24 minutos anteriores)
#             historia_base = rows[12:]
            
#             # Calculamos el promedio de actividad por minuto en el pasado
#             # Agrupamos en bloques de 12 (1 min)
#             bloques = [historia_base[i:i + 12] for i in range(0, len(historia_base), 12)]
#             sumas_bloques = [sum(float(r['valor']) for r in b) for b in bloques]
            
#             # Promedio histórico de eventos por minuto
#             promedio_actividad = sum(sumas_bloques) / len(sumas_bloques) if sumas_bloques else 0
            
#             # --- REGLAS DINÁMICAS ---
            
#             # Caso 1: Lugar Tranquilo (Promedio < 2 eventos/min)
#             if promedio_actividad < 2:
#                 # Si de repente hay mucha actividad (> 8 eventos/min), es anomalía clara.
#                 if actividad_actual > 8:
#                     return True, f"Actividad Inusual ({int(actividad_actual)} eventos/min vs normal bajo)"

#             # Caso 2: Lugar Concurrido (Promedio > 10 eventos/min)
#             elif promedio_actividad > 10:
#                 # Si la actividad se triplica (Fiesta/Multitud)
#                 if actividad_actual > (promedio_actividad * 3):
#                     return True, f"Pico de Tráfico ({int(actividad_actual)} eventos vs media {int(promedio_actividad)})"
#                 # Si la actividad cae a 0 de golpe (Fallo de sensor o cierre inesperado)
#                 # Solo si es 0 absoluto en el último minuto
#                 if actividad_actual == 0:
#                     return True, "Caída de Actividad (0 eventos detectados)"
            
#             # Caso 3: Intermedio (Regla general 3x)
#             else:
#                 if actividad_actual > (max(promedio_actividad, 2) * 3):
#                     return True, f"Alta Actividad ({int(actividad_actual)} eventos)"
            
#             return False, None

#         # --- RAMA B: ANÁLISIS NUMÉRICO (Z-SCORE) ---
#         else:
#             # Tomamos solo los últimos 60 para Z-Score (5 min) para que sea sensible
#             datos_z = rows[:60]
#             historial = [float(r['valor']) for r in datos_z]
            
#             ventana_reciente = historial[:3] 
#             valor_suavizado = sum(ventana_reciente) / len(ventana_reciente)
            
#             linea_base = historial[3:]
#             if not linea_base: return False, None

#             media_base = sum(linea_base) / len(linea_base)
#             varianza = sum([((x - media_base) ** 2) for x in linea_base]) / len(linea_base)
#             desviacion = math.sqrt(varianza)

#             if desviacion < 0.1: desviacion = 0.1

#             z_score = (valor_suavizado - media_base) / desviacion
#             UMBRAL = 3.0 

#             if abs(z_score) > UMBRAL:
#                 tipo_pico = "ALTO" if z_score > 0 else "BAJO"
#                 return True, f"Pico {tipo_pico} anómalo ({valor_suavizado:.1f})"
            
#             return False, None

#     except Exception as e:
#         print(f"⚠️ Error análisis realtime: {e}")
#         return False, None
#     finally:
#         if conn: conn.close()
async def detectar_anomalia_individual(campo_id: int, valor_actual: float) -> tuple[bool, Optional[str]]:
    """
    Detecta anomalías usando un enfoque adaptativo según el tipo de dato.
    Para Movimiento: Compara la actividad reciente contra el PROMEDIO HISTÓRICO del lugar.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 1. Contexto histórico ampliado (300 registros ~ 25 minutos)
        # Necesitamos suficiente historia para saber "qué es normal" en este lugar.
        sql = """
        SELECT v.valor, cs.nombre, cs.tipo_valor 
        FROM valores v 
        JOIN campos_sensores cs ON v.campo_id = cs.id
        WHERE v.campo_id = %s 
        ORDER BY v.fecha_hora_lectura DESC 
        LIMIT 300
        """
        cursor.execute(sql, (campo_id,))
        rows = cursor.fetchall()
        
        if not rows or len(rows) < 20:
            return False, None 

        # Detectar Tipo
        tipo = (rows[0].get('tipo_valor') or '').lower()
        nombre = (rows[0].get('nombre') or '').lower()
        es_movimiento = 'bool' in tipo or 'movimiento' in nombre or 'estado' in nombre

        # --- RAMA A: ANÁLISIS DE MOVIMIENTO (FACTOR DINÁMICO) ---
        if es_movimiento:
            # Ventana "Ahora" (Último minuto ~ 12 registros si polling=5s)
            ventana_reciente = rows[:12]
            actividad_actual = sum(float(r['valor']) for r in ventana_reciente) # Suma de 1s
            
            # Ventana "Base" (Los 24 minutos anteriores)
            historia_base = rows[12:]
            
            # Calculamos el "Factor de Movimiento Normal" (Eventos por minuto promedio)
            # Dividimos la historia en bloques de 1 minuto (12 registros)
            bloques = [historia_base[i:i + 12] for i in range(0, len(historia_base), 12)]
            sumas_bloques = [sum(float(r['valor']) for r in b) for b in bloques]
            
            # El promedio nos dice si este es un lugar "Quieto" (ej. 0.5) o "Movido" (ej. 20)
            factor_normal = sum(sumas_bloques) / len(sumas_bloques) if sumas_bloques else 0
            
            # --- REGLAS ADAPTATIVAS ---
            es_pico = False
            mensaje = ""

            # Escenario 1: Lugar Tranquilo (Factor < 2)
            # Aquí cualquier ráfaga es sospechosa.
            if factor_normal < 2:
                if actividad_actual >= 5: # Si de repente hay 5 eventos o más
                    es_pico = True
                    mensaje = f"Actividad Inusual ({int(actividad_actual)}/min vs normal bajo)"

            # Escenario 2: Lugar Concurrido (Factor > 10)
            # Aquí se necesita MUCHA actividad para que sea "pico".
            elif factor_normal > 10:
                if actividad_actual > (factor_normal * 2.5): # 2.5 veces lo normal
                    es_pico = True
                    mensaje = f"Pico de Tráfico ({int(actividad_actual)} vs media {int(factor_normal)})"
                
                # Detección de "Muerte Súbita" (Caída a 0 en lugar concurrido)
                if actividad_actual == 0:
                    es_pico = True
                    mensaje = "Caída de Actividad (0 eventos)"
            
            # Escenario 3: Lugar Promedio
            else:
                if actividad_actual > (max(factor_normal, 2) * 3): # Regla general 3x
                    es_pico = True
                    mensaje = f"Alta Actividad ({int(actividad_actual)} eventos)"

            if es_pico:
                return True, mensaje
            
            return False, None

        # --- RAMA B: ANÁLISIS NUMÉRICO (Z-SCORE) ---
        # (Se mantiene igual para temperatura, voltaje, etc.)
        else:
            datos_z = rows[:60] # Usamos 5 minutos para Z-Score
            historial = [float(r['valor']) for r in datos_z]
            
            ventana_reciente = historial[:3] 
            valor_suavizado = sum(ventana_reciente) / len(ventana_reciente)
            
            linea_base = historial[3:]
            media_base = sum(linea_base) / len(linea_base)
            varianza = sum([((x - media_base) ** 2) for x in linea_base]) / len(linea_base)
            desviacion = math.sqrt(varianza)

            if desviacion < 0.1: desviacion = 0.1

            z_score = (valor_suavizado - media_base) / desviacion
            UMBRAL = 3.0 

            if abs(z_score) > UMBRAL:
                tipo_pico = "ALTO" if z_score > 0 else "BAJO"
                return True, f"Pico {tipo_pico} anómalo ({valor_suavizado:.1f})"
            
            return False, None

    except Exception as e:
        print(f"⚠️ Error análisis realtime: {e}")
        return False, None
    finally:
        if conn: conn.close()


# -----------------------------------------------------------------------------
# 🧠 MOTOR DE ANÁLISIS 2: POR LOTES (Para Histórico/Carga Inicial)
# -----------------------------------------------------------------------------
def aplicar_analisis_anomalias(datos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not datos or len(datos) < 10: return datos

    es_movimiento = False
    if datos[0].get('nombre_campo'):
        nombre = datos[0]['nombre_campo'].lower()
        es_movimiento = 'movimiento' in nombre or 'estado' in nombre or 'puerta' in nombre

    if es_movimiento:
        # Análisis Adaptativo para Lotes
        valores = [float(d['valor']) for d in datos]
        media_total = sum(valores) / len(valores)
        
        # Definir umbral dinámico basado en la propia historia del lote
        if media_total < 1: 
            umbral_alto = 5 # Lugar tranquilo -> Pico bajo dispara alerta
        else:
            umbral_alto = media_total * 2.5 # Lugar activo -> Requiere pico más alto

        for d in datos:
            val = float(d['valor'])
            d['anomalia'] = False
            d['mensaje_alerta'] = None
            
            if val > umbral_alto: 
                d['anomalia'] = True
                d['mensaje_alerta'] = f"Pico de Actividad ({int(val)} eventos)"
    else:
        # Z-Score Estándar
        valores = [float(d['valor']) for d in datos]
        media = sum(valores) / len(valores)
        varianza = sum([((x - media) ** 2) for x in valores]) / len(valores)
        desviacion_std = math.sqrt(varianza)
        
        if desviacion_std < 0.01: desviacion_std = 0.01
        UMBRAL_Z = 2.8 

        for d in datos:
            val = float(d['valor'])
            z_score = (val - media) / desviacion_std
            d['anomalia'] = False
            d['mensaje_alerta'] = None

            if abs(z_score) > UMBRAL_Z:
                d['anomalia'] = True
                d['mensaje_alerta'] = f"Valor atípico: {val}"
    
    return datos


# def aplicar_analisis_anomalias(datos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """
#     Procesa un lote completo de datos (ej. las últimas 24h) para marcar picos pasados.
#     """
#     if not datos or len(datos) < 10: return datos

#     # Detectar tipo basado en el primer registro
#     es_movimiento = False
#     if datos[0].get('nombre_campo'):
#         nombre = datos[0]['nombre_campo'].lower()
#         es_movimiento = 'movimiento' in nombre or 'estado' in nombre or 'puerta' in nombre

#     if es_movimiento:
#         # Lógica para Movimiento en Lotes (Barras)
#         valores = [float(d['valor']) for d in datos]
#         media_total = sum(valores) / len(valores)
        
#         # Si el promedio general es muy bajo (poca actividad), cualquier ráfaga es anomalía.
#         umbral_actividad = max(media_total * 3, 5) # Mínimo 5 eventos para considerar alerta

#         for d in datos:
#             val = float(d['valor'])
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None
            
#             if val > umbral_actividad: 
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Pico de Actividad ({int(val)} eventos)"

#     else:
#         # Lógica Z-Score Estándar (Temperatura, etc.)
#         valores = [float(d['valor']) for d in datos]
#         media = sum(valores) / len(valores)
#         varianza = sum([((x - media) ** 2) for x in valores]) / len(valores)
#         desviacion_std = math.sqrt(varianza)
        
#         if desviacion_std < 0.01: desviacion_std = 0.01
#         UMBRAL_Z = 2.8 

#         for d in datos:
#             val = float(d['valor'])
#             z_score = (val - media) / desviacion_std
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None

#             if abs(z_score) > UMBRAL_Z:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Valor atípico: {val}"
    
#     return datos

# -----------------------------------------------------------------------------
# 2. VENTANA DE TIEMPO (Ancla en último dato)
# -----------------------------------------------------------------------------
async def obtener_valores_ventana_db(campo_id: int, minutos: int) -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql_ancla = "SELECT fecha FROM ultimo_valor_campo WHERE campo_id = %s"
        cursor.execute(sql_ancla, (campo_id,))
        res_ancla = cursor.fetchone()
        
        if not res_ancla:
            cursor.execute("SELECT MAX(fecha_hora_lectura) as fecha FROM valores WHERE campo_id = %s", (campo_id,))
            res_ancla = cursor.fetchone()
            
        if not res_ancla or not res_ancla['fecha']:
            return [] 

        fecha_fin = res_ancla['fecha']
        print(f"⏱️ [DB] Ventana {minutos} min. Ancla: {fecha_fin}")

        sql = """
        SELECT * FROM (
            SELECT 
                v.valor, 
                v.fecha_hora_lectura,
                um.magnitud_tipo,
                um.simbolo AS simbolo_unidad,
                cs.nombre AS nombre_campo
            FROM valores v
            JOIN campos_sensores cs ON v.campo_id = cs.id
            LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
            WHERE v.campo_id = %s 
              AND v.fecha_hora_lectura >= (%s - INTERVAL %s MINUTE)
              AND v.fecha_hora_lectura <= %s
            ORDER BY v.fecha_hora_lectura DESC
            LIMIT 15000 
        ) AS sub
        ORDER BY sub.fecha_hora_lectura ASC;
        """
        cursor.execute(sql, (campo_id, fecha_fin, minutos, fecha_fin))
        return cursor.fetchall()

    except Exception as e:
        print(f"❌ [DB Error] ventana_tiempo: {e}")
        raise e
    finally:
        if conn: conn.close()




def aplicar_analisis_historico(
    datos: List[Dict[str, Any]], 
    config: Dict[str, float] = None
) -> List[Dict[str, Any]]:
    
    if not datos or len(datos) < 5: return datos

    if not config:
        config = {'temp_min': 20.0, 'temp_max': 26.0, 'hum_min': 30.0, 'hum_max': 60.0}

    # 1. Normalización
    nombre_raw = str(datos[0].get('nombre_campo') or '').lower()
    tipo_raw = str(datos[0].get('magnitud_tipo') or '').lower()
    
    es_movimiento = 'movimiento' in nombre_raw or 'estado' in nombre_raw
    es_temperatura = 'temperatura' in nombre_raw or 'temp' in tipo_raw or 'cel' in tipo_raw
    es_humedad = 'humedad' in nombre_raw or 'hum' in tipo_raw
    
    # 2. Grupo Eléctrico/Consumo (El que estaba fallando)
    es_consumo = ('corriente' in nombre_raw or 'potencia' in nombre_raw or 'energia' in nombre_raw or 
                  'iluminacion' in nombre_raw or 'amp' in tipo_raw or 'watt' in tipo_raw or 'kwh' in tipo_raw or 'lux' in tipo_raw)

    valores_float = [float(d['valor']) for d in datos]
    n = len(valores_float)

    # -------------------------------------------------------------------------
    # CASO A: MOVIMIENTO (Densidad)
    # -------------------------------------------------------------------------
    if es_movimiento:
        media_total = sum(valores_float) / n
        umbral = max(5.0, media_total * 3.0) 

        for d in datos:
            val = float(d['valor'])
            d['anomalia'] = False
            d['mensaje_alerta'] = None
            if val > umbral: 
                d['anomalia'] = True
                d['mensaje_alerta'] = f"Ráfaga de Actividad ({int(val)})"

    # -------------------------------------------------------------------------
    # CASO B: TEMPERATURA Y HUMEDAD (Límites Fijos)
    # -------------------------------------------------------------------------
    elif es_temperatura or es_humedad:
        if es_temperatura:
            MIN_LIMITE = config.get('temp_min', 20.0)
            MAX_LIMITE = config.get('temp_max', 26.0)
            unidad = "°C"
        else: 
            MIN_LIMITE = config.get('hum_min', 30.0)
            MAX_LIMITE = config.get('hum_max', 60.0)
            unidad = "%"

        for d in datos:
            val = float(d['valor'])
            d['anomalia'] = False
            d['mensaje_alerta'] = None

            if val == 0.0:
                d['anomalia'] = True
                d['mensaje_alerta'] = "Posible Error (0.0)"
                continue

            if val > MAX_LIMITE:
                d['anomalia'] = True
                d['mensaje_alerta'] = f"Alto: {val:.1f}{unidad}"
            elif val < MIN_LIMITE:
                d['anomalia'] = True
                d['mensaje_alerta'] = f"Bajo: {val:.1f}{unidad}"

    # -------------------------------------------------------------------------
    # CASO C: CONSUMO (Energía, Potencia, Corriente, Luz)
    # ESTRATEGIA: Z-Score LOCAL + Piso de Ruido Aprendido
    # -------------------------------------------------------------------------
    elif es_consumo:
        try:
            # 1. Aprender la ESCALA de los datos (no la varianza, solo la magnitud)
            # Si la mediana es 5000W, un cambio de 1W es ruido. 
            # Si la mediana es 5W, un cambio de 1W es enorme.
            mediana_global = statistics.median(valores_float)
            
            # Piso de ruido dinámico: 10% de la mediana o un mínimo absoluto técnico
            if mediana_global == 0: 
                ruido_minimo = 0.1 # Caso borde: todo está apagado
            else:
                ruido_minimo = abs(mediana_global * 0.10) 

        except statistics.StatisticsError:
            ruido_minimo = 1.0

        # Ventana pequeña para reaccionar rápido a los picos de "sierra"
        RADIO = 2 

        for i in range(n):
            d = datos[i]
            val = valores_float[i]
            d['anomalia'] = False
            d['mensaje_alerta'] = None

            # --- Contexto Local (Vecinos) ---
            start = max(0, i - RADIO)
            end = min(n, i + RADIO + 1)
            vecinos = valores_float[start:end]
            
            # Quitamos el valor actual para no ensuciar el promedio de los vecinos
            vecinos_limpios = [v for v in vecinos if v != val]
            if not vecinos_limpios: vecinos_limpios = vecinos

            media_local = sum(vecinos_limpios) / len(vecinos_limpios)
            
            # --- Desviación Local ---
            varianza = sum([((x - media_local) ** 2) for x in vecinos_limpios]) / len(vecinos_limpios)
            std_local = math.sqrt(varianza)
            
            # 🟢 CLAVE DEL ÉXITO: 
            # Usamos la desviación local, PERO si es muy pequeña (línea plana),
            # usamos el "Piso de Ruido" que aprendimos de la mediana global.
            sigma_efectiva = max(std_local, ruido_minimo)

            # Cálculo Z-Score Local
            distancia = val - media_local
            z_score = distancia / sigma_efectiva

            # Umbral 3.0: Detecta anomalías claras
            if abs(z_score) > 3.0:
                d['anomalia'] = True
                if val > media_local:
                    d['mensaje_alerta'] = f"Pico: {val:.2f} (Ref: {media_local:.2f})"
                else:
                    # Solo marcamos caídas si realmente bajan mucho
                    if val < (media_local * 0.5): 
                        d['mensaje_alerta'] = f"Caída: {val:.2f} (Ref: {media_local:.2f})"
                    else:
                        d['anomalia'] = False # Falsa alarma (bajada suave)

    # -------------------------------------------------------------------------
    # CASO D: RESTO (Fallback Genérico)
    # -------------------------------------------------------------------------
    else:
        # Z-Score Global Simple
        media = sum(valores_float) / n
        varianza = sum([((x - media) ** 2) for x in valores_float]) / n
        std_dev = math.sqrt(varianza)
        if std_dev < 0.1: std_dev = 0.1
        
        for d in datos:
            val = float(d['valor'])
            z_score = (val - media) / std_dev
            d['anomalia'] = False
            d['mensaje_alerta'] = None
            if abs(z_score) > 3.5:
                d['anomalia'] = True
                d['mensaje_alerta'] = f"Valor atípico: {val:.2f}"

    return datos

# def aplicar_analisis_historico(
#     datos: List[Dict[str, Any]], 
#     config: Dict[str, float] = None
# ) -> List[Dict[str, Any]]:
    
#     if not datos or len(datos) < 5: return datos

#     if not config:
#         config = {'temp_min': 20.0, 'temp_max': 26.0, 'hum_min': 30.0, 'hum_max': 60.0}

#     # 1. Normalización
#     nombre_raw = str(datos[0].get('nombre_campo') or '').lower()
#     tipo_raw = str(datos[0].get('magnitud_tipo') or '').lower()
    
#     es_movimiento = 'movimiento' in nombre_raw or 'estado' in nombre_raw
#     es_temperatura = 'temperatura' in nombre_raw or 'temp' in tipo_raw or 'cel' in tipo_raw
#     es_humedad = 'humedad' in nombre_raw or 'hum' in tipo_raw
    
#     # Agrupamos todo lo que debe "aprenderse solo" (Eléctrico + Luz)
#     es_auto_aprendizaje = not (es_movimiento or es_temperatura or es_humedad)

#     valores_float = [float(d['valor']) for d in datos]
#     n = len(valores_float)

#     # -------------------------------------------------------------------------
#     # CASO A: MOVIMIENTO (Densidad) - Se mantiene igual, funciona bien
#     # -------------------------------------------------------------------------
#     if es_movimiento:
#         media_total = sum(valores_float) / n
#         umbral = max(5.0, media_total * 3.0) 

#         for d in datos:
#             val = float(d['valor'])
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None
#             if val > umbral: 
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Ráfaga de Actividad ({int(val)})"

#     # -------------------------------------------------------------------------
#     # CASO B: TEMPERATURA Y HUMEDAD (Reglas Fijas de Confort - Usuario manda)
#     # -------------------------------------------------------------------------
#     elif es_temperatura or es_humedad:
#         if es_temperatura:
#             MIN_LIMITE = config.get('temp_min', 20.0)
#             MAX_LIMITE = config.get('temp_max', 26.0)
#             unidad = "°C"
#         else: 
#             MIN_LIMITE = config.get('hum_min', 30.0)
#             MAX_LIMITE = config.get('hum_max', 60.0)
#             unidad = "%"

#         for d in datos:
#             val = float(d['valor'])
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None

#             if val == 0.0:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = "Posible Error (0.0)"
#                 continue

#             if val > MAX_LIMITE:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Alto: {val:.1f}{unidad}"
#             elif val < MIN_LIMITE:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Bajo: {val:.1f}{unidad}"

#     # -------------------------------------------------------------------------
#     # CASO C: AUTO-APRENDIZAJE (Energía, Potencia, Luz, Corriente)
#     # Algoritmo: Z-Score Robusto con MAD (Median Absolute Deviation)
#     # -------------------------------------------------------------------------
#     elif es_auto_aprendizaje:
        
#         # 1. Aprender la "Variabilidad Normal" de todo el set de datos histórico
#         # Usamos la mediana porque ignora los picos locos al aprender.
#         try:
#             mediana_global = statistics.median(valores_float)
#             # Calculamos la desviación absoluta de cada punto respecto a la mediana
#             desviaciones = [abs(x - mediana_global) for x in valores_float]
#             # La mediana de esas desviaciones es nuestro "MAD" (Qué tanto varía normalmente)
#             mad = statistics.median(desviaciones)
            
#             # Si el MAD es 0 (datos planos), forzamos un mínimo técnico para no dividir por 0
#             if mad == 0: mad = 0.001 
            
#             # Factor de escala para hacer el MAD comparable a la Desviación Estándar (constante estadística)
#             sigma_estimada = mad * 1.4826

#         except statistics.StatisticsError:
#             # Fallback si hay muy pocos datos
#             sigma_estimada = 1.0
#             mediana_global = sum(valores_float)/n

#         RADIO = 3 # Ventana de contexto local

#         for i in range(n):
#             d = datos[i]
#             val = valores_float[i]
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None

#             # --- SUB-LÓGICA: Contexto Local ---
#             start = max(0, i - RADIO)
#             end = min(n, i + RADIO + 1)
#             vecinos = valores_float[start:end]
            
#             # Limpiamos al propio valor para comparar contra "el resto"
#             vecinos_limpios = [v for v in vecinos if v != val]
#             if not vecinos_limpios: vecinos_limpios = vecinos

#             media_local = sum(vecinos_limpios) / len(vecinos_limpios)
            
#             # --- DETECCIÓN INTELIGENTE ---
#             # Comparamos la distancia del valor actual a su media local.
#             # Y dividimos esa distancia entre la variabilidad que APRENDIMOS del conjunto (sigma_estimada).
            
#             distancia = val - media_local
#             z_score_robusto = distancia / sigma_estimada

#             # UMBRAL 3.5: Significa "3.5 veces más variación de lo que aprendí que es normal"
#             # Como usamos MAD, esto funciona igual para 0.5 Amperes que para 1000 Watts.
#             if abs(z_score_robusto) > 3.5:
#                 d['anomalia'] = True
                
#                 # Mensajes inteligentes
#                 if val > media_local:
#                     d['mensaje_alerta'] = f"Pico Anormal: {val:.2f} (Tendencia: {media_local:.2f})"
#                 else:
#                     # Detección especial de "Cortes" (Caída a casi 0 cuando la tendencia no es 0)
#                     if val < 0.1 and media_local > (sigma_estimada * 2):
#                         d['mensaje_alerta'] = "Corte Súbito / Apagado"
#                     else:
#                         d['mensaje_alerta'] = f"Caída Anormal: {val:.2f} (Tendencia: {media_local:.2f})"

#     return datos



# def aplicar_analisis_historico(datos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """
#     Analiza datos históricos. 
#     - Temperatura/Humedad: Usa rangos fijos de confort (20-26°C, 30-60%).
#     - Resto: Usa Ventana Deslizante (Z-Score Local) para detectar picos inusuales.
#     """
#     if not datos or len(datos) < 5: return datos

#     # 1. Normalización de Identificadores (A prueba de balas)
#     nombre_raw = str(datos[0].get('nombre_campo') or '').lower()
#     tipo_raw = str(datos[0].get('magnitud_tipo') or '').lower()
    
#     # Banderas de identificación (Detecta cualquier variante)
#     es_movimiento = 'movimiento' in nombre_raw or 'estado' in nombre_raw or 'puerta' in nombre_raw
    
#     es_temperatura = ('temperatura' in nombre_raw or 'temp' in tipo_raw or 'cel' in tipo_raw or 'grad' in tipo_raw)
#     es_humedad = ('humedad' in nombre_raw or 'hum' in tipo_raw)
    
#     # -------------------------------------------------------------------------
#     # CASO A: MOVIMIENTO (Densidad / Ráfagas)
#     # -------------------------------------------------------------------------
#     if es_movimiento:
#         valores_float = [float(d['valor']) for d in datos]
#         n = len(valores_float)
#         media_total = sum(valores_float) / n
        
#         # Umbral Adaptativo:
#         # Si es puro (agrupado por minuto), el valor puede ser 12. 
#         # Si es optimizado (hora), puede ser 60.
#         # La media nos dice la escala.
#         umbral = max(5.0, media_total * 3.0) 

#         for d in datos:
#             val = float(d['valor'])
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None
            
#             if val > umbral: 
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Ráfaga de Actividad ({int(val)})"

#     # -------------------------------------------------------------------------
#     # CASO B: TEMPERATURA Y HUMEDAD (Reglas Fijas de Confort)
#     # -------------------------------------------------------------------------
#     elif es_temperatura or es_humedad:
#         # Definición de límites según el tipo
#         if es_temperatura:
#             MIN_LIMITE = 20.0
#             MAX_LIMITE = 26.0
#             unidad = "°C"
#         else: # Humedad
#             MIN_LIMITE = 30.0
#             MAX_LIMITE = 60.0
#             unidad = "%"

#         for d in datos:
#             val = float(d['valor'])
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None

#             # IMPORTANTE: Si es 0.0 exacto en temperatura/humedad, suele ser error de sensor
#             if val == 0.0:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = "Posible Error de Sensor (0.0)"
#                 continue

#             if val > MAX_LIMITE:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Alto: {val:.1f}{unidad} (Límite: {MAX_LIMITE}{unidad})"
            
#             elif val < MIN_LIMITE:
#                 d['anomalia'] = True
#                 d['mensaje_alerta'] = f"Bajo: {val:.1f}{unidad} (Límite: {MIN_LIMITE}{unidad})"

#     # -------------------------------------------------------------------------
#     # CASO C: GENÉRICOS (Energía, Potencia, Corriente, Luminosidad...)
#     # -------------------------------------------------------------------------
#     else:
#         valores_float = [float(d['valor']) for d in datos]
#         n = len(valores_float)
#         RADIO = 3 

#         for i in range(n):
#             d = datos[i]
#             val = valores_float[i]
#             d['anomalia'] = False
#             d['mensaje_alerta'] = None

#             # 1. Definir vecindario
#             start = max(0, i - RADIO)
#             end = min(n, i + RADIO + 1)
#             vecinos = valores_float[start:end]
            
#             # 2. Estadística local
#             vecinos_limpios = [v for v in vecinos if v != val]
#             if not vecinos_limpios: vecinos_limpios = vecinos

#             media_local = sum(vecinos_limpios) / len(vecinos_limpios)
#             varianza = sum([((x - media_local) ** 2) for x in vecinos_limpios]) / len(vecinos_limpios)
#             std_local = math.sqrt(varianza)
            
#             # Ajuste de Sensibilidad:
#             # Si el valor es pequeño (< 10), la desviación mínima permitida es pequeña (0.1)
#             # Si el valor es grande (> 100), la desviación mínima aumenta (5.0)
#             min_std = 0.1 if val < 10 else 2.0
#             if std_local < min_std: std_local = min_std

#             # 3. Z-Score Local
#             z_score = (val - media_local) / std_local
            
#             if abs(z_score) > 3.5:
#                 d['anomalia'] = True
#                 if val > media_local:
#                     d['mensaje_alerta'] = f"Pico: {val:.2f} (Contexto: {media_local:.2f})"
#                 else:
#                     d['mensaje_alerta'] = f"Caída: {val:.2f} (Contexto: {media_local:.2f})"

#     return datos

# -----------------------------------------------------------------------------
# 3. HISTÓRICO (OPTIMIZADO)
# -----------------------------------------------------------------------------
async def obtener_historico_campo_db(
    campo_id: int, fecha_inicio: datetime, fecha_fin: datetime, metodo_carga: str = 'optimizado'
) -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        if metodo_carga == 'puro':
            print(f" [DB] Modo: PURO (Analizando tipo de dato...)")
            
            # A. Identificar si es Movimiento
            cursor.execute("SELECT nombre, unidad_medida_id FROM campos_sensores WHERE id = %s", (campo_id,))
            info_campo = cursor.fetchone()
            
            # Limpieza preventiva del cursor
            # cursor.fetchall() 
            
            nombre_c = info_campo['nombre'].lower() if info_campo else ''
            es_movimiento = 'movimiento' in nombre_c or 'estado' in nombre_c or 'puerta' in nombre_c

            if es_movimiento:
                # En lugar de 0s y 1s, obtenemos la "Intensidad" del movimiento por minuto.
                # SUM(v.valor) cuenta cuántas veces el sensor dijo "1" en ese minuto.
                print(f"   -> Detectado Movimiento: Agrupando por MINUTO (Densidad).")
                
                sql = """
                SELECT 
                    -- Formateamos la fecha hasta el minuto (YYYY-MM-DD HH:MM:00)
                    DATE_FORMAT(v.fecha_hora_lectura, '%%Y-%%m-%%d %%H:%%i:00') as fecha_hora_lectura,
                    
                    -- SUMAMOS los 1s. Si hubo 12 registros de '1', el valor será 12.
                    SUM(v.valor) as valor, 
                    
                    MAX(cs.nombre) as nombre_campo,
                    MAX(um.magnitud_tipo) as magnitud_tipo, 
                    MAX(um.simbolo) as simbolo_unidad
                FROM valores v 
                JOIN campos_sensores cs ON v.campo_id = cs.id
                LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
                WHERE v.campo_id = %s 
                  AND v.fecha_hora_lectura BETWEEN %s AND %s
                -- Agrupamos por el string de fecha para compatibilidad total SQL
                GROUP BY fecha_hora_lectura
                ORDER BY fecha_hora_lectura ASC;
                """
                cursor.execute(sql, (campo_id, fecha_inicio, fecha_fin))
                return cursor.fetchall()

            else:
                # Aquí sí queremos cada milímetro de variación, traemos todo crudo.
                print(f"   -> Sensor Analógico: Trayendo datos 100% crudos.")
                
                sql = """
                SELECT * FROM (
                    SELECT v.valor, v.fecha_hora_lectura, 
                           cs.nombre AS nombre_campo, 
                           um.magnitud_tipo, um.simbolo AS simbolo_unidad
                    FROM valores v 
                    JOIN campos_sensores cs ON v.campo_id = cs.id
                    LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
                    WHERE v.campo_id = %s AND v.fecha_hora_lectura BETWEEN %s AND %s
                    ORDER BY v.fecha_hora_lectura DESC  
                ) AS sub ORDER BY sub.fecha_hora_lectura ASC;
                """
                cursor.execute(sql, (campo_id, fecha_inicio, fecha_fin))
                return cursor.fetchall()

        else:
            # ---------------------------------------------------------
            # ESTRATEGIA B: OPTIMIZADO (PROMEDIOS POR HORA)
            # ---------------------------------------------------------
            print(f" [DB] Modo: OPTIMIZADO (Solicitado explícitamente o Default)")
            
            # 1. Tabla pre-agregada
            sql_agregada = """
            SELECT TIMESTAMP(va.fecha, MAKETIME(va.hora, 0, 0)) as fecha_hora_lectura,
                CASE WHEN cs.nombre LIKE '%%Movimiento%%' THEN va.valor_sum ELSE va.valor_avg END as valor,
                cs.nombre AS nombre_campo,
                um.magnitud_tipo, um.simbolo AS simbolo_unidad
            FROM valores_agregados va JOIN campos_sensores cs ON va.campo_id = cs.id
            LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
            WHERE va.campo_id = %s AND va.fecha BETWEEN %s AND %s
            ORDER BY va.fecha ASC, va.hora ASC;
            """
            cursor.execute(sql_agregada, (campo_id, fecha_inicio.date(), fecha_fin.date()))
            resultados = cursor.fetchall()
            
            if resultados: return resultados
            
            # 2. Fallback: Agregación al vuelo
            print(f"⚠️ [DB] Sin pre-agregación. Calculando promedios al vuelo.")
            
            # 🟢 CORRECCIÓN: Usamos MAX(cs.nombre) para sacarlo del GROUP BY
            sql_on_the_fly = """
            SELECT 
                DATE_FORMAT(MIN(v.fecha_hora_lectura), '%%Y-%%m-%%d %%H:00:00') as fecha_hora_lectura,
                CASE 
                    WHEN MAX(cs.nombre) LIKE '%%Movimiento%%' THEN SUM(v.valor)
                    ELSE AVG(v.valor) 
                END as valor,
                MAX(cs.nombre) as nombre_campo,
                MAX(um.magnitud_tipo) as magnitud_tipo,
                MAX(um.simbolo) AS simbolo_unidad
            FROM valores v
            JOIN campos_sensores cs ON v.campo_id = cs.id
            LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
            WHERE v.campo_id = %s 
              AND v.fecha_hora_lectura BETWEEN %s AND %s
            GROUP BY DATE(v.fecha_hora_lectura), HOUR(v.fecha_hora_lectura)
            ORDER BY fecha_hora_lectura ASC;
            """
            cursor.execute(sql_on_the_fly, (campo_id, fecha_inicio, fecha_fin))
            return cursor.fetchall()

    except Exception as e:
        print(f"❌ [DB Error] historico: {e}")
        raise e
    finally:
        if conn: conn.close()

# async def obtener_historico_campo_db(
#     campo_id: int, fecha_inicio: datetime, fecha_fin: datetime, metodo_carga: str = 'optimizado'
# ) -> List[Dict[str, Any]]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor(pymysql.cursors.DictCursor)
        
#         # 🟢 CAMBIO CRÍTICO: Eliminamos la lógica de "rango_dias < 1"
#         # Ahora la decisión es ESTRICTAMENTE basada en lo que pide el frontend.
        
#         if metodo_carga == 'puro':
#             # ---------------------------------------------------------
#             # ESTRATEGIA A: DATOS PUROS (RAW)
#             # Trae cada lectura individual. Útil para zoom profundo o auditoría exacta.
#             # ---------------------------------------------------------
#             print(f"⚡ [DB] Modo: PURO (Solicitado explícitamente)")
#             sql = """
#             SELECT * FROM (
#                 SELECT v.valor, v.fecha_hora_lectura, um.magnitud_tipo, um.simbolo AS simbolo_unidad
#                 FROM valores v JOIN campos_sensores cs ON v.campo_id = cs.id
#                 LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
#                 WHERE v.campo_id = %s AND v.fecha_hora_lectura BETWEEN %s AND %s
#                 ORDER BY v.fecha_hora_lectura DESC  
#             ) AS sub ORDER BY sub.fecha_hora_lectura ASC;
#             """
#             cursor.execute(sql, (campo_id, fecha_inicio, fecha_fin))
#             return cursor.fetchall()

#         else:
#             # ---------------------------------------------------------
#             # ESTRATEGIA B: OPTIMIZADO (PROMEDIOS POR HORA)
#             # Default para gráficas generales, reportes mensuales/anuales.
#             # ---------------------------------------------------------
#             print(f"📊 [DB] Modo: OPTIMIZADO (Solicitado explícitamente o Default)")
            
#             # 1. Intentar buscar en tabla pre-agregada (Rendimiento extremo)
#             sql_agregada = """
#             SELECT TIMESTAMP(va.fecha, MAKETIME(va.hora, 0, 0)) as fecha_hora_lectura,
#                 CASE WHEN cs.nombre LIKE '%%Movimiento%%' THEN va.valor_sum ELSE va.valor_avg END as valor,
#                 um.magnitud_tipo, um.simbolo AS simbolo_unidad
#             FROM valores_agregados va JOIN campos_sensores cs ON va.campo_id = cs.id
#             LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
#             WHERE va.campo_id = %s AND va.fecha BETWEEN %s AND %s
#             ORDER BY va.fecha ASC, va.hora ASC;
#             """
#             cursor.execute(sql_agregada, (campo_id, fecha_inicio.date(), fecha_fin.date()))
#             resultados = cursor.fetchall()
            
#             if resultados: return resultados
            
#             # 2. Fallback: Si no hay tabla agregada, calculamos promedios al vuelo
#             # Esto reduce 10,000 puntos a 24 puntos (si es un día) o 720 puntos (si es un mes)
#             print(f"⚠️ [DB] Sin pre-agregación. Calculando promedios al vuelo.")
#             sql_on_the_fly = """
#             SELECT 
#                 DATE_FORMAT(MIN(v.fecha_hora_lectura), '%%Y-%%m-%%d %%H:00:00') as fecha_hora_lectura,
#                 CASE 
#                     WHEN MAX(cs.nombre) LIKE '%%Movimiento%%' THEN SUM(v.valor)
#                     ELSE AVG(v.valor) 
#                 END as valor,
#                 MAX(um.magnitud_tipo) as magnitud_tipo,
#                 MAX(um.simbolo) AS simbolo_unidad
#             FROM valores v
#             JOIN campos_sensores cs ON v.campo_id = cs.id
#             LEFT JOIN unidades_medida um ON cs.unidad_medida_id = um.id
#             WHERE v.campo_id = %s 
#               AND v.fecha_hora_lectura BETWEEN %s AND %s
#             GROUP BY DATE(v.fecha_hora_lectura), HOUR(v.fecha_hora_lectura)
#             ORDER BY fecha_hora_lectura ASC;
#             """
#             cursor.execute(sql_on_the_fly, (campo_id, fecha_inicio, fecha_fin))
#             return cursor.fetchall()

#     except Exception as e:
#         print(f"❌ [DB Error] historico: {e}")
#         raise e
#     finally:
#         if conn: conn.close()

# -----------------------------------------------------------------------------
# 4. RANGO DE FECHAS
# -----------------------------------------------------------------------------
async def obtener_rango_fechas_db(dispositivo_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT MIN(va.fecha) as fecha_minima, MAX(va.fecha) as fecha_maxima FROM valores_agregados va JOIN campos_sensores cs ON va.campo_id = cs.id JOIN sensores s ON cs.sensor_id = s.id WHERE s.dispositivo_id = %s"
        cursor.execute(sql, (dispositivo_id,))
        result = cursor.fetchone()
        if not result or not result['fecha_minima']:
            sql_raw = "SELECT MIN(v.fecha_hora_lectura) as fecha_minima, MAX(v.fecha_hora_lectura) as fecha_maxima FROM valores v JOIN campos_sensores cs ON v.campo_id = cs.id JOIN sensores s ON cs.sensor_id = s.id WHERE s.dispositivo_id = %s"
            cursor.execute(sql_raw, (dispositivo_id,))
            result = cursor.fetchone()
        if not result or not result['fecha_minima']:
             hoy = datetime.now().strftime('%Y-%m-%d')
             return {"fecha_minima": hoy, "fecha_maxima": hoy}
        return result
    except Exception as e:
        print(f"❌ [DB Error] rango_fechas: {e}")
        raise e
    finally:
        if conn: conn.close()