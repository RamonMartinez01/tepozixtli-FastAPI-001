# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt 
from app.core.config import settings

def get_password_hash(password: str) -> str:
    """Toma una contraseña en texto plano y devuelve un hash indescifrable usando bcrypt puro."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña que el usuario escribió con el hash de la base de datos."""
    password_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hash_bytes)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un JWT (JSON Web Token) sellado con nuestra SECRET_KEY."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # PyJWT moderno requiere el algoritmo explícitamente
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt