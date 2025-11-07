from typing import  List, Optional
from pydantic import BaseModel, field_serializer
from datetime import datetime
from app.models.enums import TipoServizio, StatoServizio

class ServizioOut(BaseModel):
    id: int
    cliente_id: int
    codiceCorrente: int
    codiceServizio: str   # ora stringa
    clienteNome: Optional[str] = None
    clienteCognome: Optional[str] = None
    dataConsegna: datetime
    dataRichiesta: datetime
    statoServizio: StatoServizio
    tipo: TipoServizio
    is_deleted: bool
    dipendenti: List[int]

    @field_serializer('dataConsegna', 'dataRichiesta')
    def serialize_datetime(self, value: datetime, _info):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True