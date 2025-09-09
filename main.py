import os
from fastapi import FastAPI
from app.api.routes import auth, users
from app.api.routes.gestore_studio import router as gestore_studio_router
from app.api.routes.documents import router as documentazione_router  # solo per /documentazione/download/{doc_id}
from app.api.routes.backup import router as backup_router  # <-- AGGIUNTO: router per backup/archiviazione
from app.db.session import Base, engine

# Crea le tabelle (sviluppo; per produzione usa Alembic!)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Studio Service API", version="0.1.0")

# Routers principali
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(gestore_studio_router, prefix="/studio", tags=["gestione-studio"])
app.include_router(documentazione_router, prefix="/documentazione", tags=["documentazione-download"])
app.include_router(backup_router, prefix="/backup", tags=["backup"])  # <-- AGGIUNTO: router per backup/archiviazione

@app.get("/")
def root():
    return {"status": "ok", "app": "Studio Service API"}