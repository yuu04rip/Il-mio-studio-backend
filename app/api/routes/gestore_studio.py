from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
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

@router.get("/notai/", response_model=List[NotaioOut])
def get_notai(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.get_notai()

# --- CLIENTI ---

@router.get("/clienti/", response_model=List[ClienteOut])
def get_clienti(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.get_clienti()

@router.get("/clienti/nome/{nome}", response_model=ClienteOut)
def cerca_cliente_per_nome(nome: str, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    cliente = gestore.cerca_cliente_per_nome(nome)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return cliente

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

@router.post("/servizi", response_model=ServizioOut)
def crea_servizio(
        cliente_id: int = Form(...),
        tipo: TipoServizio = Form(...),
        codiceCorrente: int = Form(...),
        codiceServizio: int = Form(...),
        db: Session = Depends(get_db)
):
    from datetime import datetime
    gestore = GestoreStudio(db)
    now = datetime.now()
    servizio = gestore.aggiungi_servizio(
        cliente_id=cliente_id,
        tipo=tipo,
        codiceCorrente=codiceCorrente,
        codiceServizio=codiceServizio,
        dataRichiesta=now,
        dataConsegna=now,
    )
    return servizio

@router.get("/servizi/", response_model=List[ServizioOut])
def visualizza_servizi(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.visualizza_servizi()

@router.get("/servizi/codice/{codice_servizio}", response_model=ServizioOut)
def cerca_servizio_per_codice(codice_servizio: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.cerca_servizio_per_codice(codice_servizio)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio

# --- SERVIZI ARCHIVIATI (delega a GestoreBackup tramite GestoreStudio) ---

@router.post("/servizi/{servizio_id}/archivia", response_model=ServizioOut)
def archivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.archivia_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio

@router.put("/servizi/{servizio_id}/modifica-archiviazione", response_model=ServizioOut)
def modifica_servizio_archiviato(servizio_id: int, statoServizio: bool, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    servizio = gestore.modifica_servizio_archiviato(servizio_id, statoServizio)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    return servizio

@router.get("/servizi/archiviati", response_model=List[ServizioOut])
def visualizza_servizi_archiviati(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.visualizza_servizi_archiviati()

# --- DIPENDENTE: LAVORO ASSEGNATO ---

@router.get("/dipendente/{dipendente_id}/servizi", response_model=List[ServizioOut])
def visualizza_lavoro_da_svolgere(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.visualizza_lavoro_da_svolgere(dipendente_id)

@router.get("/dipendente/{dipendente_id}/servizi_inizializzati", response_model=List[ServizioOut])
def visualizza_servizi_inizializzati(dipendente_id: int, db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    return gestore.visualizza_servizi_inizializzati(dipendente_id)

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