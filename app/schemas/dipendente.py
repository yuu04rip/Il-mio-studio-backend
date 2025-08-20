from pydantic import BaseModel
from app.schemas.enums import TipoDipendenteTecnicoSchema
from app.schemas.user import UserOut

class DipendenteTecnicoOut(BaseModel):
    id: int
    utente: UserOut
    tipo: TipoDipendenteTecnicoSchema

    class Config:
        from_attributes = True