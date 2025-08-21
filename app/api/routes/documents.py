from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
import os
from app.api.deps import get_db
from app.core.config import settings
from app.schemas.document import DocumentazioneOut
from app.models.documentazione import Documentazione
from app.models.enums import TipoDocumentazione
from app.models.cliente import Cliente

router = APIRouter()

STORAGE_DIR = "./storage"

def safe_storage_path(cliente_id: int, filename: str) -> str:
    filename = os.path.basename(filename)
    return os.path.join(STORAGE_DIR, f"{cliente_id}_{filename}")

@router.post("/carica", response_model=DocumentazioneOut)
async def carica_documentazione(
        cliente_id: int = Form(...),
        tipo: TipoDocumentazione = Form(...),
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    print(f"DEBUG /carica: cliente_id={cliente_id}, tipo={tipo}, file.filename={getattr(file, 'filename', None)}")
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        print(f"DEBUG /carica: Cliente con id={cliente_id} non trovato!")
        raise HTTPException(status_code=404, detail="Cliente non trovato")

    os.makedirs(STORAGE_DIR, exist_ok=True)
    path = safe_storage_path(cliente_id, file.filename)
    print(f"DEBUG /carica: path={path}")
    with open(path, "wb") as f:
        data = await file.read()
        print(f"DEBUG /carica: file size={len(data)} bytes")
        f.write(data)

    doc = Documentazione(
        cliente_id=cliente_id,
        filename=file.filename,
        tipo=tipo,
        path=path,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    print(f"DEBUG /carica: Documentazione creata id={doc.id}")
    return doc

@router.get("/visualizza/{cliente_id}", response_model=list[DocumentazioneOut])
def visualizza_documentazione(cliente_id: int, db: Session = Depends(get_db)):
    print(f"DEBUG /visualizza: cliente_id={cliente_id}")
    docs = db.query(Documentazione).filter(Documentazione.cliente_id == cliente_id).all()
    print(f"DEBUG /visualizza: trovate {len(docs)} documentazioni")
    return docs

@router.put("/sostituisci/{doc_id}", response_model=DocumentazioneOut)
async def sostituisci_documentazione(
        doc_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    print(f"DEBUG /sostituisci: doc_id={doc_id}, file.filename={getattr(file, 'filename', None)}")
    doc = db.get(Documentazione, doc_id)
    if not doc:
        print(f"DEBUG /sostituisci: Documentazione id={doc_id} non trovata!")
        raise HTTPException(status_code=404, detail="Documentazione non trovata")
    path = doc.path
    print(f"DEBUG /sostituisci: sovrascrivo path={path}")
    with open(path, "wb") as f:
        data = await file.read()
        print(f"DEBUG /sostituisci: file size={len(data)} bytes")
        f.write(data)
    doc.filename = file.filename
    db.add(doc)
    db.commit()
    db.refresh(doc)
    print(f"DEBUG /sostituisci: Documentazione aggiornata id={doc.id}")
    return doc