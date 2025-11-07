
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import auth, users
from app.api.routes.gestore_studio import router as gestore_studio_router
from app.api.routes.documents import router as documentazione_router
from app.api.routes.backup import router as backup_router
from app.db.session import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Studio Service API", version="0.1.0")

# Routers principali
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(gestore_studio_router, prefix="/studio", tags=["gestione-studio"])
app.include_router(documentazione_router, prefix="/documentazione", tags=["documentazione-download"])
app.include_router(backup_router, prefix="/backup", tags=["backup"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080", "http://localhost:3000", "http://localhost:8000"],  # metti gli origin reali del frontend
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, OPTIONS, ...
    allow_headers=["*"],    # Authorization, Content-Type, ...
)
@app.get("/")
def root():
    return {"status": "ok", "app": "Studio Service API"}