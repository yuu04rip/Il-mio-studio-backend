from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.services.gestore_backup import GestoreBackup
from app.models.services import Servizio
from app.schemas.services import ServizioOut
from app.services.gestore_studio import GestoreStudio

router = APIRouter()

@router.post("/backup/inizializza")
def inizializza_backup(db: Session = Depends(get_db)):
    gestore = GestoreStudio(db)
    gestore.inizializza_archiviazione()
    return {"msg": "Backup inizializzato correttamente"}

@router.post("/archivia-servizio/{servizio_id}", response_model=ServizioOut)
def archivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    backup.archivia_servizio(servizio)
    db.refresh(servizio)
    return servizio

@router.put("/dearchivia-servizio/{servizio_id}", response_model=ServizioOut)
def dearchivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    backup.dearchivia_servizio(servizio)
    db.refresh(servizio)
    return servizio

@router.put("/modifica-servizio-archiviato/{servizio_id}", response_model=ServizioOut)
def modifica_servizio_archiviato(servizio_id: int, statoServizio: bool, db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    backup.modifica_servizio_archiviato(servizio, statoServizio)
    db.refresh(servizio)
    return servizio

@router.delete("/elimina-servizio-archiviato/{servizio_id}")
def elimina_servizio_archiviato(servizio_id: int, db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    successo = backup.elimina_servizio_archiviato(servizio_id)
    if not successo:
        raise HTTPException(status_code=404, detail="Servizio archiviato non trovato o già eliminato")
    return {"msg": "Servizio archiviato eliminato con successo"}

@router.get("/servizi-archiviati", response_model=List[ServizioOut])
def mostra_servizi_archiviati(db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    return backup.mostra_servizi_archiviati()