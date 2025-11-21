from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.services.gestore_backup import GestoreBackup
from app.models.services import Servizio
from app.schemas.services import ServizioOut
from app.utils.serializers import servizio_to_dict

router = APIRouter(prefix="/backup")

@router.post("/inizializza")
def inizializza_backup(db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    backup.setup_backup()
    return {"msg": "Backup inizializzato correttamente"}

@router.post("/archivia-servizio/{servizio_id}", response_model=ServizioOut)
def archivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    servizio = backup.archivia_servizio(servizio)
    return servizio_to_dict(servizio)

@router.put("/dearchivia-servizio/{servizio_id}", response_model=ServizioOut)
def dearchivia_servizio(servizio_id: int, db: Session = Depends(get_db)):
    backup = GestoreBackup(db)
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    servizio = backup.dearchivia_servizio(servizio)
    return servizio_to_dict(servizio)

@router.put("/modifica-servizio-archiviato/{servizio_id}", response_model=ServizioOut)
def modifica_servizio_archiviato(servizio_id: int, payload: dict = Body(...), db: Session = Depends(get_db)):
    """
    payload should contain: { "archived": true|false }
    """
    archived = payload.get("archived")
    if archived is None:
        raise HTTPException(status_code=422, detail="Campo 'archived' obbligatorio")
    backup = GestoreBackup(db)
    servizio = db.get(Servizio, servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="Servizio non trovato")
    servizio = backup.modifica_servizio_archiviato(servizio, archived)
    return servizio_to_dict(servizio)

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
    servizi = backup.mostra_servizi_archiviati()
    return [servizio_to_dict(s) for s in servizi]