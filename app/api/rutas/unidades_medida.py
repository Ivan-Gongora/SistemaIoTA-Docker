from fastapi import APIRouter, Query, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import pymysql

# 🚨 Importaciones de Seguridad (SOLO JWT)
from app.servicios.auth_utils import get_current_user_id 
from app.servicios.servicio_simulacion import get_db_connection
from app.api.modelos.unidades_medida import UnidadMedida, UnidadMedidaCrear, UnidadMedidaActualizar

router_unidades = APIRouter()

# ----------------------------------------------------------------------
# FUNCIONES DE SERVICIO DE BASE DE DATOS (SERVICIO CRUD LOCAL)
# ----------------------------------------------------------------------

# GET: Obtener todas las unidades
async def obtener_unidades_medida() -> List[Dict[str, Any]]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, nombre, simbolo, descripcion, magnitud_tipo FROM unidades_medida")
        return cursor.fetchall()
    except Exception as e:
        print(f"Error al obtener unidades: {e}")
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")
    finally:
        if conn: conn.close()

# POST: Crear una unidad
async def set_unidad_medida(datos: UnidadMedidaCrear) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO unidades_medida (nombre, simbolo, descripcion, magnitud_tipo) VALUES (%s, %s, %s, %s)",
            (datos.nombre, datos.simbolo, datos.descripcion, datos.magnitud_tipo)
        )
        conn.commit()
        return {"status": "success", "id": conn.insert_id(), "nombre": datos.nombre}
    except pymysql.Error as e:
        raise HTTPException(status_code=400, detail=f"DB Error al crear unidad: {str(e)}")
    finally:
        if conn: conn.close()
   
# POST: Crear múltiples unidades (batch)
async def set_unidades_medida_batch(datos_lista: List[UnidadMedidaCrear]) -> Dict[str, Any]:
    """
    Inserta una lista de unidades de medida. 
    Usa INSERT IGNORE para evitar fallos si la unidad ya existe.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cargadas = 0
        errores = 0
        
        # Iteramos sobre la lista que llegó en el JSON
        for datos in datos_lista:
            try:
                # 🚨 Usamos INSERT IGNORE para que MySQL ignore los duplicados (si el nombre/símbolo ya existe)
                # NOTA: Esto requiere que 'nombre' o 'simbolo' tengan una restricción UNIQUE en la DB.
                # Si no la tienen, es más seguro chequear primero:
                
                cursor.execute("SELECT id FROM unidades_medida WHERE nombre = %s OR simbolo = %s", (datos.nombre, datos.simbolo))
                if cursor.fetchone():
                    continue # Ya existe, la ignoramos

                cursor.execute(
                    "INSERT INTO unidades_medida (nombre, simbolo, descripcion, magnitud_tipo) VALUES (%s, %s, %s, %s)",
                    (datos.nombre, datos.simbolo, datos.descripcion, datos.magnitud_tipo)
                )
                cargadas += 1
            except Exception:
                errores += 1

        conn.commit()
        return {"status": "success", "nuevas_unidades_cargadas": cargadas, "unidades_ignoradas": (len(datos_lista) - cargadas - errores), "errores": errores}

    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error en la carga masiva: {str(e)}")
    finally:
        if conn: conn.close()
                
# PUT: Actualizar una unidad
async def actualizar_unidad_medida(id: int, datos: UnidadMedidaActualizar) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        campos = []
        valores = []
        if datos.nombre is not None: campos.append("nombre = %s"); valores.append(datos.nombre)
        if datos.simbolo is not None: campos.append("simbolo = %s"); valores.append(datos.simbolo)
        if datos.descripcion is not None: campos.append("descripcion = %s"); valores.append(datos.descripcion)
        if datos.magnitud_tipo is not None: campos.append("magnitud_tipo = %s"); valores.append(datos.magnitud_tipo)
        if not campos: return {"status": "warning", "message": "No se proporcionaron datos para actualizar"}
             
        valores.append(id)
        sql = f"UPDATE unidades_medida SET {', '.join(campos)} WHERE id = %s"
        cursor.execute(sql, valores)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Unidad de medida no encontrada.")
            
        return {"status": "success", "rows_affected": cursor.rowcount}
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"DB Error al actualizar unidad: {str(e)}")
    finally:
        if conn: conn.close()

# # DELETE: Eliminar una unidad
# async def eliminar_unidad_medida(id: int) -> Dict[str, Any]:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         cursor.execute("DELETE FROM unidades_medida WHERE id = %s", (id,))
#         conn.commit()
        
#         if cursor.rowcount == 0:
#             raise HTTPException(status_code=404, detail="Unidad de medida no encontrada.")
            
#         return {"status": "success", "message": "Unidad de medida eliminada exitosamente."}
#     except pymysql.Error as e:
#         if e.args[0] == 1451: # Error de restricción de clave foránea
#              raise HTTPException(status_code=400, detail="No se puede eliminar: La unidad está siendo usada por un campo de sensor.")
#         raise HTTPException(status_code=500, detail=f"DB Error al eliminar unidad: {str(e)}")
#     finally:
#         if conn: conn.close()


# ----------------------------------------------------------------------
# ENDPOINTS DE FASTAPI (ROUTER Y SEGURIDAD SIMPLIFICADA)
# ----------------------------------------------------------------------

# GET (LECTURA): Accesible por cualquier usuario autenticado
@router_unidades.get("/unidades", response_model=List[UnidadMedida])
async def get_unidades(
    current_user_id: int = Depends(get_current_user_id) # 🚨 ÚNICAMENTE REQUIERE JWT
):
    try:
        unidades = await obtener_unidades_medida() 
        return unidades
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener unidades: {str(e)}")


# POST (CREACIÓN): Requiere JWT
@router_unidades.post("/unidades", response_model=Dict[str, Any])
async def crear_unidad(
    datos: UnidadMedidaCrear,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await set_unidad_medida(datos)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear unidad: {str(e)}")



# 🚨 NUEVO ENDPOINT (Para Carga Masiva)
@router_unidades.post("/unidades/batch_create", response_model=Dict[str, Any])
async def crear_unidades_batch(
    datos_lista: List[UnidadMedidaCrear], # 🚨 Acepta una LISTA de modelos
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await set_unidades_medida_batch(datos_lista)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear unidades: {str(e)}")



# PUT (ACTUALIZACIÓN): Requiere JWT
@router_unidades.put("/unidades/{id}", response_model=Dict[str, Any])
async def actualizar_unidad(
    id: int,
    datos: UnidadMedidaActualizar,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        return await actualizar_unidad_medida(id, datos)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar unidad: {str(e)}")



# # DELETE (ELIMINACIÓN): Requiere JWT
# @router_unidades.delete("/unidades/{id}", response_model=Dict[str, Any])
# async def eliminar_unidad(
#     id: int,
#     current_user_id: int = Depends(get_current_user_id)
# ):
#     try:
#         return await eliminar_unidad_medida(id)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error al eliminar unidad: {str(e)}")