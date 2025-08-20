from pydantic import BaseModel
from app.schemas.user import UserOut

class ClienteOut(BaseModel):
    id: int
    utente: UserOut

    class Config:
        from_attributes = True