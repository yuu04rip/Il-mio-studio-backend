from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    codice_notarile: int | None = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str
    numeroTelefonico: str | None = None
    ruolo: str | None = None  # "cliente" (default) oppure "dipendente"/"notaio"