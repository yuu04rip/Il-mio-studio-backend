from pydantic import BaseModel, field_serializer
from datetime import datetime
from app.models.enums import TipoDocumentazione

class DocumentazioneOut(BaseModel):
    id: int
    filename: str
    tipo: TipoDocumentazione
    created_at: datetime

    @field_serializer('created_at')
    def serialize_datetime(self, value: datetime, _info):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True