from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.cliente import Cliente
from app.models.user import User
from app.schemas.cliente import ClienteOut

router = APIRouter()

@router.get("/clienti/nome/{nome}", response_model=ClienteOut)
def cerca_cliente_per_nome(nome: str, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).join(Cliente.utente).filter(User.nome == nome).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente non trovato")
    return cliente