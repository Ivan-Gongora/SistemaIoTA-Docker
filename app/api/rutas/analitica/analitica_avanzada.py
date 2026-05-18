from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.servicios.analitica.motor_inteligencia import MotorInteligenciaIoT

router_analitica_pro = APIRouter()
motor = MotorInteligenciaIoT()

@router_analitica_pro.post("/pearson-influencia")
async def calcular_influencia_ambiental(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Ruta para la Capa 2. Ejecuta el Coeficiente de Pearson.
    """
    datos = payload.get("datos", [])
    if not datos:
        raise HTTPException(status_code=400, detail="El arreglo de datos está vacío.")

    try:
        df_limpio = motor.limpiar_serie_temporal(datos)
        resultado = motor.calcular_influencia_pearson(df_limpio)
        return {"status": "exito", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en motor estadístico: {str(e)}")

@router_analitica_pro.post("/comparativa-t-student")
async def comparar_periodos_ahorro(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Ruta para la Capa 2. Ejecuta la Prueba T de Student.
    Compara dos conjuntos de datos (ej. Salón A vs Salón B).
    """
    grupo_a = payload.get("grupo_a", [])
    grupo_b = payload.get("grupo_b", [])

    if not grupo_a or not grupo_b:
        raise HTTPException(status_code=400, detail="Debes enviar ambos grupos para la comparativa.")

    try:
        df_a = motor.limpiar_serie_temporal(grupo_a)
        df_b = motor.limpiar_serie_temporal(grupo_b)
        
        resultado = motor.validar_ahorro_t_student(df_a, df_b)
        return {"status": "exito", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falla en prueba de hipótesis: {str(e)}")

@router_analitica_pro.post("/anomalias-ml")
async def detectar_picos_criticos(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Ruta para la Capa 3. Aplica Isolation Forest.
    """
    datos = payload.get("datos", [])
    if not datos:
        raise HTTPException(status_code=400, detail="Sin datos para Machine Learning.")

    try:
        df_limpio = motor.limpiar_serie_temporal(datos)
        resultado = motor.detectar_anomalias_isolation_forest(df_limpio)
        return {"status": "exito", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Isolation Forest: {str(e)}")

@router_analitica_pro.post("/impacto-textual")
async def cuantificar_motivos(payload: Dict[str, List[Dict[str, Any]]]):
    """
    Procesa las variables categóricas.
    """
    import pandas as pd
    datos = payload.get("datos", [])
    if not datos:
        raise HTTPException(status_code=400, detail="Sin datos textuales.")

    try:
        df_crudo = pd.DataFrame(datos)
        resultado = motor.procesar_causalidad_textual(df_crudo)
        return {"status": "exito", "data": resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en análisis de texto: {str(e)}")