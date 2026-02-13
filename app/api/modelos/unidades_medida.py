# app/api/modelos/unidades_medida.py

from pydantic import BaseModel
from typing import Optional

# Modelo Base
class UnidadMedidaBase(BaseModel):
    nombre: str
    simbolo: str
    descripcion: Optional[str] = None
    magnitud_tipo: str
# Modelo para Crear (hereda de Base)
class UnidadMedidaCrear(UnidadMedidaBase):
    pass
    
# Modelo para Actualizar (campos opcionales)
class UnidadMedidaActualizar(BaseModel):
    nombre: Optional[str] = None
    simbolo: Optional[str] = None
    descripcion: Optional[str] = None
    magnitud_tipo: str
# Modelo de Respuesta (Incluye el ID)
class UnidadMedida(UnidadMedidaBase):
    id: int

    class Config:
        from_attributes = True