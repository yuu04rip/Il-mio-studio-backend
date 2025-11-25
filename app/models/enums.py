import enum

class TipoDocumentazione(str, enum.Enum):
    CARTA_IDENTITA = "carta_identita"
    DOCUMENTO_PROPRIETA = "documento_proprieta"
    PASSAPORTO = "passaporto"
    TESSERA_SANITARIA = "tessera_sanitaria"
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
    DIPENDENTE = "dipendente"

class Role(str, enum.Enum):
    CLIENTE = "cliente"
    NOTAIO = "notaio"
    DIPENDENTE = "dipendente"

class StatoServizio(str, enum.Enum):
    CREATO = "creato"
    IN_LAVORAZIONE = "in_lavorazione"
    IN_ATTESA_APPROVAZIONE = "in_attesa_approvazione"
    APPROVATO = "approvato"
    RIFIUTATO = "rifiutato"
    CONSEGNATO = "consegnato"