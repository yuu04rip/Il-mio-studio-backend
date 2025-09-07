from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.schemas.dipendente import DipendenteTecnicoOut
from app.schemas.notaio import NotaioOut
from app.models.user import User
from app.models.enums import TipoDipendenteTecnico, Role
from app.schemas.user import UserCreate
from app.core.security import hash_password  # <-- IMPORTANTE!

router = APIRouter()

@router.post("/add-dipendente", response_model=DipendenteTecnicoOut)
def add_dipendente(
        user_data: UserCreate,
        tipo: TipoDipendenteTecnico,
        db: Session = Depends(get_db)
):
    exist = db.query(User).filter(User.email == user_data.email).first()
    if exist:
        raise HTTPException(status_code=400, detail="Dipendente già esistente")
    data = user_data.dict()
    data.pop('ruolo', None)
    # Hash della password!
    data['password'] = hash_password(data['password'])
    user = User(**data, ruolo=Role.DIPENDENTE)
    db.add(user)
    db.commit()
    db.refresh(user)
    dipendente = DipendenteTecnico(utente_id=user.id, tipo=tipo)
    db.add(dipendente)
    db.commit()
    db.refresh(dipendente)
    return dipendente

@router.post("/add-notaio", response_model=NotaioOut)
def add_notaio(
        user_data: UserCreate,
        codice_notarile: int = Query(...),
        db: Session = Depends(get_db)
):
    # Controllo email unica
    exist = db.query(User).filter(User.email == user_data.email).first()
    if exist:
        raise HTTPException(status_code=400, detail="Notaio già esistente")

    # Controllo codice notarile unico
    existing_codice = db.query(Notaio).filter(Notaio.codice_notarile == codice_notarile).first()
    if existing_codice:
        raise HTTPException(status_code=400, detail="Codice notarile già utilizzato")

    data = user_data.dict()
    data.pop('ruolo', None)
    # Hash della password!
    data['password'] = hash_password(data['password'])

    # Crea direttamente il Notaio (e quindi anche User e DipendenteTecnico)
    notaio = Notaio(
        utente=User(**data, ruolo=Role.NOTAIO),
        tipo=TipoDipendenteTecnico.NOTAIO,
        codice_notarile=codice_notarile
    )
    db.add(notaio)
    db.commit()
    db.refresh(notaio)
    return notaio

@router.delete("/dipendente/{dipendente_id}")
def distruggi_dipendente(dipendente_id: int, db: Session = Depends(get_db)):
    dip = db.get(DipendenteTecnico, dipendente_id)
    if not dip:
        raise HTTPException(status_code=404, detail="Dipendente non trovato")
    db.delete(dip)
    db.commit()
    return {"ok": True}

@router.get("/dipendente/{dipendente_id}/servizi", response_model=list)
def visualizza_lavoro_da_svolgere(dipendente_id: int, db: Session = Depends(get_db)):
    dip = db.get(DipendenteTecnico, dipendente_id)
    if not dip:
        raise HTTPException(status_code=404, detail="Dipendente non trovato")
    return [s for s in dip.servizi if not s.statoServizio]

@router.get("/dipendente/{dipendente_id}/servizi_inizializzati", response_model=list)
def visualizza_servizi_inizializzati(dipendente_id: int, db: Session = Depends(get_db)):
    dip = db.get(DipendenteTecnico, dipendente_id)
    if not dip:
        raise HTTPException(status_code=404, detail="Dipendente non trovato")
    return [s for s in dip.servizi if s.statoServizio]