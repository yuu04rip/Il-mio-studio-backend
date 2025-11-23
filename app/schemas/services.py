from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, field_serializer

from app.models.enums import TipoServizio, StatoServizio


class CreatoreServizioOut(BaseModel):
    id: int
    nome: Optional[str] = None
    cognome: Optional[str] = None


class ServizioOut(BaseModel):
    id: int
    cliente_id: int
    codiceCorrente: int
    codiceServizio: str
    clienteNome: Optional[str] = None
    clienteCognome: Optional[str] = None
    dataConsegna: datetime
    dataRichiesta: datetime
    statoServizio: StatoServizio
    tipo: TipoServizio
    is_deleted: bool
    dipendenti: List[int]
    archived: bool
    creato_da: Optional[CreatoreServizioOut] = None
    creato_da_id: Optional[int] = None

    @field_serializer('dataConsegna', 'dataRichiesta')
    def serialize_datetime(self, value: datetime, _info):
        return value.isoformat() if value else None

    class Config:
        from_attributes = True