import secrets

from fastapi import Header, HTTPException

from app.config import settings


def verify_password(x_app_password: str | None = Header(default=None)) -> None:
    """Protezione semplice a password unica condivisa.
    Se APP_PASSWORD non è configurata, nessun controllo (comportamento attuale invariato).
    Il confronto è a tempo costante per evitare timing attack sulla password."""
    if not settings.APP_PASSWORD:
        return
    if not x_app_password or not secrets.compare_digest(x_app_password, settings.APP_PASSWORD):
        raise HTTPException(status_code=401, detail="Password non valida")
