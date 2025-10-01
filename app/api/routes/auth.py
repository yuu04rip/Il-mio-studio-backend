from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.models import Notaio
from app.schemas.user import UserOut
from app.schemas.auth import ChangeEmailRequest, RegisterNotaioRequest
from app.api.deps import get_current_user
from app.api.deps import get_db
from app.core.security import hash_password, create_access_token, verify_password
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
    # CASE-INSENSITIVE
    ruolo_value = payload.ruolo.upper() if payload.ruolo else "CLIENTE"
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
    elif ruolo == Role.NOTAIO:
        if not payload.codice_notarile:
            raise HTTPException(status_code=400, detail="Codice notarile obbligatorio per il notaio")
        notaio = Notaio(utente_id=user.id, codice_notarile=payload.codice_notarile)
        db.add(notaio)
        db.commit()
        db.refresh(notaio)
    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)
@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    gestore = GestoreLogin(db)
    user = gestore.login(payload.email, payload.password, getattr(payload, "codice_notarile", None))
    print("Payload login:", payload)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenziali non valide")
    if hasattr(payload, "ruolo") and payload.ruolo:
        ruolo_richiesto = payload.ruolo.upper()
        ruolo_reale = user.ruolo.value.upper()
        if ruolo_richiesto != ruolo_reale:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruolo non autorizzato")
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
@router.post("/change-email", response_model=UserOut)
def change_email(
        payload: ChangeEmailRequest,
        db: Session = Depends(get_db),
        current: User = Depends(get_current_user)
):
    # Verifica password
    if not verify_password(payload.password, current.password):
        raise HTTPException(status_code=400, detail="Password errata")
    # Email deve essere unica
    if db.query(User).filter(User.email == payload.new_email).first():
        raise HTTPException(status_code=400, detail="Email già registrata")
    current.email = payload.new_email
    db.commit()
    db.refresh(current)
    return current
@router.post("/register-notaio", response_model=Token)
def register_notaio(payload: RegisterNotaioRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    # Verifica unicità codice notarile
    if db.query(Notaio).filter(Notaio.codice_notarile == payload.codice_notarile).first():
        raise HTTPException(status_code=400, detail="Codice notarile già registrato")
    user = User(
        email=payload.email,
        nome=payload.nome,
        cognome=payload.cognome,
        numeroTelefonico=payload.numeroTelefonico,
        password=hash_password(payload.password),
        ruolo=Role.NOTAIO,
    )
    gestore = GestoreLogin(db)
    gestore.aggiungi_utente(user)
    notaio = Notaio(utente_id=user.id, codice_notarile=payload.codice_notarile)
    db.add(notaio)
    db.commit()
    db.refresh(notaio)
    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)
@router.post("/register-dipendente", response_model=Token)
def register_dipendente(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    ruolo = Role.DIPENDENTE
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

    # Qui puoi fare:
    from app.models.dipendente import DipendenteTecnico
    from app.models.enums import TipoDipendenteTecnico

    tipo = getattr(payload, "tipo", None)
    if not tipo:
        tipo = TipoDipendenteTecnico.DIPENDENTE
    elif isinstance(tipo, str):
        tipo = TipoDipendenteTecnico(tipo)

    dipendente_tecnico = DipendenteTecnico(
        utente_id=user.id,
        tipo=tipo,
    )
    db.add(dipendente_tecnico)
    db.commit()
    db.refresh(dipendente_tecnico)

    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)