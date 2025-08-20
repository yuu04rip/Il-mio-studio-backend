import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from app.schemas.document import DocumentazioneOut
from app.models.documentazione import Documentazione
from app.models.enums import TipoDocumentazione
from app.models.cliente import Cliente

router = APIRouter()

@router.post("/carica", response_model=DocumentazioneOut)
async def carica_documentazione(
        cliente_id: int,
        tipo: TipoDocumentazione,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    path = f"./storage/{cliente_id}_{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    doc = Documentazione(
        cliente_id=cliente_id,
        filename=file.filename,
        tipo=tipo,
        path=path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.get("/visualizza/{cliente_id}", response_model=list[DocumentazioneOut])
def visualizza_documentazione(cliente_id: int, db: Session = Depends(get_db)):
    docs = db.query(Documentazione).filter(Documentazione.cliente_id == cliente_id).all()
    return docs

@router.put("/sostituisci/{doc_id}", response_model=DocumentazioneOut)
async def sostituisci_documentazione(doc_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    doc = db.get(Documentazione, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documentazione non trovata")
    path = doc.path
    with open(path, "wb") as f:
        f.write(await file.read())
    doc.filename = file.filename
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc