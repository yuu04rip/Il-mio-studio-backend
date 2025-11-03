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

@router.get("/servizi/{servizio_id}/documenti", response_model=list[DocumentazioneOut])
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