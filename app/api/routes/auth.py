from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.api.deps import get_db
from app.core.security import hash_password, create_access_token
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.schemas.user import ChangePasswordRequest
from app.services.gestore_login import GestoreLogin

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
    gestore = GestoreLogin(db)
    gestore.aggiungi_utente(user)
    if ruolo == Role.CLIENTE:
        cliente = Cliente(utente_id=user.id)
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    gestore = GestoreLogin(db)
    user = gestore.login(payload.email, payload.password, getattr(payload, "codice_notarile", None))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali non valide")
    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)

@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, db: Session = Depends(get_db)):
    gestore = GestoreLogin(db)
    ok = gestore.change_password(
        payload.email,
        payload.old_password,
        payload.new_password,
        getattr(payload, "codice_notarile", None)
    )
    if not ok:
        raise HTTPException(status_code=401, detail="Credenziali non valide o codice notarile errato")
    return {"msg": "Password aggiornata con successo"}

@router.post('/logout')
async def logout():
    # Qui non c'è nulla da fare lato backend, il logout è gestito solo lato client.
    return JSONResponse(content={"message": "Logout effettuato"})