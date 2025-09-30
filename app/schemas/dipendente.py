from typing import Optional

from pydantic import BaseModel
from app.schemas.enums import  TipoDipendenteTecnico
from app.schemas.user import UserOut

class DipendenteTecnicoOut(BaseModel):
    id: int
    utente: UserOut
    tipo: TipoDipendenteTecnico

    class Config:
        from_attributes = True
class DipendenteTecnicoDettagliOut(BaseModel):
    id: int
    nome: Optional[str]
    cognome: Optional[str]
    email: Optional[str]
    numeroTelefonico: Optional[str]
    tipo: TipoDipendenteTecnico