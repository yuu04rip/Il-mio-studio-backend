import enum

class TipoDocumentazione(str, enum.Enum):
    CARTA_IDENTITA = "carta_identita"
    DOCUMENTO_PROPRIETA = "documento_proprieta"
    PASSAPORTO = "passaporto"
    VISURE_CATASTALI = "visure_catastali"
    PLANIMETRIA = "planimetria"
    ATTO = "atto"
    COMPROMESSO = "compromesso"
    PREVENTIVO = "preventivo"

class TipoServizio(str, enum.Enum):
    ATTO = "atto"
    COMPROMESSO = "compromesso"
    PREVENTIVO = "preventivo"

class TipoDipendenteTecnico(str, enum.Enum):
    NOTAIO = "notaio"
    CONTABILE = "contabile"
    ASSISTENTE = "assistente"

class Role(str, enum.Enum):
    CLIENTE = "cliente"
    NOTAIO = "notaio"
    DIPENDENTE = "dipendente"