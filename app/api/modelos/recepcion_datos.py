# app/api/modelos/recepcion_datos.py

from pydantic import BaseModel
from typing import List, Dict, Any

# Define la estructura de un solo sensor en el payload
class SensorData(BaseModel):
    nombre: str
    datos: Dict[str, Any] # Ej: {"Temperatura": 26.3, "Humedad": 75.4}

# Define la estructura del payload completo
class PayloadDispositivo(BaseModel):
    proyecto: str       # ID del Proyecto (como string)
    dispositivo: str    # ID del Dispositivo (como string)
    fecha: str          # Formato YYYY-MM-DD
    hora: str           # Formato HH:MM:SS
    id_paquete: int
    sensores: List[SensorData]