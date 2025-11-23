from typing import Any, Dict, List
from datetime import datetime


def _enum_value(e: Any):
    return e.value if hasattr(e, "value") else e


def _datetime_iso(dt: Any):
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    # support objects that already are strings
    return str(dt)


def servizio_to_dict(servizio) -> Dict:
    """
    Serializza un'istanza Servizio in un dict compatibile con il response_model ServizioOut.
    Assicura la presenza di tutti i campi richiesti, incluso 'archived', 'creato_da' e 'creato_da_id'.
    Converte enum -> valore e datetime -> ISO string.
    """
    # campi cliente nome/cognome: supporta sia attributi snake_case che camelCase
    cliente_nome = getattr(servizio, "clienteNome", None) or getattr(servizio, "cliente_nome", None)
    cliente_cognome = getattr(servizio, "clienteCognome", None) or getattr(servizio, "cliente_cognome", None)

    # lista ID dipendenti
    dip_ids: List[int] = []
    try:
        dipendenti = getattr(servizio, "dipendenti", []) or []
        for d in dipendenti:
            try:
                dip_ids.append(int(getattr(d, "id", d)))
            except Exception:
                # ignoriamo valori non convertibili
                pass
    except Exception:
        dip_ids = []

    # creatore del servizio (DipendenteTecnico -> utente)
    creatore = None
    try:
        creato_da = getattr(servizio, "creato_da", None)
        if creato_da is not None:
            utente = getattr(creato_da, "utente", None)
            nome = getattr(utente, "nome", None) if utente is not None else None
            cognome = getattr(utente, "cognome", None) if utente is not None else None
            creatore = {
                "id": getattr(creato_da, "id", None),
                "nome": nome,
                "cognome": cognome,
            }
    except Exception:
        creatore = None

    creatore_id = getattr(servizio, "creato_da_id", None)

    return {
        "id": getattr(servizio, "id", None),
        "cliente_id": getattr(servizio, "cliente_id", None),
        "codiceCorrente": getattr(servizio, "codiceCorrente", None),
        "codiceServizio": getattr(servizio, "codiceServizio", None),
        "clienteNome": cliente_nome,
        "clienteCognome": cliente_cognome,
        "dataConsegna": _datetime_iso(getattr(servizio, "dataConsegna", None)),
        "dataRichiesta": _datetime_iso(getattr(servizio, "dataRichiesta", None)),
        "statoServizio": _enum_value(getattr(servizio, "statoServizio", None)),
        "tipo": _enum_value(getattr(servizio, "tipo", None)),
        "is_deleted": bool(getattr(servizio, "is_deleted", False)),
        "dipendenti": dip_ids,
        "archived": bool(getattr(servizio, "archived", False)),
        "creato_da": creatore,
        "creato_da_id": creatore_id,
    }