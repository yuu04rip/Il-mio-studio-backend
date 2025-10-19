from pydantic import BaseModel, EmailStr, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    codice_notarile: int | None = None
    ruolo: str | None = None

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str
    numeroTelefonico: str | None = None
    ruolo: str | None = None

class ChangeEmailRequest(BaseModel):
    email: str
    new_email: str
    password: str
class RegisterNotaioRequest(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str
    numeroTelefonico: str | None = None
    codice_notarile: int

    @field_validator('codice_notarile')
    @classmethod
    def validate_codice_notarile(cls, v):
        if not v:
            raise ValueError('codice_notarile obbligatorio per la registrazione notaio')
        return v