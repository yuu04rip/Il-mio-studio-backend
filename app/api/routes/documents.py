from mimetypes import guess_type
from urllib.parse import quote

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
import os
from fastapi.responses import FileResponse
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
        f"{disposition_type}; filename=\"{ascii_filename}\"; filename*=UTF-8''{quoted_filename}"
    )
    return FileResponse(
        path=doc.path,
        filename=doc.filename,
        media_type=mime or "application/octet-stream",
        headers={"Content-Disposition": content_disposition}
    )