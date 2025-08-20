from pydantic import BaseModel
from app.models.enums import TipoDocumentazione

class DocumentazioneOut(BaseModel):
    id: int
    filename: str
    tipo: TipoDocumentazione
    path: str
    created_at: str

    class Config:
        from_attributes = True