from pydantic import BaseModel, field_serializer
from datetime import datetime
from app.models.enums import TipoServizio

class ServizioOut(BaseModel):
    id: int
    cliente_id: int
    codiceCorrente: int
    codiceServizio: int
    dataConsegna: datetime
    dataRichiesta: datetime
    statoServizio: bool
    tipo: TipoServizio
    is_deleted: bool

    @field_serializer('dataConsegna', 'dataRichiesta')
    def serialize_datetime(self, value: datetime, _info):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True