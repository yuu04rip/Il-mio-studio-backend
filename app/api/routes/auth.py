from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Body
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from app.models import Notaio
from app.schemas.user import UserOut, ChangePasswordRequest
from app.schemas.auth import ChangeEmailRequest, RegisterNotaioRequest, LoginRequest, RegisterRequest, Token
from app.api.deps import get_current_user, get_db
from app.core.security import hash_password, create_access_token, verify_password
from app.models.user import User, Role
from app.models.cliente import Cliente
from app.services.gestore_login import GestoreLogin

# per invio email e generazione password temporanea
from app.core.email import send_email
import secrets

router = APIRouter()

@router.post("/register", response_model=Token)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email già registrata")
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
    # Logout gestito solo lato client.
    return JSONResponse(content={"message": "Logout effettuato"})

@router.post("/change-email", response_model=UserOut)
def change_email(
        payload: ChangeEmailRequest,
        db: Session = Depends(get_db),
        current: User = Depends(get_current_user)
):
    if not verify_password(payload.password, current.password):
        raise HTTPException(status_code=400, detail="Password errata")
    if db.query(User).filter(User.email == payload.new_email).first():
        raise HTTPException(status_code=400, detail="Email già registrata")
    current.email = payload.new_email
    db.commit()
    db.refresh(current)
    return current

@router.post("/register-notaio", response_model=Token)
def register_notaio(payload: RegisterNotaioRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email già registrata")
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
    """
    Crea un dipendente tecnico. Se la password non è fornita nel payload,
    viene generata una password temporanea che verrà inviata via email al dipendente.
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email già registrata")

    # password opzionale: se non fornita, genero una temporanea
    pw_raw = getattr(payload, "password", None)
    if not pw_raw:
        pw_raw = secrets.token_urlsafe(10)

    ruolo = Role.DIPENDENTE
    user = User(
        email=payload.email,
        nome=payload.nome,
        cognome=payload.cognome,
        numeroTelefonico=payload.numeroTelefonico,
        password=hash_password(pw_raw),
        ruolo=ruolo,
    )
    gestore = GestoreLogin(db)
    gestore.aggiungi_utente(user)

    from app.models.dipendente import DipendenteTecnico
    from app.models.enums import TipoDipendenteTecnico

    tipo = getattr(payload, "tipo", None)
    if not tipo:
        tipo = TipoDipendenteTecnico.DIPENDENTE
    elif isinstance(tipo, str):
        try:
            tipo = TipoDipendenteTecnico(tipo)
        except Exception:
            # fallback safe
            tipo = TipoDipendenteTecnico.DIPENDENTE

    dipendente_tecnico = DipendenteTecnico(
        utente_id=user.id,
        tipo=tipo,
    )
    db.add(dipendente_tecnico)
    db.commit()
    db.refresh(dipendente_tecnico)

    # Invia email con credenziali (se fallisce l'invio non rollbackiamo la creazione)
    try:
        subject = "Credenziali accesso - Il Mio Studio"
        body = (
            f"Ciao {user.nome},\n\n"
            f"Il tuo account dipendente è stato creato.\n\n"
            f"Email: {user.email}\n"
            f"Password temporanea: {pw_raw}\n\n"
            f"Accedi e modifica la password al primo accesso.\n\n"
            "Se non aspettavi questa email, contatta lo studio.\n"
        )
        send_email(to=user.email, subject=subject, body=body)
    except Exception as e:
        # log dell'errore per debugging; non facciamo rollback della creazione
        print("Errore invio email credenziali:", e)

    token = create_access_token({"sub": str(user.id), "role": user.ruolo.value})
    return Token(access_token=token)

def _send_email_compat(to: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Compatibility wrapper for send_email:
    - tries to call send_email(to=..., subject=..., body=..., html_body=...)
    - if that raises TypeError (signature doesn't accept html_body), falls back to send_email(to, subject, body)
    - logs exceptions instead of raising (we don't want email failures to break the API response)
    """
    try:
        # try keyword style with html_body
        send_email(to=to, subject=subject, body=body, html_body=html_body)
    except TypeError:
        try:
            # fallback to positional/keyword without html
            send_email(to, subject, body)
        except Exception as e:
            print("[EMAIL] errore invio (fallback):", e)
    except Exception as e:
        print("[EMAIL] errore invio:", e)


@router.post("/forgot-password")
def forgot_password(
        background_tasks: BackgroundTasks,
        payload: dict = Body(...),
        db: Session = Depends(get_db),
):
    """
    Endpoint /auth/forgot-password

    Body JSON:
    {
      "email": "user@example.com",            # obbligatorio
      "codice_notarile": 12345                # opzionale (se si vuole restringere ai notai)
    }

    Comportamento:
    - cerca l'utente per email
    - se presente (e se fornito codice_notarile verifica che l'utente sia il notaio con quel codice),
      genera una password temporanea, ne salva l'hash sul db e invia una mail con la password.
    - l'invio viene eseguito in background (BackgroundTasks) per non bloccare la risposta.
    - restituisce 200 anche in caso l'email non sia presente per evitare enumerazione utenti (best practice).
    """

    email = payload.get("email")
    codice_notarile = payload.get("codice_notarile", None)

    if not email:
        raise HTTPException(status_code=400, detail="Email mancante")

    # Trova utente
    user: Optional[User] = db.query(User).filter(User.email == email).first()

    # Se non troviamo l'utente, rispondi comunque 200 per non rivelare l'esistenza dell'email
    if not user:
        # possibile log qui per monitoraggio
        return {"ok": True, "msg": "Se l'email è registrata, riceverai le istruzioni via email."}

    # Se è stato passato codice_notarile, verifichiamo che l'utente sia effettivamente quel notaio
    if codice_notarile is not None:
        try:
            codice_int = int(codice_notarile)
        except Exception:
            # non valido: non rivelare info sensibili
            return {"ok": True, "msg": "Se l'email è registrata, riceverai le istruzioni via email."}

        notaio = db.query(Notaio).filter(Notaio.utente_id == user.id, Notaio.codice_notarile == codice_int).first()
        if not notaio:
            # non corrisponde: non rivelare
            return {"ok": True, "msg": "Se l'email è registrata, riceverai le istruzioni via email."}

    # Genera password temporanea
    temp_pw = secrets.token_urlsafe(10)

    # Salva hash della password temporanea
    try:
        user.password = hash_password(temp_pw)
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        # Log dell'errore e ritorno 500
        raise HTTPException(status_code=500, detail=f"Errore interno salvataggio password: {e}")

    # Prepara contenuto email (plain + html)
    subject = "Recupero password - Il Mio Studio"
    body_text = (
        f"Ciao {user.nome or ''} {user.cognome or ''},\n\n"
        "Hai richiesto il recupero della password.\n\n"
        f"La tua password temporanea è: {temp_pw}\n\n"
        "Accedi e modifica la password il prima possibile.\n\n"
        "Se non hai richiesto questa operazione, contatta lo studio.\n"
    )
    body_html = f"""
    <p>Ciao {user.nome or ''} {user.cognome or ''},</p>
    <p>Hai richiesto il recupero della password.</p>
    <p><strong>La tua password temporanea è:</strong> {temp_pw}</p>
    <p>Accedi e modifica la password il prima possibile.</p>
    <p>Se non hai richiesto questa operazione, contatta lo studio.</p>
    """

    # Invia email in background tramite wrapper compatibile
    background_tasks.add_task(_send_email_compat, user.email, subject, body_text, body_html)

    return {"ok": True, "msg": "Se l'email è registrata, riceverai la password via email."}