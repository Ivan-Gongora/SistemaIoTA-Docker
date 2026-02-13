import csv
import datetime
import random
import math
import time

# --- 1. CONFIGURACIÓN DE LA SIMULACIÓN ---
DEVICE_ID = 1
SIMULATION_DAYS = 7  # SOLO 7 DÍAS PARA PRUEBA
INTERVAL_SECONDS = 5
OUTPUT_FILE = 'simulacion_aula_7dias_realista.csv'

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
POWER_BASE_LOAD = 50      # 50W - MUCHO MÁS REALISTA

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
    print(f"🎯 GENERANDO 7 DÍAS DE DATOS REALISTAS...")
    print(f"📊 Dispositivo: {DEVICE_ID}")
    print(f"⏱️  Intervalo: {INTERVAL_SECONDS} segundos")
    print(f"💾 Archivo: {OUTPUT_FILE}")
    print("=" * 50)
    
    start_time = time.time()
    current_time = datetime.datetime(2025, 10, 1, 0, 0, 0)
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

            # Sensor BH1750 - iluminación realista
            if is_occupied:
                # Ocupación: iluminación artificial
                if 18 <= hour_of_day < 22:  # Noche: iluminación completa
                    iluminacion = random.randint(400, 600)
                else:  # Día: mezcla de natural y artificial
                    iluminacion = random.randint(300, 500)
            else:
                # Aula vacía
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
                    # Noche: posible luz de seguridad o oscuridad
                    iluminacion = random.randint(0, 50) if random.random() < 0.1 else 0

            # --- F. Escribir Fila ---
            fecha_str = current_time.strftime('%Y-%m-%d')
            hora_str = current_time.strftime('%H:%M:%S')
            
            writer.writerow([
                DEVICE_ID, 
                paquete_id, 
                fecha_str, 
                hora_str,
                round(temp_interior, 1),      # DHT22 - 1 decimal
                round(hum_interior, 1),       # DHT22 - 1 decimal
                round(corriente, 2),          # SCT-013-000 - 2 decimales
                round(potencia_activa, 1),    # SCT-013-000 - 1 decimal
                f"{energia_intervalo:.8f}",   # Energía en formato decimal fijo
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

if __name__ == "__main__":
    main()