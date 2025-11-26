from typing import List

import io
from mimetypes import guess_type
from urllib.parse import quote

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse

from app.api.deps import get_db
from app.schemas.document import DocumentazioneOut
from app.models.documentazione import Documentazione
from app.models.enums import TipoDocumentazione
from app.models.services import Servizio
from app.services.gestore_studio import GestoreStudio

router = APIRouter()


@router.get("/servizi/{servizio_id}/documenti", response_model=List[DocumentazioneOut])
def visualizza_documentazione_servizio(servizio_id: int, db: Session = Depends(get_db)):
    return db.query(Documentazione).filter(Documentazione.servizio_id == servizio_id).all()


@router.post("/servizi/{servizio_id}/documenti/carica", response_model=DocumentazioneOut)
async def carica_documentazione_servizio(
        servizio_id: int,
        tipo: TipoDocumentazione = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    cliente_id = servizio.cliente_id
    data = await file.read()
    gestore = GestoreStudio(db)
    doc = gestore.aggiungi_documentazione(
        cliente_id=cliente_id,
        servizio_id=servizio_id,
        filename=file.filename,
        tipo=tipo,
        data=data
    )
    if doc not in servizio.lavoroCaricato:
        servizio.lavoroCaricato.append(doc)
        db.commit()
    return doc


@router.put("/servizi/{servizio_id}/documenti/{doc_id}/sostituisci", response_model=DocumentazioneOut)
async def sostituisci_documentazione_servizio(
        servizio_id: int,
        doc_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    doc = db.get(Documentazione, doc_id)
    if not doc or doc.servizio_id != servizio_id:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    data = await file.read()
    gestore = GestoreStudio(db)
    doc = gestore.sostituisci_documentazione(doc_id, filename=file.filename, data=data)
    servizio = db.get(Servizio, servizio_id)
    if servizio and doc not in servizio.lavoroCaricato:
        servizio.lavoroCaricato.append(doc)
        db.commit()
    return doc


@router.get("/download/{doc_id}")
def download_documentazione(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Documentazione, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentazione non trovata")
    ext = (doc.filename or "").split(".")[-1].lower()
    mime, _ = guess_type(doc.filename)
    disposition_type = "inline" if ext in ["pdf", "jpg", "jpeg", "png"] else "attachment"
    ascii_filename = doc.filename.encode('ascii', 'ignore').decode('ascii') or "documento"
    quoted_filename = quote(doc.filename)
    content_disposition = (
        f'{disposition_type}; filename="{ascii_filename}"; filename*=UTF-8\'\'{quoted_filename}'
    )
    return StreamingResponse(
        io.BytesIO(doc.data),
        media_type=mime or "application/octet-stream",
        headers={"Content-Disposition": content_disposition}
    )


@router.delete("/servizi/{servizio_id}/documenti/{doc_id}", response_model=DocumentazioneOut)
def elimina_documentazione_servizio(
        servizio_id: int,
        doc_id: int,
        db: Session = Depends(get_db)
):
    doc = db.get(Documentazione, doc_id)
    if not doc or doc.servizio_id != servizio_id:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    servizio = db.get(Servizio, servizio_id)
    if servizio and doc in servizio.lavoroCaricato:
        servizio.lavoroCaricato.remove(doc)
    db.delete(doc)
    db.commit()
    return doc


# --- Nuovi endpoint per l'API frontend (client-level) ---

@router.post("/documenti/carica", response_model=DocumentazioneOut)
async def carica_documentazione_cliente(
        cliente_id: int = Form(...),
        tipo: TipoDocumentazione = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Endpoint chiamato dal frontend:
    client: carica_documentazione_cliente(self, cliente_id, tipo, filepath)
    - riceve cliente_id e tipo via form e un file multipart
    - salva la documentazione con servizio_id = None
    """
    data = await file.read()
    gestore = GestoreStudio(db)
    # servizio_id = None perché è documentazione legata al cliente, non ad un servizio specifico
    doc = gestore.aggiungi_documentazione(
        cliente_id=cliente_id,
        servizio_id=None,
        filename=file.filename,
        tipo=tipo,
        data=data
    )
    # Non ci sono relazioni con Servizio da gestire qui.
    return doc


@router.get("/documenti/visualizza/{cliente_id}", response_model=List[DocumentazioneOut])
def visualizza_documentazione_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """
    Endpoint chiamato dal frontend:
    client: visualizza_documentazione_cliente(self, cliente_id)
    - restituisce tutte le documentazioni associate al cliente (servizio_id può essere anche None)
    """
    return db.query(Documentazione).filter(Documentazione.cliente_id == cliente_id).all()


@router.put("/documenti/sostituisci/{doc_id}", response_model=DocumentazioneOut)
async def sostituisci_documentazione_cliente(
        doc_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    Endpoint chiamato dal frontend:
    client: sostituisci_documentazione_cliente(self, doc_id, filepath)
    - sostituisce i dati del documento indicato (indipendentemente da servizio/cliente)
    """
    doc = db.get(Documentazione, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")
    data = await file.read()
    gestore = GestoreStudio(db)
    doc = gestore.sostituisci_documentazione(doc_id, filename=file.filename, data=data)
    # Se il documento è collegato ad un servizio e serve mantenerlo nella relazione, GestoreStudio dovrebbe
    # già aggiornare gli oggetti mappati; altrimenti eventuale logica aggiuntiva può essere inserita qui.
    return doc


# --- Nuovo endpoint DELETE per compatibilità frontend ---
@router.delete("/documenti/{doc_id}", response_model=DocumentazioneOut)
def elimina_documentazione_by_id(
        doc_id: int,
        db: Session = Depends(get_db)
):
    """
    Elimina un documento dato il suo id indipendentemente dal fatto che sia collegato a un servizio.
    Se è collegato a un servizio rimuove anche la relazione servizio.lavoroCaricato.
    Questo endpoint risponde a DELETE /documentazione/documenti/{doc_id} quando il router è incluso
    con prefix="/documentazione".
    """
    doc = db.get(Documentazione, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento non trovato")

    # Se collegato a un servizio, rimuoviamo il riferimento
    servizio_id = getattr(doc, "servizio_id", None)
    if servizio_id is not None:
        servizio = db.get(Servizio, servizio_id)
        if servizio and doc in getattr(servizio, "lavoroCaricato", []):
            servizio.lavoroCaricato.remove(doc)
            db.add(servizio)

    db.delete(doc)
    db.commit()
    return doc