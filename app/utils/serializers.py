from typing import List, Dict, Any
from app.models.services import Servizio

def servizio_to_dict(servizio: Servizio) -> Dict[str, Any]:
    """
    Serializza un oggetto Servizio (SQLAlchemy) in dict compatibile con ServizioOut.
    Include anche i campi clienteNome / clienteCognome (snapshot).
    """
    dip_ids: List[int] = []
    try:
        dip_ids = [d.id for d in getattr(servizio, "dipendenti", []) if getattr(d, "id", None) is not None]
    except Exception:
        dip_ids = []

    return {
        "id": getattr(servizio, "id", None),
        "cliente_id": getattr(servizio, "cliente_id", None),
        "codiceCorrente": getattr(servizio, "codiceCorrente", None),
        "codiceServizio": getattr(servizio, "codiceServizio", None),
        "clienteNome": getattr(servizio, "cliente_nome", None),
        "clienteCognome": getattr(servizio, "cliente_cognome", None),
        "dataConsegna": getattr(servizio, "dataConsegna", None),
        "dataRichiesta": getattr(servizio, "dataRichiesta", None),
        "statoServizio": getattr(servizio, "statoServizio", None),
        "tipo": getattr(servizio, "tipo", None),
        "is_deleted": getattr(servizio, "is_deleted", False),
        "dipendenti": dip_ids,
    }