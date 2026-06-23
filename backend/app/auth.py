from fastapi import Header, HTTPException

from app.config import settings


def verify_password(x_app_password: str | None = Header(default=None)) -> None:
    """Protezione semplice a password unica condivisa.
    Se APP_PASSWORD non è configurata, nessun controllo (comportamento attuale invariato)."""
    if settings.APP_PASSWORD and x_app_password != settings.APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Password non valida")
