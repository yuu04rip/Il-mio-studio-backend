from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.services import Servizio
from app.schemas.services import ServizioOut
from app.models.cliente import Cliente
from app.models.enums import TipoServizio

router = APIRouter()

@router.post("/inizializza", response_model=ServizioOut)
def inizializza_servizio(
        cliente_nome: str,
        tipo: TipoServizio,
        codiceCorrente: int,
        codiceServizio: int,
        db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).join(Cliente.utente).filter(Cliente.utente.nome == cliente_nome).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    servizio = Servizio(
        cliente_id=cliente.id,
        tipo=tipo,
        codiceCorrente=codiceCorrente,
        codiceServizio=codiceServizio,
        statoServizio=False
    )
    db.add(servizio)
    db.commit()
    db.refresh(servizio)
    return servizio