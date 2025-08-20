from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.services import Servizio
from app.schemas.services import ServizioOut

router = APIRouter()

@router.post("/archivia", response_model=ServizioOut)
def archivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Servizio non trovato")
    servizio.statoServizio = True
    db.add(servizio)
    db.commit()
    db.refresh(servizio)
    return servizio