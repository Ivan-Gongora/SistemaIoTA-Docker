import csv
import requests
import time
import sys
import asyncio
import aiohttp

# --- Configuración ---
API_URL = "http://127.0.0.1:8001/api/guardar_json/"
CSV_FILE = "DATOS2_2.csv"
ID_PROYECTO_PRUEBA = "1" # Basado en tu JSON de ejemplo
ID_D9SPOSITIVO_PRUEBA = "1" # Basado en tu JSON de ejemplo
MAX_CONCURRENT_REQUESTS = 100 # Número de solicitudes a enviar al mismo tiempo
# ---------------------

def transformar_fila_a_json(row):
    """
    Convierte una fila del CSV al formato JSON anidado que espera la API.
    (Misma función que antes, corrigiendo el error de 'Iluminacion')
    """
    try:
        payload = {
            "proyecto": ID_PROYECTO_PRUEBA,
            "dispositivo": ID_D9SPOSITIVO_PRUEBA, 
            "fecha": row['Fecha'],
            "hora": row['Hora'],
            "id_paquete": int(row['Paquete_id']),
            "sensores": [
                {
                    "nombre": "DHT22",
                    "datos": {
                        "Temperatura": float(row['Temperatura']),
                        "Humedad": float(row['Humedad'])
                    }
                },
                {
                    "nombre": "SCT-013-000",
                    "datos": {
                        "Energia": float(row['Corriente']),
                        "Corriente": float(row['Potencia']),
                        "Potencia": float(row['Energia'])
                    }
                },
                {
                    "nombre": "BH1750",
                    "datos": {
                        "Iluminacion": int(float(row['Iluminacion'])) # Convertir 128.0 -> 128
                    }
                },
                {
                    "nombre": "PIR HC-SR501",
                    "datos": {
                        "Movimiento": int(row['Movimiento'])
                    }
                }
            ]
        }
        return payload
    except (ValueError, KeyError) as e:
        print(f"Error procesando fila {row['Paquete_id']}: {e}", file=sys.stderr)
        return None

async def send_request(session, payload, semaphore):
    """
    Envía una única solicitud POST usando la sesión y el semáforo.
    """
    # Espera a que el semáforo libere un "espacio"
    async with semaphore:
        try:
            async with session.post(API_URL, json=payload, timeout=30) as response:
                if response.status != 200 and response.status != 201:
                    # Imprime el error pero no detiene la carga
                    print(f"Error en Paquete {payload['id_paquete']}: HTTP {response.status}", file=sys.stderr)
                return response.status
        except Exception as e:
            print(f"Error de conexión en Paquete {payload['id_paquete']}: {e}", file=sys.stderr)
            return None # Retorna None si la solicitud falla

async def main():
    print("Iniciando carga masiva de datos...")
    
    # --- 1. Leer y transformar todos los datos del CSV ---
    print(f"Leyendo y preparando datos desde '{CSV_FILE}'...")
    payloads = []
    try:
        with open(CSV_FILE, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                json_data = transformar_fila_a_json(row)
                if json_data:
                    payloads.append(json_data)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{CSV_FILE}'.")
        return
    
    total_requests = len(payloads)
    if total_requests == 0:
        print("No se encontraron datos válidos para enviar.")
        return
        
    print(f"Se prepararon {total_requests:,} solicitudes JSON.")
    print(f"Iniciando envío concurrente (Lotes de {MAX_CONCURRENT_REQUESTS})...")
    
    # --- 2. Preparar la sesión asíncrona ---
    
    # Un semáforo limita cuántas solicitudes se ejecutan al mismo tiempo
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    tasks = []
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Crear todas las "tareas" (una por cada solicitud)
        for payload in payloads:
            tasks.append(send_request(session, payload, semaphore))
        
        # Ejecutar todas las tareas concurrentemente
        results = await asyncio.gather(*tasks)

    # --- 3. Reportar resultados ---
    end_time = time.time()
    
    count_success = sum(1 for r in results if r in (200, 201))
    count_fail = total_requests - count_success
    
    print("\n" + "="*30)
    print("Carga masiva completada.")
    print(f"Tiempo total: {end_time - start_time:.2f} segundos.")
    print(f"Total de solicitudes enviadas: {total_requests:,}")
    print(f"Registros exitosos (200/201): {count_success:,}")
    print(f"Registros fallidos (Error/Timeout): {count_fail:,}")
    
    if count_fail > 0:
        print("\nRevise los errores impresos arriba para más detalles.")

# --- Ejecutar el script asíncrono ---
if __name__ == "__main__":
    asyncio.run(main())


# import csv
# import requests
# import time
# import sys

# # --- Configuración ---
# API_URL = "http://127.0.0.1:8001/api/guardar_json/"
# CSV_FILE = "simulacion_aula_1mes.csv"
# ID_PROYECTO_PRUEBA = "1" # Basado en tu JSON de ejemplo
# # ---------------------

# def transformar_fila_a_json(row):
#     """
#     Convierte una fila del CSV al formato JSON anidado que espera la API.
#     """
#     try:
#         payload = {
#             "proyecto": ID_PROYECTO_PRUEBA,
#             "dispositivo": row['Dispositivo_id'], # Tomado del CSV
#             "fecha": row['Fecha'],
#             "hora": row['Hora'],
#             "id_paquete": int(row['Paquete_id']),
#             "sensores": [
#                 {
#                     "nombre": "DHT22",
#                     "datos": {
#                         "Temperatura": float(row['Temperatura']),
#                         "Humedad": float(row['Humedad'])
#                     }
#                 },
#                 {
#                     "nombre": "SCT-013-000",
#                     "datos": {
#                         "Energia": float(row['Energia']),
#                         "Corriente": float(row['Corriente']),
#                         "Potencia": float(row['Potencia'])
#                     }
#                 },
#                 {
#                     "nombre": "BH1750",
#                     "datos": {
#                         "Iluminacion": int(float(row['Iluminacion']))
#                     }
#                 },
#                 {
#                     "nombre": "PIR HC-SR501",
#                     "datos": {
#                         "Movimiento": int(row['Movimiento'])
#                     }
#                 }
#             ]
#         }
#         return payload
#     except ValueError as e:
#         print(f"Error de conversión de datos en fila: {row}. Error: {e}")
#         return None
#     except KeyError as e:
#         print(f"Error: La columna {e} no se encuentra en el CSV.")
#         return None

# def iniciar_carga():
#     print(f"Iniciando carga de datos desde '{CSV_FILE}' al endpoint '{API_URL}'...")
    
#     try:
#         with open(CSV_FILE, mode='r') as f:
#             # Usamos DictReader para leer el CSV usando los nombres de las columnas
#             reader = csv.DictReader(f)
            
#             count_success = 0
#             count_fail = 0
#             total_rows = 0
#             start_time = time.time()

#             for row in reader:
#                 total_rows += 1
                
#                 # 1. Transformar la fila a JSON
#                 payload = transformar_fila_a_json(row)
#                 if payload is None:
#                     count_fail += 1
#                     continue

#                 # 2. Enviar los datos a la API (POST)
#                 try:
#                     # Usamos 'json=payload' para que requests maneje la serialización
#                     response = requests.post(API_URL, json=payload, timeout=10)
                    
#                     if response.status_code == 200 or response.status_code == 201:
#                         count_success += 1
#                     else:
#                         # Imprimir el primer error y detenerse
#                         print(f"\n¡Error de API! El servidor respondió con: {response.status_code}")
#                         print(f"Respuesta: {response.text}")
#                         print(f"Payload enviado: {payload}")
#                         count_fail += 1
#                         # Descomenta la siguiente línea si quieres que el script se detenga al primer error
#                         # raise Exception("Detenido por error de API")

#                 except requests.exceptions.RequestException as e:
#                     print(f"\nError de conexión: {e}")
#                     print("El script se detendrá. Verifica que la API (FastAPI) esté corriendo.")
#                     sys.exit() # Detener el script si la API no está disponible

#                 # 3. Reportar progreso
#                 if total_rows % 1000 == 0:
#                     print(f"  ... {total_rows:,} registros procesados ({count_success} exitosos, {count_fail} fallidos) ...")

#             end_time = time.time()
#             print("\n" + "="*30)
#             print("Carga de datos completada.")
#             print(f"Total de filas leídas: {total_rows:,}")
#             print(f"Registros exitosos (200 OK): {count_success:,}")
#             print(f"Registros fallidos: {count_fail:,}")
#             print(f"Tiempo total: {end_time - start_time:.2f} segundos.")

#     except FileNotFoundError:
#         print(f"Error: No se encontró el archivo '{CSV_FILE}'.")
#         print("Asegúrate de que el script esté en la misma carpeta que el CSV.")
#     except Exception as e:
#         print(f"Error inesperado: {e}")

# # --- Ejecutar el script ---
# if __name__ == "__main__":
#     iniciar_carga()