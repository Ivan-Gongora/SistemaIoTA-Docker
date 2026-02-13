# app/api/modelos/campos_sensores.py

from pydantic import BaseModel
from typing import Optional, Union
from decimal import Decimal

# Modelo Base
class CampoSensorBase(BaseModel):
    nombre: str  # Ej: Temperatura Ambiente
    tipo_valor: str  # Ej: Float, Int, String
    sensor_id: int  # Clave foránea al sensor padre
    unidad_medida_id: Optional[int] = None  # Clave foránea a la unidad de medida
    nombre_unidad: Optional[str] = None
    simbolo_unidad: Optional[str] = None
    magnitud_tipo: Optional[str] = None

# Modelo para Crear
class CampoSensorCrear(CampoSensorBase):
    pass

# Modelo para Actualizar
class CampoSensorActualizar(BaseModel):
    nombre: Optional[str] = None
    tipo_valor: Optional[str] = None
    unidad_medida_id: Optional[int] = None

# Modelo de Respuesta (Lo que la API devuelve)
class CampoSensor(CampoSensorBase):
    id: int
    
    # Datos extra del JOIN con unidades_medida
    nombre_unidad: Optional[str] = None
    simbolo_unidad: Optional[str] = None
    magnitud_tipo: Optional[str] = None
    ultimo_valor: Optional[Union[str, Decimal, float]] = None  # ✅ ACEPTA Decimal
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)  # ✅ CONVIERTE Decimal a string en JSON
        }


# # app/api/modelos/campos_sensores.py

# from decimal import Decimal
# from pydantic import BaseModel
# from typing import Optional

# from pyparsing import Union

# # Modelo Base
# class CampoSensorBase(BaseModel):
#     nombre: str # Ej: Temperatura Ambiente
#     tipo_valor: str # Ej: Float, Int, String
#     sensor_id: int # Clave foránea al sensor padre
#     unidad_medida_id: Optional[int] = None  # Clave foránea a la unidad de medida
#     nombre_unidad: Optional[str] = None
#     simbolo_unidad: Optional[str] = None
#     magnitud_tipo: Optional[str] = None
# # Modelo para Crear
# class CampoSensorCrear(CampoSensorBase):
#     pass
    
# # Modelo para Actualizar
# class CampoSensorActualizar(BaseModel):
#     nombre: Optional[str] = None
#     tipo_valor: Optional[str] = None
#     unidad_medida_id: Optional[int] = None

# # Modelo de Respuesta (Lo que la API devuelve)
# class CampoSensor(CampoSensorBase):
#     id: int
    
#     # Datos extra del JOIN con unidades_medida
#     nombre_unidad: Optional[str] = None
#     simbolo_unidad: Optional[str] = None
#     magnitud_tipo: Optional[str] = None
#     ultimo_valor:  Optional[Union[str, float, Decimal]] # Pydantic lo recibe como string (de la DB)
#     class Config:
#         from_attributes = True