from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import re

class Settings_Mail(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool
    FRONTEND_URL: str  # <--- НОВОЕ

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

class UserRegistration(BaseModel):
    email: EmailStr
    name: str
    password: str = Field(..., min_length=5, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        invalid_chars = r"[\s\"']"
        if re.search(invalid_chars, value):
            raise ValueError("Пароль содержит запрещенные символы")
        return value

class UserAuthorization(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=5, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        invalid_chars = r"[\s\"']"
        if re.search(invalid_chars, value):
            raise ValueError("Пароль содержит запрещенные символы")
        return value

class PasswordRecovery(BaseModel):
    email: EmailStr

class PasswordRecoveryChange(BaseModel):
    new_password: str = Field(..., min_length=5, max_length=72)

    @field_validator("new_password", mode="before")
    @classmethod
    def validate_new_password(cls, value: Optional[str]) -> Optional[str]:
        if value == "":
            return None
        return value

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value == "":
            return None
        return value

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: Optional[str]) -> Optional[str]:
        if value == "":
            return None
        return value

class PasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=5, max_length=72)
    new_password: str = Field(..., min_length=5, max_length=72)

    @field_validator("old_password")
    @classmethod
    def validate_old_password(cls, value: str) -> str:
        invalid_chars = r"[\s\"']"
        if re.search(invalid_chars, value):
            raise ValueError("Пароль содержит запрещенные символы")
        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        invalid_chars = r"[\s\"']"
        if re.search(invalid_chars, value):
            raise ValueError("Пароль содержит запрещенные символы")
        return value