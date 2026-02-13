from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime # Importar date y datetime

# ====================================================================
# MODELOS DE BASE DE DATOS Y RECEPCIÓN DE DATOS (Interpreta la DB)
# ====================================================================

# Modelo base para los datos de recibos (campos que esperamos del DB)
class ReciboEnergiaBase(BaseModel):
    # Usamos `date` de datetime.date para periodos para que Pydantic lo valide como fecha
    periodo: date = Field(..., description="Fecha de cierre del periodo de facturación (YYYY-MM-DD)")
    consumo_total_kwh: float = Field(..., gt=0, description="Consumo total de energía en kWh")
    demanda_maxima_kw: float = Field(..., gt=0, description="Demanda máxima de potencia en kW")
    costo_total: float = Field(..., gt=0, description="Costo total del recibo")
    dias_facturados: int = Field(..., gt=0, le=31, description="Número de días facturados en el periodo") # Max 31 días
    factor_potencia: Optional[float] = Field(None, ge=0, le=100, description="Factor de potencia, en %") # Opcional, 0-100
    tarifa: Optional[str] = Field(None, max_length=50, description="Tipo de tarifa aplicada") # Opcional
    kwh_punta: Optional[float] = Field(None, ge=0, description="Consumo en horario punta en kWh") # Opcional

# Modelo para crear un recibo (usado para la inserción en la DB)
class ReciboEnergiaCrear(ReciboEnergiaBase):
    usuario_id: int = Field(..., description="ID del usuario al que pertenece el recibo")
    fecha_carga: datetime = Field(..., description="Fecha y hora de carga del recibo")
    lote_nombre: str = Field(..., max_length=255, description="Nombre del lote al que pertenece el recibo")

# Modelo de respuesta para un recibo ya en la BD (incluye ID de la BD)
class ReciboEnergia(ReciboEnergiaCrear):
    id: int = Field(..., description="ID único del recibo en la base de datos")

    class Config:
        from_attributes = True

# Modelo para la respuesta del endpoint de lotes (una lista de strings)
class LotesResponse(BaseModel):
    lotes: List[str] = Field(..., description="Lista de nombres de lotes cargados por el usuario")

# -----------------------------------------------------------------
# 🎯 MODELOS DE SIMULACIÓN Y ANÁLISIS
# -----------------------------------------------------------------

class EscenarioPayload(BaseModel):
    """
    Parámetros de entrada para la simulación de escenarios energéticos.
    Los valores de tasas son porcentajes expresados como decimales (ej: 0.05 = 5%).
    """
    
    # Parámetros del escenario
    tasa_inflacion_energetica: float = Field(
        default=0.0, 
        description="Inflación anual esperada del costo_por_kwh (ej: 0.08 para 8%)",
        ge=0.0,
        le=0.5
    )
    
    tasa_crecimiento_consumo: float = Field(
        default=0.0,
        description="Crecimiento anual esperado del consumo base (ej: 0.10 para 10%)",
        ge=-0.5,
        le=0.5 
    )
    
    mejora_eficiencia_consumo: float = Field(
        default=0.0,
        description="Reducción porcentual fija del consumo por eficiencia (ej: 0.15 para 15%)",
        ge=0.0,
        le=1.0
    )

    # Parámetros de selección de datos y horizonte de proyección
    lotes_seleccionados: Optional[List[str]] = Field(
        default=None,
        description="Lista de nombres de lotes específicos para el análisis."
    )

    meses_a_predecir: int = Field(
        default=12,
        description="Número de meses futuros para los que se desea generar el escenario.",
        ge=1,   
        le=120   # ⬅️ Límite máximo de 10 años
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tasa_inflacion_energetica": 0.075,
                "tasa_crecimiento_consumo": 0.05,
                "mejora_eficiencia_consumo": 0.10,
                "lotes_seleccionados": ["default", "Recibos 2025 IA"],
                "meses_a_predecir": 60
            }
        }

# -----------------------------------------------------------------
# 🎯 NUEVO: Modelo para enviar lotes a los endpoints de Análisis IA
# -----------------------------------------------------------------
class AnalisisPayload(BaseModel):
    """
    Parámetros de entrada para los endpoints de análisis de IA que solo requieren lotes.
    """
    lotes_seleccionados: Optional[List[str]] = Field(
        default=None,
        description="Lista de nombres de lotes específicos para el análisis. Si es None o vacía, se analizarán todos los lotes disponibles."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "lotes_seleccionados": ["default"]
            }
        }

class ReciboEnergiaModelo(BaseModel):
    """Modelo Pydantic para los datos recuperados de MySQL."""
    id: int
    usuario_id: int
    periodo: date # Ya viene como objeto date de MySQL/PyMySQL
    consumo_total_kwh: float
    demanda_maxima_kw: float
    costo_total: float
    dias_facturados: int
    factor_potencia: Optional[float] = None
    tarifa: Optional[str] = None
    kwh_punta: Optional[float] = None
    fecha_carga: datetime
    lote_nombre: str

    class Config:
        from_attributes = True # Permite mapeo desde resultados de cursor (si es DictCursor)
        # O from_orm si usaras SQLAlchemy, pero en PyMySQL ayuda a la serialización.