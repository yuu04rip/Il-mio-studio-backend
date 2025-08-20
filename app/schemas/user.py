from pydantic import BaseModel, EmailStr

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