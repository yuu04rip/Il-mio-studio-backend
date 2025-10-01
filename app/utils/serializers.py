def servizio_to_dict(servizio):
    return {
        "id": servizio.id,
        "cliente_id": servizio.cliente_id,
        "tipo": servizio.tipo,
        "codiceCorrente": servizio.codiceCorrente,
        "codiceServizio": servizio.codiceServizio,
        "statoServizio": servizio.statoServizio,
        "dataRichiesta": servizio.dataRichiesta,
        "dataConsegna": servizio.dataConsegna,
        "is_deleted": servizio.is_deleted,
        "dipendenti": [d.id for d in servizio.dipendenti],
    }