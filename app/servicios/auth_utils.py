# app/servicio/auth_utils.py
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

# Importación de configuración
from app.configuracion import configuracion 

# Constantes leídas de la configuración
SECRET_KEY = configuracion.JWT_SECRET_KEY
ALGORITHM = configuracion.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = configuracion.ACCESS_TOKEN_EXPIRE_MINUTES

# Esquema de autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login") 

# ----------------------------------------------------------------------
# 1. CREACIÓN DE TOKENS
# ----------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea y codifica el token JWT."""
    to_encode = data.copy()
    
    # Usamos timezone.utc para evitar el error de datetime
    ahora_utc = datetime.now(timezone.utc)

    if expires_delta:
        expire = ahora_utc + expires_delta
    else:
        expire = ahora_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire, 
        "iat": ahora_utc, 
        "sub": str(data["sub"])
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ----------------------------------------------------------------------
# 2. MODELO DE USUARIO (NUEVO)
# ----------------------------------------------------------------------
class UserPayload(BaseModel):
    id: int
    permisos: List[str] = []

# ----------------------------------------------------------------------
# 3. DEPENDENCIAS DE AUTENTICACIÓN
# ----------------------------------------------------------------------

# 🚨 NUEVA FUNCIÓN MAESTRA: Devuelve el objeto completo (ID + Permisos)
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        permisos: List[str] = payload.get("permisos", []) 

        if user_id is None:
            raise credentials_exception
        
        return UserPayload(id=int(user_id), permisos=permisos)
        
    except JWTError:
        raise credentials_exception

# 🚨 FUNCIÓN PUENTE (RESTAURADA): Para compatibilidad con tus endpoints actuales
# Esta función es la que buscan 'valores.py', 'dispositivos.py', etc.
async def get_current_user_id(user: UserPayload = Depends(get_current_user)) -> int:
    """
    Extrae solo el ID del usuario autenticado.
    Mantiene la compatibilidad con endpoints que esperan 'current_user_id: int'.
    """
    return user.id

# ----------------------------------------------------------------------
# 4. CLASE PARA PERMISOS (REQUERIR PERMISO)
# ----------------------------------------------------------------------
class RequerirPermiso:
    def __init__(self, permiso: str):
        self.permiso = permiso

    async def __call__(self, user: UserPayload = Depends(get_current_user)):
        # 1. Verificar si es Super Admin (opcional)
        if "SUPER_ADMIN" in user.permisos:
            return user

        # 2. Verificar si tiene el permiso específico
        if self.permiso not in user.permisos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para realizar esta acción ({self.permiso})"
            )
        return user 

# ----------------------------------------------------------------------
# 5. VALIDACIÓN DE INVITACIONES
# ----------------------------------------------------------------------
def validate_invitation_token(token: str) -> Dict[str, Any]:
    """Decodifica un token de invitación y verifica su validez y tipo."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        token_type = payload.get("type")
        if token_type != "INVITE":
            raise HTTPException(status_code=400, detail="Tipo de token inválido.")
            
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El link de invitación es inválido o ha expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error de procesamiento del token.")
# from datetime import datetime, timedelta,timezone
# from typing import Optional

# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
# from typing import List, Dict, Any, Optional
# # Importación ajustada desde el directorio superior 'app'
# from app.configuracion import configuracion 

# from app.servicios.servicio_simulacion import get_db_connection
# from fastapi import Security # Importación necesaria
# from pydantic import BaseModel

# # Constantes leídas de la configuración
# SECRET_KEY = configuracion.JWT_SECRET_KEY
# ALGORITHM = configuracion.JWT_ALGORITHM
# ACCESS_TOKEN_EXPIRE_MINUTES = configuracion.ACCESS_TOKEN_EXPIRE_MINUTES

# # Esquema de autenticación
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login") 

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     """Crea y codifica el token JWT."""
#     to_encode = data.copy()
    
#     # Usamos timezone.utc para obtener la hora actual exacta y consciente de la zona
#     ahora_utc = datetime.now(timezone.utc)

#     if expires_delta:
#         expire = ahora_utc + expires_delta
#     else:
#         expire = ahora_utc + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
#     # Actualizamos usando la variable 'ahora_utc'
#     to_encode.update({
#         "exp": expire, 
#         "iat": ahora_utc, 
#         "sub": str(data["sub"])
#     })
    
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


# # Modelo de Usuario Autenticado
# class UserPayload(BaseModel):
#     id: int
#     permisos: List[str] = []

# async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UserPayload:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Credenciales inválidas o token expirado.",
#         headers={"WWW-Authenticate": "Bearer"},)

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         permisos: List[str] = payload.get("permisos", []) # 

#         if user_id is None:
#             raise credentials_exception
        
#         # 🚀 RETORNAMOS UN OBJETO RICO, NO SOLO EL ID
#         return UserPayload(id=int(user_id), permisos=permisos)
        
#     except JWTError:
#         raise credentials_exception
#  # app/servicios/auth_utils.py

# class RequerirPermiso:
#     def __init__(self, permiso: str):
#         self.permiso = permiso

#     async def __call__(self, user: UserPayload = Depends(get_current_user_id)):
#         # 1. Verificar si es Super Admin (opcional)
#         if "SUPER_ADMIN" in user.permisos:
#             return user

#         # 2. Verificar si tiene el permiso específico
#         if self.permiso not in user.permisos:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"No tienes permisos para realizar esta acción ({self.permiso})"
#             )
#         return user   

    
    
#  # app/servicios/auth_utils.py (Añadir al final)

# def validate_invitation_token(token: str) -> Dict[str, Any]:
#     """Decodifica un token de invitación y verifica su validez y tipo."""
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
#         # 🚨 CRÍTICO: Verificar que el token sea del tipo "INVITE"
#         token_type = payload.get("type")
#         if token_type != "INVITE":
#             raise HTTPException(status_code=400, detail="Tipo de token inválido.")
            
#         # Devolver el contenido del token (ID de usuario que invita, ID del proyecto)
#         return payload
        
#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="El link de invitación es inválido o ha expirado.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     except Exception:
#         raise HTTPException(status_code=500, detail="Error de procesamiento del token.")
 
 
 # # Esta función se usará con Depends() para proteger las rutas.
# async def get_current_user_id(token: str = Depends(oauth2_scheme)):
#     """Decodifica y valida el token en rutas protegidas, devolviendo el ID del usuario."""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Credenciales inválidas o token expirado.",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub") 
#         if user_id is None:
#             raise credentials_exception
        
#         return int(user_id) # Devolver el ID como entero
        
#     except JWTError:
#         raise credentials_exception
    
    
 # def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     """Crea y codifica el token JWT."""
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
#     to_encode.update({"exp": expire, "iat": datetime.utcnow(), "sub": str(data["sub"])})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


    
    

# app/servicios/auth_utils.py (Nueva Función de Servicio)

# app/servicios/auth_utils.py (Función CORREGIDA)

# async def check_user_permission(
#     current_user_id: int, 
#     required_permission: str, 
#     proyecto_id: int | None = None
# ) -> bool:
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         # 🚨 1. VERIFICACIÓN GLOBAL Y LECTURA BÁSICA (SIN PROYECTO ID)
        
#         # Query para verificar si el usuario tiene el permiso globalmente (si existe una tabla de roles a nivel de usuario)
#         # O si el permiso es de lectura (VER_DATOS) y el usuario es el Admin.
        
#         # Lógica de verificación simplificada:
#         sql_check = """
#         SELECT COUNT(rp.rol_id)
#         FROM proyecto_usuarios pu
#         JOIN rol_permisos rp ON pu.rol_id = rp.rol_id
#         JOIN permisos p ON rp.permiso_id = p.id
#         WHERE pu.usuario_id = %s AND p.nombre_permiso = %s AND (pu.proyecto_id = %s OR pu.rol_id = 1);
#         """
        
#         # 🚨 SOLUCIÓN RÁPIDA: Chequeo de Admin Global (Rol ID 1) para VER_DATOS
#         if required_permission == "VER_DATOS":
#             # Si el usuario es miembro de CUALQUIER proyecto (con cualquier rol), o es Admin, puede ver las unidades
#             sql_read_access = """
#             SELECT COUNT(DISTINCT pu.usuario_id)
#             FROM proyecto_usuarios pu
#             WHERE pu.usuario_id = %s;
#             """
#             cursor.execute(sql_read_access, (current_user_id,))
#             if cursor.fetchone()[0] > 0:
#                  return True
            
#             # Si el usuario es el creador de CUALQUIER proyecto, también puede ver. (Por si no fue asignado a proyecto_usuarios)
#             cursor.execute("SELECT COUNT(id) FROM proyectos WHERE usuario_id = %s", (current_user_id,))
#             if cursor.fetchone()[0] > 0:
#                 return True
        
#         # 2. VERIFICACIÓN LOCAL (Para CRUD, REQUIERE PROYECTO ID)
#         if proyecto_id is not None:
#              # Usamos la consulta que verifica el permiso específico en un proyecto
#              sql_local = """
#              SELECT COUNT(p.id)
#              FROM proyecto_usuarios pu
#              JOIN rol_permisos rp ON pu.rol_id = rp.rol_id
#              JOIN permisos p ON rp.permiso_id = p.id
#              WHERE pu.usuario_id = %s AND pu.proyecto_id = %s AND p.nombre_permiso = %s;
#              """
#              cursor.execute(sql_local, (current_user_id, proyecto_id, required_permission))
#              if cursor.fetchone()[0] > 0:
#                  return True

#         return False 
        
#     except Exception as e:
#         print(f"Error en check_user_permission: {e}")
#         return False
#     finally:
#         if conn:
#             conn.close()
# app/servicios/auth_utils.py (Añadir al final)

# app/servicios/auth_utils.py (Función CORREGIDA para la Membresía)

# app/servicios/auth_utils.py (Función clave)

# app/servicios/auth_utils.py (Función CORREGIDA)

# app/servicios/auth_utils.py (Función CORREGIDA y Robustecida)

# async def is_user_member_of_project(user_id: int, project_id: int) -> bool:
#     conn = None
#     try:
#         conn = get_db_connection()
#         # Usamos cursor simple
#         cursor = conn.cursor() 
        
#         # 🚨 CONSULTA UNIFICADA: Chequea DUEÑO O MIEMBRO
#         sql = """
#         SELECT EXISTS (
#             SELECT 1 FROM proyectos p WHERE p.id = %s AND p.usuario_id = %s
#             UNION
#             SELECT 1 FROM proyecto_usuarios pu WHERE pu.proyecto_id = %s AND pu.usuario_id = %s
#         ) AS is_member;
#         """
        
#         cursor.execute(sql, (project_id, user_id, project_id, user_id))
        
#         # 🚨 LECTURA SEGURA: Obtener el resultado
#         result = cursor.fetchone()
        
#         # Convertir el resultado a entero de forma segura y verificar si es 1 (True)
#         # result[0] es la tupla (0) o (1). int(result[0]) convierte esto a 0 o 1.
#         if result and result[0] is not None:
#              return int(result[0]) == 1
        
#         return False
        
#     except Exception as e:
#         # Si hay un error de conexión, el acceso debe ser denegado por seguridad
#         print(f"Error fatal checking membership: {e}")
#         return False
#     finally:
#         if conn: conn.close()
