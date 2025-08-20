from pydantic import BaseModel
from app.schemas.user import UserOut

class NotaioOut(BaseModel):
    id: int
    utente: UserOut
    codiceNotarile: int

    class Config:
        from_attributes = True