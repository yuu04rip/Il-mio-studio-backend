from fastapi import FastAPI
from app.api.routes import auth, users, documents
from app.db.session import Base, engine

# Crea le tabelle in sviluppo (per produzione usa Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Studio Service API", version="0.1.0")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])

@app.get("/")
def root():
    return {"status": "ok", "app": "Studio Service API"}