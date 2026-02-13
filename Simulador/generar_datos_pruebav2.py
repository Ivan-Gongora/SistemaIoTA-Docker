import csv
import datetime
import random
import math
import time

# --- 1. CONFIGURACIÓN DE LA SIMULACIÓN ---
DEVICE_ID = 1
SIMULATION_DAYS = 30
INTERVAL_SECONDS = 5
OUTPUT_FILE = 'simulacion_aula_1mes_realista.csv'

# --- 2. CONSTANTES REALISTAS DEL AULA ---

# Horarios de clase (Lunes a Viernes)
CLASS_START_M = 7   # 7:00 AM
CLASS_END_M = 14    # 2:00 PM  
CLASS_START_V = 14  # 2:00 PM
CLASS_END_V = 22    # 10:00 PM

# Clima Base (Otoño en Chetumal) - AJUSTADO
TEMP_EXT_MIN = 24.0  # Mínima nocturna REALISTA
TEMP_EXT_MAX = 32.0  # Máxima diurna REALISTA
HUM_EXT_MIN = 70.0   # Humedad exterior mínima REALISTA
HUM_EXT_MAX = 88.0   # Humedad exterior máxima REALISTA

# Lógica del Aire Acondicionado (A/C) - AJUSTADO
AC_THRESHOLD_TEMP = 26.0  # Temp. más realista para encender A/C
AC_TARGET_TEMP = 24.0     # Temp. objetivo REALISTA
AC_TARGET_HUM = 65.0      # Humedad objetivo REALISTA

# --- 3. CONSTANTES ELÉCTRICAS CORREGIDAS ---
# VALORES REALISTAS PARA UN AULA UNIVERSITARIA

# Consumo base (equipos siempre encendidos: routers, servidores, etc.)
POWER_BASE_LOAD = 50      # 50W - REALISTA

# Computadoras (15-20 equipos)
POWER_PC_IDLE = 80        # 80W por PC en idle
POWER_PC_ACTIVE = 120     # 120W por PC activo
NUM_PCS = 18              # 18 computadoras

# Iluminación
POWER_LIGHTS_LOW = 200    # 200W - iluminación básica
POWER_LIGHTS_FULL = 400   # 400W - iluminación completa

# Aire acondicionado - CORREGIDO
POWER_AC_IDLE = 100       # 100W - ventilador/electrónica
POWER_AC_COOLING = 1500   # 1500W - compresor funcionando

# Otros equipos
POWER_PROJECTOR = 250     # 250W - proyector
POWER_CHARGING = 5        # 5W por dispositivo cargando
NUM_CHARGING_DEVICES = 15 # 15 dispositivos cargando

VOLTAGE = 120.0  # Voltaje estándar en México

def simular_clima_exterior(hour_fraction):
    """Simula clima exterior realista para Quintana Roo"""
    sin_wave = math.sin(math.pi * (hour_fraction - 0.25) * 2) 
    temp_range = (TEMP_EXT_MAX - TEMP_EXT_MIN) / 2
    temp_avg = (TEMP_EXT_MAX + TEMP_EXT_MIN) / 2
    
    # Añade ruido aleatorio más suave
    temp_exterior = temp_avg + temp_range * sin_wave + random.uniform(-0.3, 0.3)
    
    # Humedad inversamente relacionada con temperatura
    hum_base = 85 - (temp_exterior - 25) * 2
    hum_exterior = max(HUM_EXT_MIN, min(HUM_EXT_MAX, hum_base + random.uniform(-3, 3)))
    
    return temp_exterior, hum_exterior

def calcular_consumo_electrico(is_occupied, is_ac_on, hour_of_day, is_class_time):
    """Calcula consumo eléctrico REALISTA para un aula universitaria"""
    
    # 1. CONSUMO BASE (siempre presente)
    potencia_activa = POWER_BASE_LOAD
    
    # 2. COMPUTADORAS - comportamiento realista
    if is_occupied and is_class_time:
        # Durante clase: mayoría de PCs activos
        pcs_activos = random.randint(12, NUM_PCS)
        pcs_idle = NUM_PCS - pcs_activos
        potencia_activa += (pcs_activos * POWER_PC_ACTIVE) + (pcs_idle * POWER_PC_IDLE)
    elif is_occupied:
        # Ocupación no lectiva: menos PCs activos
        pcs_activos = random.randint(3, 8)
        pcs_idle = NUM_PCS - pcs_activos
        potencia_activa += (pcs_activos * POWER_PC_ACTIVE) + (pcs_idle * POWER_PC_IDLE)
    else:
        # Aula vacía: solo consumo fantasma de PCs
        potencia_activa += NUM_PCS * 2  # 2W por PC en standby
    
    # 3. ILUMINACIÓN - según hora y ocupación
    if is_occupied:
        if 18 <= hour_of_day < 22:  # Noche: iluminación completa
            potencia_activa += POWER_LIGHTS_FULL
        else:  # Día: iluminación reducida o natural
            potencia_activa += random.randint(POWER_LIGHTS_LOW // 2, POWER_LIGHTS_LOW)
    else:
        # Aula vacía: posible luz de seguridad
        potencia_activa += random.randint(0, 20) if random.random() < 0.1 else 0
    
    # 4. AIRE ACONDICIONADO - comportamiento REALISTA
    if is_ac_on:
        # El A/C no consume potencia máxima constantemente
        if random.random() < 0.7:  # 70% del tiempo el compresor está activo
            potencia_activa += POWER_AC_COOLING
        potencia_activa += POWER_AC_IDLE  # Consumo base del A/C siempre que está encendido
    
    # 5. PROYECTOR - solo durante clases
    if is_occupied and is_class_time and random.random() < 0.6:
        potencia_activa += POWER_PROJECTOR
    
    # 6. CARGA DE DISPOSITIVOS
    if is_occupied:
        dispositivos_cargando = random.randint(8, NUM_CHARGING_DEVICES)
        potencia_activa += dispositivos_cargando * POWER_CHARGING
    
    # 7. VARIACIÓN NATURAL (ruido del sensor)
    potencia_activa += random.uniform(-20, 20)
    potencia_activa = max(10, potencia_activa)  # Mínimo consumo realista
    
    return potencia_activa

def main():
    print(f"🎯 GENERANDO {SIMULATION_DAYS} DÍAS DE DATOS REALISTAS...")
    print(f"📊 Dispositivo: {DEVICE_ID}")
    print(f"⏱️  Intervalo: {INTERVAL_SECONDS} segundos")
    print(f"💾 Archivo: {OUTPUT_FILE}")
    print("=" * 50)
    
    start_time = time.time()
    current_time = datetime.datetime(2025, 9, 1, 0, 0, 0)
    end_time = current_time + datetime.timedelta(days=SIMULATION_DAYS)
    paquete_id = 1
    
    # VARIABLES DE ENERGÍA - CORREGIDAS
    energia_total_acumulada = 0.0
    energia_dia_actual = 0.0
    dia_actual = current_time.day
    
    # Estado del aula
    temp_interior = 25.0  # Más realista
    hum_interior = 75.0   # Más realista
    
    # Estado del A/C
    ac_on = False
    ac_runtime = 0

    # Definir el CSV
    header = [
        'Dispositivo_id', 'Paquete_id', 'Fecha', 'Hora', 
        'Temperatura', 'Humedad', 'Corriente', 'Potencia', 'Energia',
        'Iluminacion', 'Movimiento'
    ]
    
    total_rows = 0

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        while current_time < end_time:
            
            # --- A. Verificar cambio de día ---
            if current_time.day != dia_actual:
                print(f"📅 Día {current_time.day} completado - Energía acumulada: {energia_total_acumulada:.2f} kWh")
                energia_dia_actual = 0.0
                dia_actual = current_time.day
            
            # --- B. Determinar Estado del Aula ---
            day_of_week = current_time.weekday()
            hour_of_day = current_time.hour
            minute_of_day = current_time.minute
            
            is_weekend = (day_of_week >= 5)
            is_class_time = (not is_weekend) and \
                            ((CLASS_START_M <= hour_of_day < CLASS_END_M) or \
                             (CLASS_START_V <= hour_of_day < CLASS_END_V))
            
            # Comportamiento más realista de ocupación
            if is_class_time:
                # Durante clases: alta probabilidad de ocupación
                # Considerar cambios de clase (aumento de movimiento)
                if minute_of_day >= 50 and minute_of_day <= 55:  # Cambio de clase
                    is_occupied = random.random() < 0.98
                else:
                    is_occupied = random.random() < 0.85
            else:
                # Fuera de horario: baja probabilidad
                is_occupied = random.random() < 0.05
            
            # --- C. Simular Clima y A/C MEJORADO ---
            hour_fraction = (hour_of_day + current_time.minute / 60) / 24.0
            temp_exterior, hum_exterior = simular_clima_exterior(hour_fraction)
            
            # Lógica MEJORADA del A/C
            if is_occupied and temp_interior > AC_THRESHOLD_TEMP:
                ac_on = True
                ac_runtime += 1
            elif not is_occupied or temp_interior <= AC_TARGET_TEMP:
                ac_on = False
                # El A/C se apaga gradualmente
                if ac_runtime > 0:
                    ac_runtime -= 1
            
            # Ajuste de temperatura más realista
            if ac_on and ac_runtime > 0:
                # Enfriamiento activo
                temp_change = (AC_TARGET_TEMP - temp_interior) * 0.15 + random.uniform(-0.05, 0.05)
                hum_change = (AC_TARGET_HUM - hum_interior) * 0.1 + random.uniform(-0.1, 0.1)
            else:
                # Temperatura natural
                temp_change = (temp_exterior - temp_interior) * 0.02 + random.uniform(-0.05, 0.05)
                hum_change = (hum_exterior - hum_interior) * 0.01 + random.uniform(-0.2, 0.2)
            
            temp_interior += temp_change
            hum_interior += hum_change
            
            # Límites realistas
            temp_interior = max(22.0, min(32.0, temp_interior))
            hum_interior = max(40.0, min(90.0, hum_interior))

            # --- D. SIMULACIÓN ELÉCTRICA CORREGIDA ---
            potencia_activa = calcular_consumo_electrico(is_occupied, ac_on, hour_of_day, is_class_time)
            
            # Cálculo de corriente REALISTA
            corriente = potencia_activa / VOLTAGE

            # Cálculo de energía CORREGIDO (kWh en el intervalo de 5 segundos)
            energia_intervalo = (potencia_activa / 1000.0) * (INTERVAL_SECONDS / 3600.0)
            energia_total_acumulada += energia_intervalo
            energia_dia_actual += energia_intervalo

            # --- E. Sensores de Ocupación MEJORADOS ---
            
            # Sensor PIR HC-SR501 - comportamiento realista
            if is_occupied:
                # Durante ocupación, alta probabilidad de detección
                # Pero no constante (personas se mueven)
                if random.random() < 0.85:
                    movimiento = 1
                else:
                    movimiento = 0  # Breves momentos sin movimiento
            else:
                # Aula vacía: ocasionalmente falsos positivos
                movimiento = 1 if random.random() < 0.002 else 0

            # Sensor BH1750 - iluminación realista MEJORADA
            if is_occupied:
                # Ocupación: iluminación artificial
                if 18 <= hour_of_day < 22:  # Noche: iluminación completa
                    iluminacion = random.randint(400, 600)
                else:  # Día: mezcla de natural y artificial
                    iluminacion = random.randint(300, 500)
            else:
                # Aula vacía - COMPORTAMIENTO MÁS CONSISTENTE
                if 6 <= hour_of_day <= 18:  # Horas de luz natural
                    # Iluminación natural variable
                    hora_solar = abs(hour_of_day - 12)
                    if hora_solar <= 2: 
                        iluminacion = random.randint(700, 900)
                    elif hora_solar <= 4: 
                        iluminacion = random.randint(400, 700)
                    else: 
                        iluminacion = random.randint(100, 400)
                else:
                    # Noche: SIEMPRE oscuro cuando está vacío (más consistente)
                    iluminacion = 0

            # --- F. Escribir Fila ---
            fecha_str = current_time.strftime('%Y-%m-%d')
            hora_str = current_time.strftime('%H:%M:%S')
            
            # Formatear energía para evitar notación científica
            energia_str = f"{energia_intervalo:.8f}"
            
            writer.writerow([
                DEVICE_ID, 
                paquete_id, 
                fecha_str, 
                hora_str,
                round(temp_interior, 1),      # DHT22 - 1 decimal
                round(hum_interior, 1),       # DHT22 - 1 decimal
                round(corriente, 2),          # SCT-013-000 - 2 decimales
                round(potencia_activa, 1),    # SCT-013-000 - 1 decimal
                energia_str,                  # Energía en formato decimal fijo
                int(iluminacion),             # BH1750 - entero
                int(movimiento)               # PIR HC-SR501 - entero (0/1)
            ])
            
            # --- G. Incrementar Tiempo ---
            current_time += datetime.timedelta(seconds=INTERVAL_SECONDS)
            paquete_id += 1
            total_rows += 1
            
            # Mostrar progreso cada 20,000 registros
            if total_rows % 20000 == 0:
                hora_actual = current_time.strftime('%Y-%m-%d %H:%M:%S')
                print(f"  ... {total_rows:,} registros - {hora_actual}")

    end_gen_time = time.time()
    print("=" * 50)
    print("✅ SIMULACIÓN COMPLETADA")
    print(f"📊 Total registros: {total_rows:,}")
    print(f"⚡ Energía total: {energia_total_acumulada:.2f} kWh")
    print(f"📅 Consumo diario promedio: {energia_total_acumulada/SIMULATION_DAYS:.2f} kWh/día")
    print(f"⏱️  Tiempo de generación: {end_gen_time - start_time:.2f} segundos")
    print(f"💾 Archivo: {OUTPUT_FILE}")
    
    # Mostrar estadísticas de rango
    print(f"\n🔍 RANGOS ESPERADOS:")
    print(f"   • Potencia: 10W - 2,800W")
    print(f"   • Corriente: 0.08A - 23.3A") 
    print(f"   • Energía/día: 1.0 - 2.5 kWh")
    print(f"   • Temperatura: 22°C - 32°C")
    print(f"   • Humedad: 40% - 90%")
    print(f"   • Iluminación: 0 - 900 lux")
    
    # Mostrar estimación de archivo
    tamaño_estimado_mb = (total_rows * 120) / (1024 * 1024)  # ~120 bytes por registro
    print(f"   • Tamaño estimado: {tamaño_estimado_mb:.1f} MB")

if __name__ == "__main__":
    main()
# import csv
# import datetime
# import random
# import math
# import time

# # --- 1. CONFIGURACIÓN DE LA SIMULACIÓN ---
# DEVICE_ID = 1
# SIMULATION_DAYS = 30
# INTERVAL_SECONDS = 5
# OUTPUT_FILE = 'simulacion_aula_1mes_corregida.csv'

# # --- 2. CONSTANTES REALISTAS DEL AULA ---

# # Horarios de clase (Lunes a Viernes)
# CLASS_START_M = 7   # 7:00 AM
# CLASS_END_M = 14    # 2:00 PM  
# CLASS_START_V = 14  # 2:00 PM
# CLASS_END_V = 22    # 10:00 PM

# # Clima Base (Otoño en Chetumal) - AJUSTADO
# TEMP_EXT_MIN = 24.0  # Mínima nocturna REALISTA
# TEMP_EXT_MAX = 32.0  # Máxima diurna REALISTA
# HUM_EXT_MIN = 70.0   # Humedad exterior mínima REALISTA
# HUM_EXT_MAX = 88.0   # Humedad exterior máxima REALISTA

# # Lógica del Aire Acondicionado (A/C) - AJUSTADO
# AC_THRESHOLD_TEMP = 26.0  # Temp. más realista para encender A/C
# AC_TARGET_TEMP = 24.0     # Temp. objetivo REALISTA
# AC_TARGET_HUM = 65.0      # Humedad objetivo REALISTA

# # --- 3. CONSTANTES ELÉCTRICAS CORREGIDAS ---
# # VALORES REALISTAS PARA UN AULA UNIVERSITARIA

# # Consumo base (equipos siempre encendidos: routers, servidores, etc.)
# POWER_BASE_LOAD = 50      # 50W - MUCHO MÁS REALISTA

# # Computadoras (15-20 equipos)
# POWER_PC_IDLE = 80        # 80W por PC en idle
# POWER_PC_ACTIVE = 120     # 120W por PC activo
# NUM_PCS = 18              # 18 computadoras

# # Iluminación
# POWER_LIGHTS_LOW = 200    # 200W - iluminación básica
# POWER_LIGHTS_FULL = 400   # 400W - iluminación completa

# # Aire acondicionado - CORREGIDO
# POWER_AC_IDLE = 100       # 100W - ventilador/electrónica
# POWER_AC_COOLING = 1500   # 1500W - compresor funcionando

# # Otros equipos
# POWER_PROJECTOR = 250     # 250W - proyector
# POWER_CHARGING = 5        # 5W por dispositivo cargando
# NUM_CHARGING_DEVICES = 15 # 15 dispositivos cargando

# VOLTAGE = 120.0  # Voltaje estándar en México

# def simular_clima_exterior(hour_fraction):
#     """Simula clima exterior realista para Quintana Roo"""
#     sin_wave = math.sin(math.pi * (hour_fraction - 0.25) * 2) 
#     temp_range = (TEMP_EXT_MAX - TEMP_EXT_MIN) / 2
#     temp_avg = (TEMP_EXT_MAX + TEMP_EXT_MIN) / 2
    
#     # Añade ruido aleatorio más suave
#     temp_exterior = temp_avg + temp_range * sin_wave + random.uniform(-0.3, 0.3)
    
#     # Humedad inversamente relacionada con temperatura
#     hum_base = 85 - (temp_exterior - 25) * 2
#     hum_exterior = max(HUM_EXT_MIN, min(HUM_EXT_MAX, hum_base + random.uniform(-3, 3)))
    
#     return temp_exterior, hum_exterior

# def calcular_consumo_electrico(is_occupied, is_ac_on, hour_of_day, is_class_time):
#     """Calcula consumo eléctrico REALISTA para un aula universitaria"""
    
#     # 1. CONSUMO BASE (siempre presente)
#     potencia_activa = POWER_BASE_LOAD
    
#     # 2. COMPUTADORAS - comportamiento realista
#     if is_occupied and is_class_time:
#         # Durante clase: mayoría de PCs activos
#         pcs_activos = random.randint(12, NUM_PCS)
#         pcs_idle = NUM_PCS - pcs_activos
#         potencia_activa += (pcs_activos * POWER_PC_ACTIVE) + (pcs_idle * POWER_PC_IDLE)
#     elif is_occupied:
#         # Ocupación no lectiva: menos PCs activos
#         pcs_activos = random.randint(3, 8)
#         pcs_idle = NUM_PCS - pcs_activos
#         potencia_activa += (pcs_activos * POWER_PC_ACTIVE) + (pcs_idle * POWER_PC_IDLE)
#     else:
#         # Aula vacía: solo consumo fantasma de PCs
#         potencia_activa += NUM_PCS * 2  # 2W por PC en standby
    
#     # 3. ILUMINACIÓN - según hora y ocupación
#     if is_occupied:
#         if 18 <= hour_of_day < 22:  # Noche: iluminación completa
#             potencia_activa += POWER_LIGHTS_FULL
#         else:  # Día: iluminación reducida o natural
#             potencia_activa += random.randint(POWER_LIGHTS_LOW // 2, POWER_LIGHTS_LOW)
#     else:
#         # Aula vacía: posible luz de seguridad
#         potencia_activa += random.randint(0, 20) if random.random() < 0.1 else 0
    
#     # 4. AIRE ACONDICIONADO - comportamiento REALISTA
#     if is_ac_on:
#         # El A/C no consume potencia máxima constantemente
#         if random.random() < 0.7:  # 70% del tiempo el compresor está activo
#             potencia_activa += POWER_AC_COOLING
#         potencia_activa += POWER_AC_IDLE  # Consumo base del A/C siempre que está encendido
    
#     # 5. PROYECTOR - solo durante clases
#     if is_occupied and is_class_time and random.random() < 0.6:
#         potencia_activa += POWER_PROJECTOR
    
#     # 6. CARGA DE DISPOSITIVOS
#     if is_occupied:
#         dispositivos_cargando = random.randint(8, NUM_CHARGING_DEVICES)
#         potencia_activa += dispositivos_cargando * POWER_CHARGING
    
#     # 7. VARIACIÓN NATURAL (ruido del sensor)
#     potencia_activa += random.uniform(-20, 20)
#     potencia_activa = max(10, potencia_activa)  # Mínimo consumo realista
    
#     return potencia_activa

# def main():
#     print(f"Iniciando simulación REALISTA de {SIMULATION_DAYS} días...")
    
#     start_time = time.time()
#     current_time = datetime.datetime(2025, 10, 1, 0, 0, 0)
#     end_time = current_time + datetime.timedelta(days=SIMULATION_DAYS)
#     paquete_id = 1
    
#     # VARIABLES DE ENERGÍA - CORREGIDAS
#     energia_total_acumulada = 0.0
#     energia_dia_actual = 0.0
#     dia_actual = current_time.day
    
#     # Estado del aula
#     temp_interior = 25.0  # Más realista
#     hum_interior = 75.0   # Más realista
    
#     # Estado del A/C
#     ac_on = False
#     ac_runtime = 0

#     # Definir el CSV
#     header = [
#         'Dispositivo_id', 'Paquete_id', 'Fecha', 'Hora', 
#         'Temperatura', 'Humedad', 'Corriente', 'Potencia', 'Energia',
#         'Iluminacion', 'Movimiento'
#     ]
    
#     total_rows = 0

#     with open(OUTPUT_FILE, 'w', newline='') as f:
#         writer = csv.writer(f)
#         writer.writerow(header)

#         while current_time < end_time:
            
#             # --- A. Verificar cambio de día ---
#             if current_time.day != dia_actual:
#                 energia_dia_actual = 0.0
#                 dia_actual = current_time.day
#                 if total_rows % 10000 == 0:
#                     print(f"  Día {current_time.day} - Energía acumulada: {energia_total_acumulada:.2f} kWh")
            
#             # --- B. Determinar Estado del Aula ---
#             day_of_week = current_time.weekday()
#             hour_of_day = current_time.hour
#             minute_of_day = current_time.minute
            
#             is_weekend = (day_of_week >= 5)
#             is_class_time = (not is_weekend) and \
#                             ((CLASS_START_M <= hour_of_day < CLASS_END_M) or \
#                              (CLASS_START_V <= hour_of_day < CLASS_END_V))
            
#             # Comportamiento más realista de ocupación
#             if is_class_time:
#                 # Durante clases: alta probabilidad de ocupación
#                 # Considerar cambios de clase (aumento de movimiento)
#                 if minute_of_day >= 50 and minute_of_day <= 55:  # Cambio de clase
#                     is_occupied = random.random() < 0.98
#                 else:
#                     is_occupied = random.random() < 0.85
#             else:
#                 # Fuera de horario: baja probabilidad
#                 is_occupied = random.random() < 0.05
            
#             # --- C. Simular Clima y A/C MEJORADO ---
#             hour_fraction = (hour_of_day + current_time.minute / 60) / 24.0
#             temp_exterior, hum_exterior = simular_clima_exterior(hour_fraction)
            
#             # Lógica MEJORADA del A/C
#             if is_occupied and temp_interior > AC_THRESHOLD_TEMP:
#                 ac_on = True
#                 ac_runtime += 1
#             elif not is_occupied or temp_interior <= AC_TARGET_TEMP:
#                 ac_on = False
#                 # El A/C se apaga gradualmente
#                 if ac_runtime > 0:
#                     ac_runtime -= 1
            
#             # Ajuste de temperatura más realista
#             if ac_on and ac_runtime > 0:
#                 # Enfriamiento activo
#                 temp_change = (AC_TARGET_TEMP - temp_interior) * 0.15 + random.uniform(-0.05, 0.05)
#                 hum_change = (AC_TARGET_HUM - hum_interior) * 0.1 + random.uniform(-0.1, 0.1)
#             else:
#                 # Temperatura natural
#                 temp_change = (temp_exterior - temp_interior) * 0.02 + random.uniform(-0.05, 0.05)
#                 hum_change = (hum_exterior - hum_interior) * 0.01 + random.uniform(-0.2, 0.2)
            
#             temp_interior += temp_change
#             hum_interior += hum_change
            
#             # Límites realistas
#             temp_interior = max(22.0, min(32.0, temp_interior))
#             hum_interior = max(40.0, min(90.0, hum_interior))

#             # --- D. SIMULACIÓN ELÉCTRICA CORREGIDA ---
#             potencia_activa = calcular_consumo_electrico(is_occupied, ac_on, hour_of_day, is_class_time)
            
#             # Cálculo de corriente REALISTA
#             corriente = potencia_activa / VOLTAGE

#             # Cálculo de energía CORREGIDO (kWh en el intervalo de 5 segundos)
#             energia_intervalo = (potencia_activa / 1000.0) * (INTERVAL_SECONDS / 3600.0)
#             energia_total_acumulada += energia_intervalo
#             energia_dia_actual += energia_intervalo

#             # --- E. Sensores de Ocupación MEJORADOS ---
            
#             # Sensor PIR HC-SR501 - comportamiento realista
#             if is_occupied:
#                 # Durante ocupación, alta probabilidad de detección
#                 # Pero no constante (personas se mueven)
#                 if random.random() < 0.85:
#                     movimiento = 1
#                 else:
#                     movimiento = 0  # Breves momentos sin movimiento
#             else:
#                 # Aula vacía: ocasionalmente falsos positivos
#                 movimiento = 1 if random.random() < 0.002 else 0

#             # Sensor BH1750 - iluminación realista
#             if is_occupied:
#                 # Ocupación: iluminación artificial
#                 if 18 <= hour_of_day < 22:  # Noche: iluminación completa
#                     iluminacion = random.randint(400, 600)
#                 else:  # Día: mezcla de natural y artificial
#                     iluminacion = random.randint(300, 500)
#             else:
#                 # Aula vacía
#                 if 6 <= hour_of_day <= 18:  # Horas de luz natural
#                     # Iluminación natural variable
#                     hora_solar = abs(hour_of_day - 12)
#                     if hora_solar <= 2: 
#                         iluminacion = random.randint(700, 900)
#                     elif hora_solar <= 4: 
#                         iluminacion = random.randint(400, 700)
#                     else: 
#                         iluminacion = random.randint(100, 400)
#                 else:
#                     # Noche: posible luz de seguridad o oscuridad
#                     iluminacion = random.randint(0, 50) if random.random() < 0.1 else 0

#             # --- F. Escribir Fila ---
#             fecha_str = current_time.strftime('%Y-%m-%d')
#             hora_str = current_time.strftime('%H:%M:%S')
            
#             writer.writerow([
#                 DEVICE_ID, 
#                 paquete_id, 
#                 fecha_str, 
#                 hora_str,
#                 round(temp_interior, 1),      # DHT22 - 1 decimal
#                 round(hum_interior, 1),       # DHT22 - 1 decimal
#                 round(corriente, 2),          # SCT-013-000 - 2 decimales
#                 round(potencia_activa, 1),    # SCT-013-000 - 1 decimal
#                 round(energia_intervalo, 8),  # Energía en el intervalo, 8 decimales
#                 int(iluminacion),             # BH1750 - entero
#                 int(movimiento)               # PIR HC-SR501 - entero (0/1)
#             ])
            
#             # --- G. Incrementar Tiempo ---
#             current_time += datetime.timedelta(seconds=INTERVAL_SECONDS)
#             paquete_id += 1
#             total_rows += 1
            
#             if total_rows % 50000 == 0:
#                 print(f"  ... {total_rows:,} registros generados ...")
#                 # Mostrar ejemplo REALISTA
#                 print(f"    Ejemplo - Pot: {potencia_activa:.1f}W, Corriente: {corriente:.2f}A, Energía: {energia_intervalo:.8f}kWh")

#     end_gen_time = time.time()
#     print("-" * 50)
#     print("SIMULACIÓN REALISTA COMPLETADA")
#     print(f"Total registros: {total_rows:,}")
#     print(f"Energía total simulada: {energia_total_acumulada:.2f} kWh")
#     print(f"Consumo diario promedio: {energia_total_acumulada/SIMULATION_DAYS:.2f} kWh/día")
#     print(f"Tiempo: {end_gen_time - start_time:.2f} segundos")
#     print(f"Archivo: {OUTPUT_FILE}")

# if __name__ == "__main__":
#     main()


# import csv
# import datetime
# import random
# import math
# import time

# # --- 1. CONFIGURACIÓN DE LA SIMULACIÓN ---
# DEVICE_ID = 1
# SIMULATION_DAYS = 30
# INTERVAL_SECONDS = 5
# OUTPUT_FILE = 'simulacion_aula_1mes_corregida.csv'

# # --- 2. CONSTANTES DEL AULA (BASADO EN TU INVESTIGACIÓN) ---

# # Horarios de clase (Lunes a Viernes)
# CLASS_START_M = 7  # 7:00 AM
# CLASS_END_M = 14   # 2:00 PM
# CLASS_START_V = 14 # 2:00 PM
# CLASS_END_V = 22   # 10:00 PM

# # Clima Base (Otoño en Chetumal)
# TEMP_EXT_MIN = 19.0 # Mínima nocturna
# TEMP_EXT_MAX = 30.0 # Máxima diurna
# HUM_EXT_MIN = 75.0  # Humedad exterior mínima
# HUM_EXT_MAX = 85.0  # Humedad exterior máxima

# # Lógica del Aire Acondicionado (A/C)
# AC_THRESHOLD_TEMP = 25.0 # Temp. interior para encender el A/C
# AC_TARGET_TEMP = 22.0    # Temp. objetivo del A/C
# AC_TARGET_HUM = 60.0     # Humedad objetivo del A/C

# # Constantes eléctricas MEJORADAS
# POWER_BASE_LOAD = 250
# POWER_PC_LOAD = 2500
# POWER_LIGHTS = 500
# POWER_AC_LOAD = 5500
# VOLTAGE = 220.0
# POWER_FACTOR_BASE = 0.95  # Factor de potencia para carga base
# POWER_FACTOR_PC = 0.85    # Factor de potencia para PCs (menos eficiente)
# POWER_FACTOR_AC = 0.90    # Factor de potencia para A/C

# def simular_clima_exterior(hour_fraction):
#     # ... (igual que antes)
#     sin_wave = math.sin(math.pi * (hour_fraction - 0.25) * 2) 
#     temp_range = (TEMP_EXT_MAX - TEMP_EXT_MIN) / 2
#     temp_avg = (TEMP_EXT_MAX + TEMP_EXT_MIN) / 2
    
#     # Añade ruido aleatorio
#     temp_exterior = temp_avg + temp_range * sin_wave + random.uniform(-0.5, 0.5)
#     hum_exterior = random.uniform(HUM_EXT_MIN, HUM_EXT_MAX)
    
#     return temp_exterior, hum_exterior

# def main():
#     print(f"Iniciando simulación CORREGIDA de {SIMULATION_DAYS} días...")
    
#     start_time = time.time()
#     current_time = datetime.datetime(2025, 10, 1, 0, 0, 0)
#     end_time = current_time + datetime.timedelta(days=SIMULATION_DAYS)
#     paquete_id = 1
    
#     # VARIABLES DE ENERGÍA MEJORADAS
#     energia_total_acumulada = 0.0
#     energia_dia_actual = 0.0
#     dia_actual = current_time.day
    
#     # Estado del aula
#     temp_interior = 24.0
#     hum_interior = 80.0

#     # Definir el CSV
#     header = [
#         'Dispositivo_id', 'Paquete_id', 'Fecha', 'Hora', 
#         'Temperatura', 'Humedad', 'Corriente', 'Potencia', 'Energia_Total', 'Energia_Diaria',
#         'Iluminacion', 'Movimiento'
#     ]
    
#     total_rows = 0

#     with open(OUTPUT_FILE, 'w', newline='') as f:
#         writer = csv.writer(f)
#         writer.writerow(header)

#         while current_time < end_time:
            
#             # --- A. Verificar cambio de día (PARA ENERGÍA DIARIA) ---
#             if current_time.day != dia_actual:
#                 energia_dia_actual = 0.0  # Reset energía diaria
#                 dia_actual = current_time.day
            
#             # --- B. Determinar Estado del Aula (igual que antes) ---
#             day_of_week = current_time.weekday()
#             hour_of_day = current_time.hour
#             is_weekend = (day_of_week >= 5)
#             is_class_time = (not is_weekend) and \
#                             ((CLASS_START_M <= hour_of_day < CLASS_END_M) or \
#                              (CLASS_START_V <= hour_of_day < CLASS_END_V))
            
#             if is_class_time:
#                 is_occupied = random.random() < 0.95
#             else:
#                 is_occupied = random.random() < 0.01
            
#             # --- C. Simular Clima y A/C (igual que antes) ---
#             hour_fraction = (hour_of_day + current_time.minute / 60) / 24.0
#             temp_exterior, hum_exterior = simular_clima_exterior(hour_fraction)
            
#             is_ac_on = is_occupied and temp_interior > AC_THRESHOLD_TEMP
            
#             if is_ac_on:
#                 temp_interior += (AC_TARGET_TEMP - temp_interior) * 0.1 + random.uniform(-0.1, 0.1)
#                 hum_interior += (AC_TARGET_HUM - hum_interior) * 0.1 + random.uniform(-0.2, 0.2)
#             else:
#                 temp_interior += (temp_exterior - temp_interior) * 0.01 + random.uniform(-0.1, 0.1)
#                 hum_interior += (hum_exterior - hum_interior) * 0.01 + random.uniform(-0.2, 0.2)
            
#             hum_interior = max(40.0, min(99.9, hum_interior))

#             # --- D. SIMULACIÓN ELÉCTRICA MEJORADA ---
#             potencia_activa = POWER_BASE_LOAD
#             factor_potencia = POWER_FACTOR_BASE
            
#             if is_occupied:
#                 potencia_activa += POWER_PC_LOAD + random.uniform(-200, 200)
#                 factor_potencia = POWER_FACTOR_PC  # Los PCs tienen peor factor de potencia
            
#             if is_occupied:  # Luces solo cuando está ocupado
#                 potencia_activa += POWER_LIGHTS
            
#             if is_ac_on:
#                 potencia_activa += POWER_AC_LOAD + random.uniform(-100, 100)
#                 factor_potencia = POWER_FACTOR_AC  # A/C tiene su propio factor

#             # CÁLCULO DE CORRIENTE MEJORADO (considera factor de potencia)
#             potencia_aparente = potencia_activa / factor_potencia
#             corriente = potencia_aparente / VOLTAGE

#             # CÁLCULO DE ENERGÍA MEJORADO
#             incremento_energia = (potencia_activa / 1000.0) * (INTERVAL_SECONDS / 3600.0)
#             energia_total_acumulada += incremento_energia
#             energia_dia_actual += incremento_energia

#             # --- E. Sensores de Ocupación (igual que antes) ---
#             movimiento = 1 if is_occupied and random.random() < 0.8 else 0
            
#             if is_occupied:
#                 iluminacion = random.uniform(450, 600)
#             elif 7 <= hour_of_day < 18:
#                 iluminacion = random.uniform(100, 250)
#             else:
#                 iluminacion = random.uniform(0, 10)

#             # --- F. Escribir Fila ---
#             fecha_str = current_time.strftime('%Y-%m-%d')
#             hora_str = current_time.strftime('%H:%M:%S')
            
#             writer.writerow([
#                 DEVICE_ID, paquete_id, fecha_str, hora_str,
#                 round(temp_interior, 2),
#                 round(hum_interior, 2),
#                 round(corriente, 6),  # Más decimales para corriente realista
#                 round(potencia_activa, 2),
#                 round(energia_total_acumulada, 6),  # Energía total acumulada
#                 round(energia_dia_actual, 6),       # Energía del día actual
#                 round(iluminacion, 0),
#                 movimiento
#             ])
            
#             # --- G. Incrementar Tiempo ---
#             current_time += datetime.timedelta(seconds=INTERVAL_SECONDS)
#             paquete_id += 1
#             total_rows += 1
            
#             if total_rows % 100000 == 0:
#                 print(f"  ... {total_rows:,} registros generados ...")
#                 # Mostrar ejemplo de datos para verificar coherencia
#                 print(f"    Ejemplo - Potencia: {potencia_activa:.2f}W, Corriente: {corriente:.4f}A, Energía_Diaria: {energia_dia_actual:.4f}kWh")

#     end_gen_time = time.time()
#     print("-" * 50)
#     print("SIMULACIÓN CORREGIDA COMPLETADA")
#     print(f"Total registros: {total_rows:,}")
#     print(f"Energía total simulada: {energia_total_acumulada:.2f} kWh")
#     print(f"Tiempo: {end_gen_time - start_time:.2f} segundos")
#     print(f"Archivo: {OUTPUT_FILE}")

# if __name__ == "__main__":
#     main()