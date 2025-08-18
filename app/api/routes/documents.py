import os
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.schemas.document import DocumentOut
from app.models.user import User
from app.models.document import Document

router = APIRouter()

def user_storage_dir(user_id: int) -> Path:
    return Path(settings.STORAGE_PATH) / f"user_{user_id}"

@router.post("", response_model=DocumentOut)
async def upload_document(
        f: UploadFile = File(...),
        db: Session = Depends(get_db),
        current: User = Depends(get_current_user),
):
    user_dir = user_storage_dir(current.id)
    user_dir.mkdir(parents=True, exist_ok=True)

    dest = user_dir / f.filename
    i = 1
    base, ext = os.path.splitext(f.filename)
    while dest.exists():
        dest = user_dir / f"{base}_{i}{ext}"
        i += 1

    with dest.open("wb") as out:
        content = await f.read()
        out.write(content)

    doc = Document(
        owner_id=current.id,
        filename=dest.name,
        content_type=f.content_type,
        path=str(dest.resolve()),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.get("", response_model=list[DocumentOut])
def list_my_documents(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.owner_id == current.id).order_by(Document.created_at.desc()).all()
    return docs

@router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    doc = db.get(Document, doc_id)
    if not doc or doc.owner_id != current.id:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(doc.path):
        raise HTTPException(status_code=410, detail="File no longer available")
    return FileResponse(path=doc.path, filename=doc.filename, media_type=doc.content_type or "application/octet-stream")