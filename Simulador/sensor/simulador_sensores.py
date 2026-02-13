import requests
import time
import random
from datetime import datetime

# Endpoint donde se enviarán los datos simulados
ENDPOINT = "http://3.236.53.192:8001/api/guardar_json/"

# IDs reales existentes en el sistema
PROYECTO_ID = "1"
DISPOSITIVO_ID = "1"

# Variables para energía acumulada y id de paquete
energia_acumulada = 0.0
id_paquete = 1

def generar_datos_dht22():
    temperatura = round(random.uniform(20.0, 35.0), 2)
    humedad = round(random.uniform(30.0, 95.0), 2)
    return temperatura, humedad

def generar_datos_sct013():
    global energia_acumulada
    
    # Corriente simulada
    corriente = round(random.uniform(0.5, 10.0), 2)
    
    # Asumiendo voltaje constante de 120V para México
    voltaje = 120
    
    # Potencia = Voltaje * Corriente (Ley de Ohm)
    potencia = round(voltaje * corriente, 2)
    
    # Energía acumulada en kWh = Potencia(kW) * Tiempo(h)
    energia_acumulada += (potencia / 1000) * (5 / 3600)  # acumulando por periodo de 5s
    energia = round(energia_acumulada, 4)
    
    return energia, corriente, potencia

def generar_datos_bh1750():
    iluminacion = round(random.uniform(50, 1200), 0)
    return iluminacion

def generar_datos_pir():
    movimiento = random.randint(0, 1)
    return movimiento

while True:
    # Obtener fecha y hora actual
    ahora = datetime.now()
    fecha = ahora.strftime("%Y-%m-%d")
    hora = ahora.strftime("%H:%M:%S")

    # Generar datos de sensores
    temp, hum = generar_datos_dht22()
    energia, corriente, potencia = generar_datos_sct013()
    iluminacion = generar_datos_bh1750()
    movimiento = generar_datos_pir()

    # Estructura JSON según requerimiento
    payload = {
        "proyecto": PROYECTO_ID,
        "dispositivo": DISPOSITIVO_ID,
        "fecha": fecha,
        "hora": hora,
        "id_paquete": id_paquete,
        "sensores": [
            {
                "nombre": "DHT22",
                "datos": {
                    "Temperatura": temp,
                    "Humedad": hum
                }
            },
            {
                "nombre": "SCT-013-000",
                "datos": {
                    "Energia": energia,
                    "Corriente": corriente,
                    "Potencia": potencia
                }
            },
            {
                "nombre": "BH1750",
                "datos": {
                    "Iluminacion": iluminacion
                }
            },
            {
                "nombre": "PIR HC-SR501",
                "datos": {
                    "Movimiento": movimiento
                }
            }
        ]
    }

    # Enviar POST
    try:
        respuesta = requests.post(ENDPOINT, json=payload)
        print(f"Datos enviados | Paquete #{id_paquete} | Estado HTTP: {respuesta.status_code}")
        print(payload)
    except Exception as e:
        print(f"Error al enviar datos: {e}")

    # Incrementar id_paquete tras cada envío
    id_paquete += 1

    # Esperar 5 segundos antes de próxima lectura/envío
    time.sleep(5)
