from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import categories, movements, recurring, telegram

app = FastAPI(title="Bilancio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categories.router)
app.include_router(movements.router)
app.include_router(recurring.router)
app.include_router(telegram.router)


@app.get("/health")
def health():
    return {"status": "ok"}
