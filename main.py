import os
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.routes import auth, users, documents
from app.api.routes.dipendente import router as dipendente_notaio_router
from app.api.routes.documents import router as documentazione_router
from app.api.routes.services import router as servizi_router
from app.api.routes.users import router as me_router
from app.db.session import Base, engine
from app.api.routes.services_init import router as servizi_init_router

# Crea le tabelle (sviluppo; per produzione usa Alembic!)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Studio Service API", version="0.1.0")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(dipendente_notaio_router, tags=["dipendente-notaio"])
app.include_router(documentazione_router, prefix="/documentazione", tags=["documentazione"])
app.include_router(servizi_router, tags=["servizi"])
app.include_router(me_router, tags=["me"])
app.include_router(servizi_init_router, tags=["servizi-init"])
@app.get("/")
def root():
    return {"status": "ok", "app": "Studio Service API"}