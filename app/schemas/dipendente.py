from pydantic import BaseModel
from app.schemas.enums import  TipoDipendenteTecnico
from app.schemas.user import UserOut

class DipendenteTecnicoOut(BaseModel):
    id: int
    utente: UserOut
    tipo: TipoDipendenteTecnico

    class Config:
        from_attributes = True