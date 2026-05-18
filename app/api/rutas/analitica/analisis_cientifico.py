from fastapi import APIRouter, Depends, HTTPException
from app.esquemas.analisis_schema import AnalisisIndividualRequest, AnalisisComparativoRequest
from app.servicios.servicio_analisis import MotorAnalisisEnergetico

router_cientifico = APIRouter()
motor_analisis = MotorAnalisisEnergetico()

@router_cientifico.post("/analisis/individual")
async def endpoint_analisis_individual(request: AnalisisIndividualRequest):
    try:
        resultado = motor_analisis.generar_analisis_individual(
            dispositivo_id=request.dispositivo_id,
            fecha_ini=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            dias_totales=request.dias_mes_normalizacion
        )
        if "error" in resultado:
            raise HTTPException(status_code=404, detail=resultado["error"])
        
        return {"status": "success", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router_cientifico.post("/analisis/comparativo")
async def endpoint_analisis_comparativo(request: AnalisisComparativoRequest):
    try:
        resultado = motor_analisis.generar_analisis_comparativo(
            id_base=request.dispositivo_base_id,
            id_ctrl=request.dispositivo_ctrl_id,
            fecha_ini=request.fecha_inicio,
            fecha_fin=request.fecha_fin
        )
        if "error" in resultado:
            raise HTTPException(status_code=404, detail=resultado["error"])
            
        return {"status": "success", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))