from pydantic import BaseModel
from app.models.enums import TipoDocumentazione, TipoServizio, TipoDipendenteTecnico, Role

class TipoDocumentazioneSchema(BaseModel):
    tipo: TipoDocumentazione

class TipoDipendenteTecnicoSchema(BaseModel):
    tipo: TipoDipendenteTecnico

class TipoServizioSchema(BaseModel):
    tipo: TipoServizio

class RoleSchema(BaseModel):
    ruolo: Role