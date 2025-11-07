from pydantic import BaseModel
from typing import Optional
from app.schemas.user import UserOut

class ClienteOut(BaseModel):
    id: int
    utente: UserOut

    class Config:
        from_attributes = True

class ClienteDettagliOut(BaseModel):
    id: int
    nome: Optional[str]
    cognome: Optional[str]
    email: Optional[str]
    numeroTelefonico: Optional[str]
class ClienteSearchOut(BaseModel):
    """
    Modello leggero usato dall'endpoint /clienti/search/
    Restituisce i campi minimi usati dall'autocomplete frontend.
    """
    id: int
    nome: Optional[str] = None
    cognome: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True