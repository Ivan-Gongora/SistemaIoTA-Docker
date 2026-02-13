from fastapi import Path, APIRouter, Query, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pymysql
import bcrypt

# Importaciones ajustadas a tu estructura:
from app.configuracion import configuracion
from app.servicios.servicio_simulacion import get_db_connection
# 🚨 Ajustar la ruta si es necesario
from app.servicios.auth_utils import create_access_token 

# 🚨 Asume que estos modelos están en app/api/modelos/usuarios.py
from app.api.modelos.usuarios import UsuarioCrear, UsuarioActualizar, UsuarioLogin, Token, UsuarioRespuesta 


router_usuario = APIRouter()

# ----------------------------------------------------------------------
# 1. Rutas de Creación y Actualización (Funcionalidad Existente)
# ----------------------------------------------------------------------

# Crear Proyectos 
@router_usuario.post("/crear_usuario/")
async def crear_usuario(datos: UsuarioCrear):
    try:
        resultados = await set_usuario(datos)
        return {"message": "Se registró el usuario", "resultados": resultados}

    except ValueError as e:
        return {"message": "Error al registrar el usuario", "details": str(e)}
    except Exception as e:
        print("Excepción general:", type(e), e)
        return JSONResponse(
            status_code=500,
            content={"message": "Error inesperado durante la inserción ", "details": str(e)},
        )
    
# Crear usuario
async def set_usuario(datos: UsuarioCrear) -> List[Dict[str, Any]]:
    procesado = []
    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

     # Verificar si el nombre_usuario o email ya existe
        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario = %s OR email = %s", (datos.nombre_usuario, datos.email))
        if cursor.fetchone():
            return [{
                "status": "error",
                "message": "El nombre de usuario o el correo electrónico ya están en uso"
            }]

        # Obtener fechas
        fecha_registro = datos.fecha_registro or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        hashed_pw = bcrypt.hashpw(datos.contrasena.encode('utf-8'), bcrypt.gensalt())
 
        # Preparar campos y valores
        campos = ["nombre_usuario", "nombre", "apellido", "email", "contrasena", "activo", "fecha_registro"]
        valores = [datos.nombre_usuario, datos.nombre, datos.apellido, datos.email, hashed_pw, datos.activo, fecha_registro]

        if datos.tipo_usuario:
            campos.append("tipo_usuario")
            valores.append(datos.tipo_usuario)

        # Construir consulta dinámicamente
        sql = f"INSERT INTO usuarios ({', '.join(campos)}) VALUES ({', '.join(['%s'] * len(valores))})"

        cursor.execute(sql, valores)
        conn.commit()

        procesado.append({
            "status": "success",
            "nombre_usuario": datos.nombre_usuario,
            "email": datos.email,
            "tipo_usuario": datos.tipo_usuario or 'empleado',
            "fecha_registro": fecha_registro
        })

    except pymysql.MySQLError as e:
        if conn: conn.rollback()
        procesado.append({
            "status": "error",
            "message": f"DB Error: {str(e)}"
        })
    except Exception as e:
        if conn: conn.rollback()
        procesado.append({
            "status": "error",
            "message": f"Unexpected Error: {str(e)}"
        })
    finally:
        if conn: conn.close()

    return procesado


# ----------------------------------------------------------------------
# 2. Rutas de Login (IMPLEMENTACIÓN DE JWT)
# ----------------------------------------------------------------------

# 🚨 Endpoint principal: Ahora devuelve el modelo Token (con datos de usuario)
@router_usuario.post("/login", response_model=Token) 
async def login(datos: UsuarioLogin):
    return await login_usuario(datos)


# Login de usuario (MODIFICADO para generar Token)
async def login_usuario(datos: UsuarioLogin):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (datos.nombre_usuario,))
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado") 
        
        # Verificar contraseña
        if not bcrypt.checkpw(datos.contrasena.encode('utf-8'), usuario["contrasena"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # Actualizar el último login
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE usuarios SET ultimo_login = %s WHERE id = %s", (ahora, usuario["id"]))
        conn.commit()

        # 🚨 PREPARACIÓN Y GENERACIÓN DEL TOKEN
        access_token_expires = timedelta(minutes=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        access_token = create_access_token(
            data={"sub": str(usuario["id"])}, 
            expires_delta=access_token_expires
        )
        
        # Eliminar contraseña antes de devolver los datos
        usuario.pop("contrasena", None) 
        
        # 🚨 Retornamos el objeto Token que incluye los datos del usuario
        # Usamos UsuarioRespuesta.model_validate para asegurar que el diccionario coincida con el modelo
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "usuario": UsuarioRespuesta.model_validate(usuario)
        }

    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")
    except Exception as e:
        # Esto atrapará errores como problemas en la generación del token
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    finally:
        if conn:
            conn.close()


# ----------------------------------------------------------------------
# 3. Rutas Existentes (Mantener, aunque se recomienda protegerlas)
# ----------------------------------------------------------------------

# Obtener usuario por ID (Sin protección JWT aún)
@router_usuario.get("/obtener_usuario/")
async def login_usuario(datos: UsuarioLogin):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S" # Formato estándar para la web
        
        # 1. Buscar al usuario por nombre de usuario
        cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario = %s", (datos.nombre_usuario,))
        usuario = cursor.fetchone()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado") 
        
        # 2. Verificar contraseña
        if not bcrypt.checkpw(datos.contrasena.encode('utf-8'), usuario["contrasena"].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # 3. Actualizar el último login
        ahora = datetime.now().strftime(DATE_FORMAT)
        cursor.execute("UPDATE usuarios SET ultimo_login = %s WHERE id = %s", (ahora, usuario["id"]))
        conn.commit()

        # 4. Generación del Token
        access_token_expires = timedelta(minutes=configuracion.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        access_token = create_access_token(
            data={"sub": str(usuario["id"])}, 
            expires_delta=access_token_expires
        )
        
        # 5. Eliminación de datos sensibles y CONVERSIÓN DE DATETIME A STRING
        usuario.pop("contrasena", None) 
        
        # Convertir fecha_registro
        if 'fecha_registro' in usuario and isinstance(usuario['fecha_registro'], datetime):
            usuario['fecha_registro'] = usuario['fecha_registro'].strftime(DATE_FORMAT)

        # Convertir ultimo_login (debe ser None si es nulo en la DB, pero lo forzamos a string si es datetime)
        if 'ultimo_login' in usuario and usuario['ultimo_login'] is not None and isinstance(usuario['ultimo_login'], datetime):
            usuario['ultimo_login'] = usuario['ultimo_login'].strftime(DATE_FORMAT)
            
        # Nota: Si el campo es None en la DB y Pydantic lo permite (Optional[str]), no necesita conversión.

        # 6. Retornamos el objeto Token (incluye el UsuarioRespuesta validado)
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "usuario": UsuarioRespuesta.model_validate(usuario) # 🚨 Uso de model_validate
        }

    except pymysql.MySQLError as e:
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")
    except Exception as e:
        # Esto atrapará errores como problemas en la generación del token o Pydantic
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
    finally:
        if conn:
            conn.close()