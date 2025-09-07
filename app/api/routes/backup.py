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

@router.get("/servizi/archiviati", response_model=list[ServizioOut])
def mostra_servizi_archiviati(db: Session = Depends(get_db)):
    return db.query(Servizio).filter(Servizio.statoServizio == True).all()

@router.put("/servizi/archiviati/{servizio_id}", response_model=ServizioOut)
def modifica_servizio_archiviato(servizio_id: int, statoServizio: bool, db: Session = Depends(get_db)):
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    servizio.statoServizio = statoServizio
    db.add(servizio)
    db.commit()
    db.refresh(servizio)
    return servizio
