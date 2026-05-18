from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any

from app.servicios.auth_utils import get_current_user_id
from app.servicios.servicio_permisos import verificar_permiso_proyecto, obtener_proyecto_id_desde_dispositivo
from app.servicios.analitica.servicio_extraccion import extraer_datos_dispositivo_df
from app.servicios.analitica.motor_inteligencia import MotorAnalisisCore

router_analitica = APIRouter()
motor = MotorAnalisisCore()

@router_analitica.get("/dispositivos/{dispositivo_id}/diagnostico")
async def obtener_diagnostico_salon(
    dispositivo_id: int,
    fecha_inicio: str = Query(..., description="Formato YYYY-MM-DD"),
    fecha_fin: str = Query(..., description="Formato YYYY-MM-DD"),
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Genera un diagnóstico completo del salón evaluando fugas, correlación y anomalías.
    """
    proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')
    
    df_actual = extraer_datos_dispositivo_df(dispositivo_id, fecha_inicio, fecha_fin)
    
    if df_actual.empty:
        raise HTTPException(status_code=404, detail="No existen registros en el rango de fechas seleccionado.")
        
    try:
        reporte = motor.generar_diagnostico_integral(df_actual)
        return {"status": "success", "data": reporte}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla interna en el procesamiento matemático: {str(e)}")

@router_analitica.get("/dispositivos/{dispositivo_id}/comparativa")
async def obtener_comparativa_periodos(
    dispositivo_id: int,
    fecha_inicio_base: str = Query(..., description="Inicio del periodo anterior"),
    fecha_fin_base: str = Query(..., description="Fin del periodo anterior"),
    fecha_inicio_eval: str = Query(..., description="Inicio del periodo actual"),
    fecha_fin_eval: str = Query(..., description="Fin del periodo actual"),
    current_user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Ejecuta la Prueba T de Student para validar si existe ahorro real entre dos periodos.
    """
    proyecto_id = await obtener_proyecto_id_desde_dispositivo(dispositivo_id)
    await verificar_permiso_proyecto(current_user_id, proyecto_id, 'VER_DATOS_IOT')
    
    df_base = extraer_datos_dispositivo_df(dispositivo_id, fecha_inicio_base, fecha_fin_base)
    df_eval = extraer_datos_dispositivo_df(dispositivo_id, fecha_inicio_eval, fecha_fin_eval)
    
    if df_base.empty or df_eval.empty:
        raise HTTPException(status_code=404, detail="Información insuficiente en uno de los periodos indicados.")
        
    try:
        comparativa = motor.evaluar_significancia_ahorro(df_base, df_eval)
        return {"status": "success", "data": comparativa}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla en el cálculo estadístico: {str(e)}")