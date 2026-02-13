import csv
import datetime
import random
import math
import time

# --- 1. CONFIGURACIÓN DE LA SIMULACIÓN ---

DEVICE_ID = 1  # ID del dispositivo a simular
SIMULATION_DAYS = 30  # Duración de la simulación
INTERVAL_SECONDS = 5  # Intervalo de lectura
OUTPUT_FILE = 'simulacion_aula_1mes.csv'

# --- 2. CONSTANTES DEL AULA (BASADO EN TU INVESTIGACIÓN) ---

# Horarios de clase (Lunes a Viernes)
CLASS_START_M = 7  # 7:00 AM
CLASS_END_M = 14   # 2:00 PM
CLASS_START_V = 14 # 2:00 PM
CLASS_END_V = 22   # 10:00 PM

# Clima Base (Otoño en Chetumal)
TEMP_EXT_MIN = 19.0 # Mínima nocturna
TEMP_EXT_MAX = 30.0 # Máxima diurna
HUM_EXT_MIN = 75.0  # Humedad exterior mínima
HUM_EXT_MAX = 85.0  # Humedad exterior máxima

# Lógica del Aire Acondicionado (A/C)
AC_THRESHOLD_TEMP = 25.0 # Temp. interior para encender el A/C
AC_TARGET_TEMP = 22.0    # Temp. objetivo del A/C
AC_TARGET_HUM = 60.0     # Humedad objetivo del A/C

# Carga Eléctrica (en Watts)
POWER_BASE_LOAD = 250    # Carga base (PCs en standby, router, etc.)
POWER_PC_LOAD = 2500     # Carga de 15-20 PCs, proyector y cargadores
POWER_LIGHTS = 500       # Luces del aula
POWER_AC_LOAD = 5500     # 2.5 A/C de 20,000 BTU (~2200W c/u)
VOLTAGE = 220.0          # Voltaje de la línea de A/C

# --- 3. FUNCIONES DE SIMULACIÓN ---

def simular_clima_exterior(hour_fraction):
    """Calcula la temperatura exterior basada en una curva sinusoidal."""
    # Simula el pico de temp. a las 3 PM (0.625 de 24h)
    sin_wave = math.sin(math.pi * (hour_fraction - 0.25) * 2) 
    temp_range = (TEMP_EXT_MAX - TEMP_EXT_MIN) / 2
    temp_avg = (TEMP_EXT_MAX + TEMP_EXT_MIN) / 2
    
    # Añade ruido aleatorio
    temp_exterior = temp_avg + temp_range * sin_wave + random.uniform(-0.5, 0.5)
    hum_exterior = random.uniform(HUM_EXT_MIN, HUM_EXT_MAX)
    
    return temp_exterior, hum_exterior

def main():
    print(f"Iniciando simulación de {SIMULATION_DAYS} días...")
    print(f"Intervalo: {INTERVAL_SECONDS} seg. | Generando aprox. {int(SIMULATION_DAYS * 24 * 60 * 60 / INTERVAL_SECONDS * 7)} registros.")
    print(f"Archivo de salida: {OUTPUT_FILE}")
    
    start_time = time.time()
    
    # Inicialización de variables de estado
    current_time = datetime.datetime(2025, 10, 1, 0, 0, 0) # Inicia en Octubre (Otoño)
    end_time = current_time + datetime.timedelta(days=SIMULATION_DAYS)
    paquete_id = 1
    energia_acumulada = 0.0
    
    # Estado inicial del aula
    temp_interior = 24.0
    hum_interior = 80.0
    
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
            
            # --- A. Determinar el Estado del Aula ---
            day_of_week = current_time.weekday() # 0=Lunes, 6=Domingo
            hour_of_day = current_time.hour
            
            is_weekend = (day_of_week >= 5) # Sábado o Domingo
            
            is_class_time = (not is_weekend) and \
                            ((CLASS_START_M <= hour_of_day < CLASS_END_M) or \
                             (CLASS_START_V <= hour_of_day < CLASS_END_V))
            
            # Simular ocupación (95% probable en horario de clase, 1% de noche)
            if is_class_time:
                is_occupied = random.random() < 0.95
            else:
                is_occupied = random.random() < 0.01 # (Ej. personal de limpieza)
            
            # --- B. Simular Clima y A/C ---
            hour_fraction = (hour_of_day + current_time.minute / 60) / 24.0
            temp_exterior, hum_exterior = simular_clima_exterior(hour_fraction)
            
            # CÓDIGO CORREGIDO:
            is_ac_on = is_occupied and temp_interior > AC_THRESHOLD_TEMP
            
            # Ajustar temperatura interior
            if is_ac_on:
                # El A/C enfría activamente
                temp_interior += (AC_TARGET_TEMP - temp_interior) * 0.1 + random.uniform(-0.1, 0.1)
                hum_interior += (AC_TARGET_HUM - hum_interior) * 0.1 + random.uniform(-0.2, 0.2)
            else:
                # El A/C está apagado, el aula tiende a la temp. exterior
                temp_interior += (temp_exterior - temp_interior) * 0.01 + random.uniform(-0.1, 0.1)
                hum_interior += (hum_exterior - hum_interior) * 0.01 + random.uniform(-0.2, 0.2)
            
            # Limitar valores de humedad
            hum_interior = max(40.0, min(99.9, hum_interior))

            # --- C. Simular Carga Eléctrica ---
            potencia = POWER_BASE_LOAD
            is_lights_on = is_occupied
            
            if is_occupied:
                potencia += POWER_PC_LOAD + random.uniform(-200, 200) # PCs, proyector, cargadores
            
            if is_lights_on:
                potencia += POWER_LIGHTS
            
            if is_ac_on:
                potencia += POWER_AC_LOAD + random.uniform(-100, 100) # Carga masiva del A/C
            
            corriente = potencia / VOLTAGE
            # (Potencia en kW) * (intervalo en horas)
            energia_acumulada += (potencia / 1000.0) * (INTERVAL_SECONDS / 3600.0)

            # --- D. Simular Sensores de Ocupación ---
            
            # Movimiento: 80% probable si está ocupado
            movimiento = 1 if is_occupied and random.random() < 0.8 else 0
            
            # Iluminación
            if is_lights_on:
                iluminacion = random.uniform(450, 600) # Luz artificial + natural (si es de día)
            elif 7 <= hour_of_day < 18:
                iluminacion = random.uniform(100, 250) # Vacío pero con luz de día
            else:
                iluminacion = random.uniform(0, 10) # Vacío de noche

            # --- E. Escribir Fila en CSV ---
            fecha_str = current_time.strftime('%Y-%m-%d')
            hora_str = current_time.strftime('%H:%M:%S')
            
            # Escribir los 7 campos de datos
            writer.writerow([
                DEVICE_ID, paquete_id, fecha_str, hora_str,
                round(temp_interior, 2),
                round(hum_interior, 2),
                round(corriente, 2),
                round(potencia, 2),
                round(energia_acumulada, 2),
                round(iluminacion, 0),
                movimiento
            ])
            
            # --- F. Incrementar Tiempo ---
            current_time += datetime.timedelta(seconds=INTERVAL_SECONDS)
            paquete_id += 1
            total_rows += 1
            
            if total_rows % 100000 == 0:
                print(f"  ... {total_rows:,} registros generados ...")

    end_gen_time = time.time()
    print("-" * 30)
    print("Simulación completada.")
    print(f"Total de registros generados: {total_rows:,}")
    print(f"Tiempo de generación: {end_gen_time - start_time:.2f} segundos.")
    print(f"Datos guardados en: {OUTPUT_FILE}")

# --- 4. EJECUTAR EL SCRIPT ---
if __name__ == "__main__":
    main()