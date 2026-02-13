from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional, Any

#clase para los usuarios
# Modelo base (sin ID)
class UsuarioBase(BaseModel):
    nombre_usuario: str
    nombre: str
    apellido: str 
    email: EmailStr
    contrasena: str
    activo: Optional[bool] = None
    fecha_registro: Optional[str] = ''
    ultimo_login: Optional[str]=''
    tipo_usuario: Optional[str] = None

    
# Modelo para crear usuario
class UsuarioCrear(UsuarioBase):
    pass

# Modelo para actualizar parcialmente
class UsuarioActualizar(BaseModel): 
    nombre_usuario: str
    apellido: str 
    email: EmailStr
    contrasena: str
    fecha_registro: Optional[str] = ''
    ultimo_login: Optional[str]=''

# Modelo para el login
class UsuarioLogin(BaseModel):
    nombre_usuario: str
    contrasena: str


# Modelo con ID, por ejemplo, para respuestas
class Usuario(UsuarioBase):
    id: int

    class Config:
        # 🚨 CORRECCIÓN CLAVE: orm_mode renombrado a from_attributes (para Pydantic v2)
        from_attributes = True 
        
# Modelo que se devolverá en el login (solo los datos sin contraseña)
class UsuarioRespuesta(BaseModel):
    id: int
    nombre_usuario: str
    nombre: str
    apellido: str
    email: EmailStr
    activo: Optional[bool] = None
    fecha_registro: Optional[str] = ''
    ultimo_login: Optional[str]=''
    tipo_usuario: Optional[str] = None
    
    class Config:
        # 🚨 CORRECCIÓN CLAVE: from_attributes ya está correctamente aquí
        from_attributes = True 

# Modelo de respuesta final del endpoint /login
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # CRÍTICO: Incluimos el objeto de usuario completo para que el frontend lo guarde
    usuario: UsuarioRespuesta