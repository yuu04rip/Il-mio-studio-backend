from pydantic import BaseModel
from app.models.enums import TipoServizio

class ServizioOut(BaseModel):
    id: int
    codiceCorrente: int
    codiceServizio: int
    dataConsegna: str
    dataRichiesta: str
    statoServizio: bool
    tipo: TipoServizio

    class Config:
        from_attributes = True