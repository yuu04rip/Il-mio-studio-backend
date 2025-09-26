from fastapi import APIRouter, Depends, HTTPException, Request, Query, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.core.email import send_email
from app.services.gestore_studio import GestoreStudio
from app.core.security import hash_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.models.services import Servizio
from app.models.documentazione import Documentazione
from app.models.enums import TipoDipendenteTecnico, TipoServizio, TipoDocumentazione
from app.schemas.user import UserCreate
from app.schemas.dipendente import DipendenteTecnicoOut
from app.schemas.notaio import NotaioOut
from app.schemas.cliente import ClienteOut
from app.schemas.services import ServizioOut
from app.schemas.document import DocumentazioneOut

import os

router = APIRouter()
STORAGE_DIR = "./storage"

def safe_storage_path(cliente_id: int, filename: str) -> str:
    filename = os.path.basename(filename)
    return os.path.join(STORAGE_DIR, f"{cliente_id}_{filename}")

# --- DIPENDENTI & NOTAI ---

@router.delete("/dipendente/{dipendente_id}")
def elimina_dipendente(dipendente_id: int, db: Session = Depends(get_db)):
    """
    SOFT DELETE: Rimuove il dipendente solo dalla lista (non dal database).
    """
    gestore = GestoreStudio(db)
    ok = gestore.elimina_dipendente(dipendente_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dipendente non trovato nella lista")
    return {"ok": True}

@router.delete("/dipendente/{dipendente_id}/distruggi")
def distruggi_dipendente(dipendente_id: int, db: Session = Depends(get_db)):
    """
    HARD DELETE: Elimina il dipendente effettivamente dal database.
    """
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
@router.get("/clienti/search/", response_model=List[ClienteOut])
def search_clienti(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    clienti = gestore.search_clienti(q)
    return clienti

@router.get("/clienti/nome/{nome}", response_model=ClienteOut)
def cerca_cliente_per_nome(nome: str, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    cliente = gestore.cerca_cliente_per_nome(nome)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return cliente
@router.post("/servizi/richiesta-chat")
async def richiesta_servizio_chat(
        request: Request,
        cliente_id: int = Form(None),  # <-- Form(None) per accettare anche json!
        testo: str = Form(None),
        db: Session = Depends(get_db)
):
    # Se non arrivano come form, prova a leggere dal JSON
    if cliente_id is None or testo is None:
        try:
            body = await request.json()
            cliente_id = body.get("cliente_id")
            testo = body.get("testo")
        except Exception:
            raise HTTPException(status_code=400, detail="Missing parameters cliente_id and testo")

    if cliente_id is None or testo is None:
        raise HTTPException(status_code=400, detail="Missing parameters cliente_id and testo")

    # Recupera il cliente e la sua email
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
    """
    SOFT DELETE: Rimuove il servizio solo dalla lista (non dal database).
    """
    gestore = GestoreStudio(db)
    ok = gestore.elimina_servizio(servizio_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Servizio non trovato nella lista")
    return {"ok": True}

@router.delete("/servizi/{servizio_id}/distruggi")
def distruggi_servizio(servizio_id: int, db: Session = Depends(get_db)):
    """
    HARD DELETE: Elimina il servizio effettivamente dal database.
    """
    gestore = GestoreStudio(db)
    ok = gestore.distruggi_servizio(servizio_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Servizio non trovato nel database")
    return {"ok": True}
# Inizializza servizio (dipendente tecnico)
@router.post("/servizi/{servizio_id}/inizializza")
def inizializza_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.inizializza_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o già inizializzato")
    return servizio

# Inoltra atto al notaio (dipendente tecnico)
@router.post("/servizi/{servizio_id}/inoltra-notaio")
def inoltra_servizio_notaio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.inoltra_servizio_notaio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o non in lavorazione")
    return servizio

# Lista servizi da approvare (notaio)
@router.get("/notai/servizi", response_model=list)
def servizi_da_approvare(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.servizi_da_approvare()

# Approva atto (notaio)
@router.post("/servizi/{servizio_id}/approva")
def approva_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.approva_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o non in attesa approvazione")
    return servizio

# Rifiuta atto (notaio)
@router.post("/servizi/{servizio_id}/rifiuta")
def rifiuta_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.rifiuta_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato o non in attesa approvazione")
    return servizio

# Assegna servizio a dipendente (gestore studio)
@router.put("/servizi/{servizio_id}/assegna")
def assegna_servizio(servizio_id: int, dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    ok = gestore.assegna_servizio(servizio_id, dipendente_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Servizio o dipendente non trovato")
    return {"ok": True}


# --- DOCUMENTAZIONE ---

@router.post("/documenti/carica", response_model=DocumentazioneOut)
async def carica_documentazione(
        cliente_id: int = Form(...),
        tipo: TipoDocumentazione = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    gestore = GestoreStudio(db)
    os.makedirs(STORAGE_DIR, exist_ok=True)
    path = safe_storage_path(cliente_id, file.filename)
    with open(path, "wb") as f:
        data = await file.read()
        f.write(data)
    doc = gestore.aggiungi_documentazione(
        cliente_id=cliente_id,
        filename=file.filename,
        tipo=tipo,
        path=path,
    )
    return doc

@router.get("/documenti/visualizza/{cliente_id}", response_model=List[DocumentazioneOut])
def visualizza_documentazione(cliente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.visualizza_documentazione_cliente(cliente_id)

@router.put("/documenti/sostituisci/{doc_id}", response_model=DocumentazioneOut)
async def sostituisci_documentazione(
        doc_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    gestore = GestoreStudio(db)
    doc = db.get(Documentazione, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentazione non trovata")
    path = doc.path
    with open(path, "wb") as f:
        data = await file.read()
        f.write(data)
    return gestore.sostituisci_documentazione(doc_id, filename=file.filename, path=path)
from app.utils.serializers import servizio_to_dict

@router.post("/servizi", response_model=ServizioOut)
async def crea_servizio(
        request: Request,
        cliente_id: int = Form(None),
        tipo: TipoServizio = Form(None),
        codiceCorrente: int = Form(None),
        codiceServizio: int = Form(None),
        dipendente_id: int = Form(None),
        db: Session = Depends(get_db)
):
    from datetime import datetime
    if None in (cliente_id, tipo, codiceCorrente, codiceServizio, dipendente_id):
        try:
            body = await request.json()
            cliente_id = body.get("cliente_id", cliente_id)
            tipo = body.get("tipo", tipo)
            codiceCorrente = body.get("codiceCorrente", codiceCorrente)
            codiceServizio = body.get("codiceServizio", codiceServizio)
            dipendente_id = body.get("dipendente_id", dipendente_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Dati mancanti nella request")
    for v in [cliente_id, tipo, codiceCorrente, codiceServizio, dipendente_id]:
        if v is None:
            raise HTTPException(status_code=422, detail="Tutti i campi sono obbligatori")
    gestore = GestoreStudio(db)
    now = datetime.now()
    servizio = gestore.aggiungi_servizio(
        cliente_id=cliente_id,
        tipo=tipo,
        codiceCorrente=codiceCorrente,
        codiceServizio=codiceServizio,
        dataRichiesta=now,
        dataConsegna=now,
        dipendente_id=dipendente_id
    )
    return servizio_to_dict(servizio)

@router.get("/servizi/", response_model=List[ServizioOut])
def visualizza_servizi(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi()]

@router.get("/servizi/codice/{codice_servizio}", response_model=ServizioOut)
def cerca_servizio_per_codice(codice_servizio: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.cerca_servizio_per_codice(codice_servizio)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio_to_dict(servizio)

@router.get("/servizi", response_model=List[ServizioOut])
def visualizza_servizi(cliente_id: int = Query(None), db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    if cliente_id is not None:
        return [servizio_to_dict(s) for s in gestore.visualizza_servizi_cliente(cliente_id)]
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi()]
# --- SERVIZI ARCHIVIATI (delega a GestoreBackup tramite GestoreStudio) ---
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

# --- DIPENDENTE: LAVORO ASSEGNATO ---
@router.get("/dipendente/{dipendente_id}/servizi", response_model=List[ServizioOut])
def visualizza_lavoro_da_svolgere(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_lavoro_da_svolgere(dipendente_id)]

@router.get("/dipendente/{dipendente_id}/servizi_inizializzati", response_model=List[ServizioOut])
def visualizza_servizi_inizializzati(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return [servizio_to_dict(s) for s in gestore.visualizza_servizi_inizializzati(dipendente_id)]
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