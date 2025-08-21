from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.schemas.dipendente import DipendenteTecnicoOut
from app.schemas.notaio import NotaioOut
from app.models.user import User
from app.models.enums import TipoDipendenteTecnico, Role
from app.schemas.user import UserCreate
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
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
    exist = db.query(User).filter(User.email == user_data.email).first()
    if exist:
        raise HTTPException(status_code=400, detail="Notaio già esistente")
    data = user_data.dict()
    data.pop('ruolo', None)
    user = User(**data, ruolo=Role.NOTAIO)
    db.add(user)
    db.commit()
    db.refresh(user)
    notaio = Notaio(utente_id=user.id, codice_notarile=codice_notarile)
    db.add(notaio)
    db.commit()
    db.refresh(notaio)
    return notaio