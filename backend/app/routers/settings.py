import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import verify_password
from app.config import settings
from app.database import get_db
from app.models import AppSetting

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(verify_password)])
logger = logging.getLogger(__name__)

ALLOWED_KEYS = {
    "telegram_bot_token",
    "telegram_chat_id_1",
    "telegram_chat_id_1_name",
    "telegram_chat_id_2",
    "telegram_chat_id_2_name",
    "app_name",
}


def _load_db_settings(db: Session) -> dict[str, str]:
    rows = db.query(AppSetting).all()
    return {r.key: r.value or "" for r in rows}


def apply_to_runtime(data: dict[str, str]) -> None:
    """Aggiorna l'oggetto settings in-memory con i valori dal DB."""
    if "telegram_bot_token" in data:
        settings.TELEGRAM_BOT_TOKEN = data["telegram_bot_token"] or None
    if "telegram_chat_id_1" in data:
        settings.TELEGRAM_CHAT_ID = data["telegram_chat_id_1"] or None
    if "telegram_chat_id_1_name" in data and data["telegram_chat_id_1_name"]:
        settings.TELEGRAM_CHAT_ID_NAME = data["telegram_chat_id_1_name"]
    if "telegram_chat_id_2" in data:
        settings.TELEGRAM_CHAT_ID_GRETA = data["telegram_chat_id_2"] or None
    if "telegram_chat_id_2_name" in data and data["telegram_chat_id_2_name"]:
        settings.TELEGRAM_CHAT_ID_GRETA_NAME = data["telegram_chat_id_2_name"]


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    return _load_db_settings(db)


@router.patch("")
def update_settings(data: dict, db: Session = Depends(get_db)):
    unknown = set(data.keys()) - ALLOWED_KEYS
    if unknown:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Chiavi non consentite: {unknown}")

    for key, value in data.items():
        row = db.get(AppSetting, key)
        if row:
            row.value = str(value) if value else None
        else:
            db.add(AppSetting(key=key, value=str(value) if value else None))
    db.commit()

    apply_to_runtime(data)
    return {"ok": True}
