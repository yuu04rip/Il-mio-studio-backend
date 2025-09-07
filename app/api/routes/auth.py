from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.models.user import User, Role
from app.models.cliente import Cliente  # <-- IMPORTA Cliente!
from app.models.dipendente import DipendenteTecnico
from app.models.notaio import Notaio
from app.schemas.user import ChangePasswordRequest

router = APIRouter()

@router.post("/register", response_model=Token)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    ruolo_value = payload.ruolo
    ruolo = Role(ruolo_value) if ruolo_value in {r.value for r in Role} else Role.CLIENTE
    user = User(
        email=payload.email,
        nome=payload.nome,
        cognome=payload.cognome,
        numeroTelefonico=payload.numeroTelefonico,
        password=hash_password(payload.password),
        ruolo=ruolo,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # CREA ANCHE IL CLIENTE se il ruolo è CLIENTE!
    if ruolo == Role.CLIENTE:
        cliente = Cliente(utente_id=user.id)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)

    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali non valide")
    if user.ruolo == Role.NOTAIO:
        # Cerca direttamente il notaio collegato a quell'utente
        notaio = db.query(Notaio).filter(Notaio.utente_id == user.id).first()
        if not notaio or payload.codice_notarile != notaio.codice_notarile:
            raise HTTPException(status_code=401, detail="Codice notarile errato")
    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)

@router.post("/change-password")
def change_password(
        payload: ChangePasswordRequest,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.old_password, user.password):
        raise HTTPException(status_code=401, detail="Credenziali non valide")

    # Se è notaio, controlla il codice notarile
    if user.ruolo == Role.NOTAIO:
        notaio = db.query(Notaio).filter(Notaio.utente_id == user.id).first()
        if not notaio or payload.codice_notarile != notaio.codice_notarile:
            raise HTTPException(status_code=401, detail="Codice notarile errato")

    user.password = hash_password(payload.new_password)
    db.commit()
    return {"msg": "Password aggiornata con successo"}