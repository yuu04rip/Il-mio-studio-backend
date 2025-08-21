from pydantic import BaseModel
from app.schemas.user import UserOut

class NotaioOut(BaseModel):
    id: int
    utente: UserOut
    codice_notarile: int

    class Config:
        from_attributes = True