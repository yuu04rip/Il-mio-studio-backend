from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.api.deps import get_db
from app.core.email import send_email
from app.services.gestore_studio import GestoreStudio
from app.models.user import User
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.models.services import Servizio
from app.models.enums import TipoServizio, StatoServizio
from app.schemas.dipendente import DipendenteTecnicoOut, DipendenteTecnicoDettagliOut
from app.schemas.notaio import NotaioOut
from app.schemas.cliente import ClienteOut, ClienteDettagliOut, ClienteSearchOut
from app.schemas.services import ServizioOut
from app.utils.serializers import servizio_to_dict

router = APIRouter()

# --- DIPENDENTI & NOTAI ---
@router.delete("/dipendente/{dipendente_id}")
def elimina_dipendente(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    ok = gestore.elimina_dipendente(dipendente_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dipendente non trovato nella lista")
    return {"ok": True}

@router.delete("/dipendente/{dipendente_id}/distruggi")
def distruggi_dipendente(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    ok = gestore.distruggi_dipendente(dipendente_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dipendente non trovato nel database")
    return {"ok": True}

@router.get("/dipendenti/", response_model=List[DipendenteTecnicoOut])
def get_dipendenti(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.get_dipendenti()

@router.get("/dipendente/by_user/{utente_id}", response_model=int)
def get_dipendente_id_by_user(utente_id: int, db: Session = Depends(get_db)):
    dip = db.query(DipendenteTecnico).filter(DipendenteTecnico.utente_id == utente_id).first()
    if not dip:
        raise HTTPException(status_code=404, detail="Dipendente tecnico non trovato")
    return dip.id

@router.get("/notai/", response_model=List[NotaioOut])
def get_notai(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.get_notai()

# --- CLIENTI ---
@router.get("/clienti/", response_model=List[ClienteOut])
def get_clienti(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.get_clienti()

@router.get("/clienti/search/", response_model=List[ClienteSearchOut])
def search_clienti(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.search_clienti(q)

@router.get("/clienti/nome/{nome}", response_model=ClienteOut)
def cerca_cliente_per_nome(nome: str, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    cliente = gestore.cerca_cliente_per_nome(nome)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return cliente

# --- SERVIZI CHAT ---
@router.post("/servizi/richiesta-chat")
async def richiesta_servizio_chat(
        request: Request,
        cliente_id: int = None,
        testo: str = None,
        db: Session = Depends(get_db)
):
    if cliente_id is None or testo is None:
        try:
            body = await request.json()
            cliente_id = body.get("cliente_id")
            testo = body.get("testo")
        except Exception:
            raise HTTPException(status_code=400, detail="Missing parameters cliente_id and testo")
    if cliente_id is None or testo is None:
        raise HTTPException(status_code=400, detail="Missing parameters cliente_id and testo")
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    user = db.get(User, cliente.utente_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    studio_email = "obpapiprova@gmail.com"
    subject = f"Richiesta servizio da {user.nome} {user.cognome}"
    body_text = f"Messaggio dal cliente:\n\n{testo}\n\nEmail cliente: {user.email}"
    send_email(to=studio_email, subject=subject, body=body_text, reply_to=user.email)
    return {"ok": True, "msg": "Richiesta inviata via email al notaio/studio"}

# --- SERVIZI ---
@router.delete("/servizi/{servizio_id}")
def elimina_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    ok = gestore.elimina_servizio(servizio_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Servizio non trovato nella lista")
    return {"ok": True}

@router.delete("/servizi/{servizio_id}/distruggi")
def distruggi_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    ok = gestore.distruggi_servizio(servizio_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Servizio non trovato nel database")
    return {"ok": True}

@router.post("/servizi/{servizio_id}/inizializza")
def inizializza_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.inizializza_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o già inizializzato")
    return servizio_to_dict(servizio)

@router.post("/servizi/{servizio_id}/inoltra-notaio")
def inoltra_servizio_notaio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.inoltra_servizio_notaio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o non in lavorazione")
    return servizio_to_dict(servizio)

@router.get("/notai/servizi", response_model=list)
def tutti_servizi_notaio(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizi = gestore.servizi_per_notaio()
    return [servizio_to_dict(s) for s in servizi]

@router.post("/servizi/{servizio_id}/approva")
def approva_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.approva_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o non in attesa approvazione")
    return servizio_to_dict(servizio)

@router.post("/servizi/{servizio_id}/rifiuta")
def rifiuta_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.rifiuta_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o non in attesa approvazione")
    return servizio_to_dict(servizio)

@router.put("/servizi/{servizio_id}/assegna")
def assegna_servizio(servizio_id: int, dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = db.get(Servizio, servizio_id)
    dipendente = db.get(DipendenteTecnico, dipendente_id)
    if not servizio or not dipendente:
        raise HTTPException(status_code=404, detail="Servizio o dipendente non trovato")
    if dipendente not in servizio.dipendenti:
        servizio.dipendenti.append(dipendente)
        db.commit()
    return {"ok": True}

@router.post("/servizi", response_model=ServizioOut)
async def crea_servizio(
        request: Request,
        cliente_id: int = None,
        tipo: TipoServizio = None,
        codiceCorrente: int = None,
        codiceServizio: str = None,  # opzionale e stringa
        dipendente_id: int = None,
        db: Session = Depends(get_db)
):
    from datetime import datetime
    # Supporta sia form params che JSON body
    try:
        body = await request.json()
    except Exception:
        body = {}

    cliente_id = body.get("cliente_id", cliente_id)
    tipo = body.get("tipo", tipo)
    codiceCorrente = body.get("codiceCorrente", codiceCorrente)
    codiceServizio = body.get("codiceServizio", codiceServizio)
    dipendente_id = body.get("dipendente_id", dipendente_id)

    # Ora non richiediamo codiceCorrente come obbligatorio: il backend lo genera se manca
    for v_name, v in (("cliente_id", cliente_id), ("tipo", tipo)):
        if v is None:
            raise HTTPException(status_code=422, detail=f"Campo obbligatorio mancante: {v_name}")

    gestore = GestoreStudio(db)
    now = datetime.now()
    servizio = gestore.aggiungi_servizio(
        cliente_id=cliente_id,
        tipo=tipo,
        codiceCorrente=codiceCorrente,
        codiceServizio=codiceServizio,  # se None, gestore lo genererà
        dataRichiesta=now,
        dataConsegna=now,
        dipendente_id=dipendente_id
    )
    return servizio_to_dict(servizio)

# sostituisci la route esistente /servizi/codice/{codice_servizio}
@router.get("/servizi/codice/{codice_servizio}", response_model=ServizioOut)
def cerca_servizio_per_codice(codice_servizio: str, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.cerca_servizio_per_codice(codice_servizio)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio_to_dict(servizio)

@router.get("/servizi/approvati", response_model=List[ServizioOut])
def visualizza_tutti_servizi_approvati(db: Session = Depends(get_db)):
    servizi = db.query(Servizio).filter(
        Servizio.statoServizio == StatoServizio.APPROVATO,
        Servizio.is_deleted == False
    ).all()
    return [servizio_to_dict(s) for s in servizi]

@router.get("/servizi", response_model=List[ServizioOut])
def visualizza_servizi(cliente_id: int = Query(None), db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    if cliente_id is not None:
        return [servizio_to_dict(s) for s in gestore.visualizza_servizi_cliente(cliente_id)]
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi()]

@router.post("/servizi/{servizio_id}/archivia", response_model=ServizioOut)
def archivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.archivia_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio_to_dict(servizio)

@router.put("/servizi/{servizio_id}/modifica-archiviazione", response_model=ServizioOut)
def modifica_servizio_archiviato(servizio_id: int, statoServizio: bool, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.modifica_servizio_archiviato(servizio_id, statoServizio)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio_to_dict(servizio)

@router.get("/servizi/archiviati", response_model=List[ServizioOut])
def visualizza_servizi_archiviati(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi_archiviati()]

@router.get("/dipendente/{dipendente_id}/servizi", response_model=List[ServizioOut])
def visualizza_lavoro_da_svolgere(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_lavoro_da_svolgere(dipendente_id)]

@router.get("/dipendente/{dipendente_id}/servizi_inizializzati", response_model=List[ServizioOut])
def visualizza_servizi_inizializzati(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi_inizializzati(dipendente_id)]

@router.get("/dipendente/{dipendente_id}/servizi_finalizzati", response_model=List[ServizioOut])
def visualizza_servizi_finalizzati(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    dip = db.get(DipendenteTecnico, dipendente_id)
    if not dip:
        raise HTTPException(status_code=404, detail="Dipendente tecnico non trovato")
    servizi = [s for s in dip.servizi if str(s.statoServizio).lower() in ("approvato", "rifiutato")]
    return [servizio_to_dict(s) for s in servizi]

@router.get("/dipendente/{dipendente_id}/servizi_completati", response_model=List[ServizioOut])
def visualizza_servizi_completati(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi_completati(dipendente_id)]

@router.patch("/servizi/{servizio_id}", response_model=ServizioOut)
def modifica_servizio(
        servizio_id: int,
        payload: dict = Body(...),
        db: Session = Depends(get_db)
):
    gestore = GestoreStudio(db)
    servizio = gestore.modifica_servizio(servizio_id, **payload)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio_to_dict(servizio)

from sqlalchemy.orm import joinedload

@router.get("/servizi/{servizio_id}", response_model=ServizioOut)
def get_servizio(servizio_id: int, db: Session = Depends(get_db)):
    servizio = (
        db.query(Servizio)
        .options(
            joinedload(Servizio.creato_da).joinedload(DipendenteTecnico.utente)
        )
        .filter(Servizio.id == servizio_id)
        .first()
    )
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio_to_dict(servizio)

@router.get("/clienti/{cliente_id}/dettagli", response_model=ClienteDettagliOut)
def get_cliente_dettagli(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    utente = cliente.utente
    return {
        "id": cliente.id,
        "nome": utente.nome if utente else None,
        "cognome": utente.cognome if utente else None,
        "email": utente.email if utente else None,
        "numeroTelefonico": utente.numeroTelefonico if utente else None,
    }

@router.get("/dipendente/{dipendente_id}/dettagli", response_model=DipendenteTecnicoDettagliOut)
def get_dipendente_dettagli(dipendente_id: int, db: Session = Depends(get_db)):
    dip = db.get(DipendenteTecnico, dipendente_id)
    if not dip:
        raise HTTPException(status_code=404, detail="Dipendente tecnico non trovato")
    utente = dip.utente
    return {
        "id": dip.id,
        "nome": utente.nome if utente else None,
        "cognome": utente.cognome if utente else None,
        "email": utente.email if utente else None,
        "numeroTelefonico": utente.numeroTelefonico if utente else None,
        "tipo": dip.tipo,
    }

@router.get("/servizi/{servizio_id}/dipendenti", response_model=List[DipendenteTecnicoDettagliOut])
def get_dipendenti_servizio(servizio_id: int, db: Session = Depends(get_db)):
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    dipendenti = servizio.dipendenti
    result = []
    for dip in dipendenti:
        utente = dip.utente
        result.append({
            "id": dip.id,
            "nome": utente.nome if utente else None,
            "cognome": utente.cognome if utente else None,
            "email": utente.email if utente else None,
            "numeroTelefonico": utente.numeroTelefonico if utente else None,
            "tipo": dip.tipo,
        })
    return result

@router.get("/dipendenti/{dipendente_id}/altri_servizi", response_model=List[ServizioOut])
def visualizza_servizi_altri_dipendenti(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi_altri_dipendenti(dipendente_id)]

@router.get("/clienti/{cliente_id}/servizi_approvati", response_model=List[ServizioOut])
def get_servizi_approvati_cliente(cliente_id: int, db: Session = Depends(get_db)):
    servizi = db.query(Servizio).filter(
        Servizio.cliente_id == cliente_id,
        Servizio.statoServizio == StatoServizio.APPROVATO,
        Servizio.is_deleted == False
    ).all()
    return [servizio_to_dict(s) for s in servizi]
#cuheriue