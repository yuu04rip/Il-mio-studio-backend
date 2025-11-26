from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import auth, users
from app.api.routes.gestore_studio import router as gestore_studio_router
from app.api.routes.documents import router as documentazione_router
from app.api.routes.backup import router as backup_router
from app.db.session import Base, engine
from app.task.cleanup_services import start_cleanup_background

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

@app.on_event("startup")
def _on_startup():
    # start the background cleanup thread (daily, soft-delete by default)
    start_cleanup_background()
    # you can tune interval_seconds or soft flag if desired:
    # start_cleanup_background(interval_seconds=24*3600, soft=True)
    print("[APP] background cleanup started")

@app.get("/")
def root():
    return {"status": "ok", "app": "Studio Service API"}