from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from app.servicios.servicio_agregacion import ejecutar_agregacion_horaria

router_agregacion = APIRouter()

@router_agregacion.post("/agregacion/forzar")
async def forzar_agregacion_datos(
    procesar_historico: bool = Query(False, description="Activa el modo de busqueda hacia atras"),
    dias_historia: int = Query(30, description="Cantidad de dias previos a procesar"),
    fecha_inicio: Optional[str] = Query(None, description="Formato YYYY-MM-DD"),
    fecha_fin: Optional[str] = Query(None, description="Formato YYYY-MM-DD")
) -> Dict[str, Any]:
    """
    Ruta para ejecutar de manera manual el empaquetado de datos.
    Acepta un inicio y un fin para atender meses anteriores sin modificar el flujo horario normal.
    """
    try:
        resultado = await ejecutar_agregacion_horaria(
            procesar_historico=procesar_historico,
            dias_historia=dias_historia,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        if resultado.get("status") == "error":
            raise HTTPException(status_code=500, detail=resultado.get("message"))
            
        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla en el proceso de solicitud manual: {str(e)}")