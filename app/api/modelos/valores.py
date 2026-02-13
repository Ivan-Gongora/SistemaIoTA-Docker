# app/api/modelos/valores.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class ValorBase(BaseModel):
    valor: Decimal
    fecha_hora_lectura: datetime
    campo_id: int

class ValorCrear(ValorBase):
    pass

class Valor(ValorBase):
    id: int
    fecha_hora_registro: datetime
    magnitud_tipo: Optional[str] = None  # Del JOIN con unidades_medida
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: str(v)  # Convierte Decimal a string en JSON
        }