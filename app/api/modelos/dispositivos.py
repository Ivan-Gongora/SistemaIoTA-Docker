from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# ====================================================================
# MODELOS PRINCIPALES DE DISPOSITIVO (Unificados)
# ====================================================================

# Modelo base (sin ID)
class DispositivoBase(BaseModel):
    nombre: str
    descripcion: str
    tipo: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    # CRÍTICO: Debe ser bool para que Vue lo use directamente
    habilitado: bool 
    fecha_creacion: Optional[str] = ""
    proyecto_id: int

# Modelo para crear dispositivo
class DispositivoCrear(DispositivoBase):
    pass

# Modelo para actualizar parcialmente
class DispositivoActualizar(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    # 🚨 CRÍTICO: Permitir la actualización del estado habilitado
    habilitado: Optional[bool] = None 


# 🚨 MODELO DE RESPUESTA FINAL (Dispositivo con todos los campos de la DB)
class Dispositivo(DispositivoBase):
    id: int

    class Config:
        # 🚨 CORRECCIÓN CLAVE: Pydantic v1 -> Pydantic v2
        from_attributes = True 

# ====================================================================
# MODELOS RELACIONADOS (Optimizados y sin duplicación)
# ====================================================================

# 🚨 ELIMINACIÓN DE DUPLICADOS: (Eliminamos las clases Proyecto duplicadas)

class Sensor(BaseModel):
    id: int
    nombre: str
    dispositivo_id: int

    class Config:
        from_attributes = True

class CampoSensor(BaseModel):
    id: int
    nombre: str
    sensor_id: int

    class Config:
        from_attributes = True
# 🚨 NUEVO MODELO DE RESPUESTA EXTENDIDO
class DispositivoGeneral(Dispositivo): # Hereda todos los campos de Dispositivo
    nombre_proyecto: Optional[str] = None
    propietario_id: Optional[int] = None
    
    class Config:
        from_attributes = True 

# Si necesitas un modelo para los datos que vienen del CSV/simulación
class ValorSimuladoResponse(BaseModel):
    row_number: int
    fecha_hora_lectura: str
    status: str
    inserted_mappings: int
    dispositivo_id: int
    proyecto_id: int
    message: Optional[str] = None