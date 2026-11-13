from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from dotenv import load_dotenv
import os
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Автоматически ищет токен в заголовке Authorization: Bearer <token>
bearer = HTTPBearer()

def create_access_token(data: dict, TIME_TO_END_TOKEN_MIN: int) -> str:
    """Генерация JWT-токена с email и id пользователя"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=TIME_TO_END_TOKEN_MIN)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def decode_access_token(auth: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    token = auth.credentials
    """Расшифровка и проверка валидности JWT-токена"""
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Срок действия токена истек"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен авторизации"
        )

def require_token_purpose(expected_purpose: str):
    """Фабрика зависимостей для проверки назначения JWT-токена"""
    async def dependency(payload: dict = Depends(decode_access_token)) -> dict:
        if payload.get("purpose") != expected_purpose:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недопустимый тип токена для этого действия"
            )
        return payload
    return dependency