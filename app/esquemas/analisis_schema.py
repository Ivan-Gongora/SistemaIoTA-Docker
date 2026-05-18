from pydantic import BaseModel
from typing import Optional

class AnalisisIndividualRequest(BaseModel):
    dispositivo_id: int
    fecha_inicio: str # Formato 'YYYY-MM-DD HH:MM:SS'
    fecha_fin: str
    dias_mes_normalizacion: int = 31 # Para ajustar meses de 28/31 días
    mes_tarifa: str = 'octubre' # Para elegir la tarifa CFE

class AnalisisComparativoRequest(BaseModel):
    dispositivo_base_id: int
    dispositivo_ctrl_id: int
    fecha_inicio: str
    fecha_fin: str
    mes_tarifa: str = 'octubre'