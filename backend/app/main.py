from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal
from app.routers import accounts, archive, categories, goals, investments, movements, persons, recurring, telegram
from app.routers.settings import apply_to_runtime, _load_db_settings
from app.routers import settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carica impostazioni DB all'avvio per sovrascrivere eventuali env var
    try:
        db = SessionLocal()
        db_cfg = _load_db_settings(db)
        apply_to_runtime(db_cfg)
    except Exception:
        pass
    finally:
        db.close()
    yield


app = FastAPI(title="Bilancio API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # L'autenticazione avviene via header X-App-Password, non via cookie:
    # allow_credentials può restare False (più restrittivo, nessun invio di cookie cross-origin).
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(movements.router)
app.include_router(recurring.router)
app.include_router(telegram.router)
app.include_router(accounts.router)
app.include_router(persons.router)
app.include_router(goals.router)
app.include_router(investments.router)
app.include_router(settings_router.router)
app.include_router(archive.router)


@app.get("/health")
def health():
    return {"status": "ok"}
