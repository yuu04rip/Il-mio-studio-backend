from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.services import Servizio
from app.schemas.services import ServizioOut
from app.models.cliente import Cliente
from app.models.enums import TipoServizio
from datetime import datetime
from app.models.user import User

router = APIRouter()

@router.post("/inizializza", response_model=ServizioOut)
def inizializza_servizio(

        cliente_nome: str = Form(...),
        tipo: TipoServizio = Form(...),
        codiceCorrente: int = Form(...),
        codiceServizio: int = Form(...),
        db: Session = Depends(get_db),
):
    print("DEBUG IMPORT: router servizi_init caricato")
    print("="*40)
    print(f"DEBUG ENDPOINT: Ricevuto cliente_nome={cliente_nome}, tipo={tipo}, codiceCorrente={codiceCorrente}, codiceServizio={codiceServizio}")

    print("DEBUG ENDPOINT: Tutti gli utenti nel DB:")
    for u in db.query(User).all():
        print(f"  User.id={u.id}, nome={u.nome}, email={u.email}, cognome={u.cognome}, ruolo={u.ruolo}")

    print("DEBUG ENDPOINT: Tutti i clienti nel DB:")
    for cli in db.query(Cliente).all():
        print(f"  Cliente.id={cli.id}, utente_id={cli.utente_id}, utente={cli.utente}")

    print("DEBUG ENDPOINT: Provo la query cliente tramite nome...")
    cliente = db.query(Cliente).join(Cliente.utente).filter(User.nome == cliente_nome).first()
    print(f"DEBUG ENDPOINT: Query cliente result={cliente}")

    if not cliente:
        utenti_nomi = [u.nome for u in db.query(User).all()]
        print(f"DEBUG ENDPOINT: Nessun cliente trovato con nome={cliente_nome}. Nomi disponibili: {utenti_nomi}")
        print("="*40)
        raise HTTPException(status_code=404, detail="Cliente non trovato")

    now = datetime.now()
    servizio = Servizio(
        cliente_id=cliente.id,
        tipo=tipo,
        codiceCorrente=codiceCorrente,
        codiceServizio=codiceServizio,
        statoServizio=False,
        dataConsegna=now,
        dataRichiesta=now
    )
    db.add(servizio)
    db.commit()
    db.refresh(servizio)
    print(f"DEBUG ENDPOINT: Servizio creato con id={servizio.id}, tipo={servizio.tipo}, cliente_id={servizio.cliente_id}")

    print("DEBUG ENDPOINT FINALE: Tutti i servizi nel DB:")
    for s in db.query(Servizio).all():
        print(f"  Servizio.id={s.id}, cliente_id={s.cliente_id}, tipo={s.tipo}, statoServizio={s.statoServizio}")

    print("="*40)
    return servizio