from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    nome: str
    cognome: str
    numeroTelefonico: str | None = None
    ruolo: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

class ChangePasswordRequest(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str
    codice_notarile: Optional[int] = None

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    cognome: Optional[str] = None
    email: Optional[EmailStr] = None
    numeroTelefonico: Optional[int] = None