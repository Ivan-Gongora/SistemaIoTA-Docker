# app/api/modelos/dashboard.py
from pydantic import BaseModel
from datetime import datetime

class ActividadRecienteItem(BaseModel):
    tipo: str       # Ej: 'lote_energia' o 'nuevo_dispositivo'
    titulo: str     # Ej: "Lote: CFE Octubre" o "NodeMCU Zona Norte"
    fuente: str    # Ej: "Módulo Energía" o "Proyecto: Invernadero"
    fecha: datetime
class ResumenKPIs(BaseModel):
    conteo_proyectos_iot: int
    conteo_dispositivos_iot: int
    conteo_lotes_energia: int
    conteo_simulaciones: int # (Lo dejaremos en 0 por ahora)
    
    # (Añadir a tu archivo de modelos de dashboard)
class EstadoDispositivos(BaseModel):
    activos: int
    total: int