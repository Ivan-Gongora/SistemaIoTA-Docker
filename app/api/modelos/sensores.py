# app/api/modelos/sensores.py

from pydantic import BaseModel
from typing import Optional,List
from app.api.modelos.campos_sensores import CampoSensorCrear # 🚨 Importar el modelo
# Modelo Base
class SensorBase(BaseModel):
    dispositivo_id: int # 🚨 Asegurar que el tipo sea 'int'
    nombre: str
    tipo: str # Ej: Temperatura/Humedad
    habilitado: Optional[bool] = True
    dispositivo_id: int # Clave foránea al dispositivo

# Modelo para Crear
class SensorCrear(SensorBase):
    # 🚨 CRÍTICO: Añadir la lista de campos para el payload
    campos: List[CampoSensorCrear] = [] 
    pass
    
# Modelo para Actualizar
class SensorActualizar(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    habilitado: Optional[bool] = None

# Modelo de Respuesta Final
class Sensor(SensorBase):
    id: int
    fecha_creacion: Optional[str] = "" # Vendrá de la DB como string
    total_campos: Optional[int] = 0
    class Config:
        from_attributes = True
 
# Modelo de Respuesta con Información Adicional       
class SensorGeneral(Sensor):
    nombre_dispositivo: Optional[str] = None
    nombre_proyecto: Optional[str] = None
    proyecto_id: Optional[int] = None
    
    class Config:
        from_attributes = True
        

# Este incluye los campos extra que trae tu consulta SQL avanzada
class SensorVistaGeneral(Sensor):
    nombre_dispositivo: str
    nombre_proyecto: str
    propietario_id: int
    
    # 🚨 LOS CAMPOS QUE FALTABAN:
    total_campos: int = 0
    mi_rol: str = "Observador" 

    class Config:
        from_attributes = True
        
class RespuestaPaginadaSensores(BaseModel):
    data: List[SensorVistaGeneral] # 👈 Usa el modelo enriquecido
    total: int
    page: int
    limit: int
    total_pages: int