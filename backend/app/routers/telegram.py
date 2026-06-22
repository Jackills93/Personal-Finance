import logging
import re
from datetime import date

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.category_guess import guess_category_id
from app.config import settings
from app.database import get_db
from app.models import Category
from app.schemas.movement import MovementCreate
from app.services import create_movement_and_notify
from app.telegram_client import send_telegram_message

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = logging.getLogger(__name__)

AMOUNT_RE = re.compile(r"\d+(?:[.,]\d+)?")


def parse_expense_message(text: str) -> tuple[float, str] | None:
    match = AMOUNT_RE.search(text)
    if not match:
        return None
    amount = float(match.group(0).replace(",", "."))
    description = (text[: match.start()] + text[match.end() :]).strip()
    return amount, description or "Spesa da Telegram"


@router.post("/webhook")
def telegram_webhook(payload: dict = Body(...), db: Session = Depends(get_db)):
    message = payload.get("message")
    if not message or "text" not in message:
        return {"ok": True}

    chat_id = str(message.get("chat", {}).get("id", ""))
    if not settings.TELEGRAM_CHAT_ID or chat_id != settings.TELEGRAM_CHAT_ID:
        logger.warning("Messaggio Telegram da chat non autorizzata: %s", chat_id)
        return {"ok": True}

    parsed = parse_expense_message(message["text"])
    if parsed is None:
        send_telegram_message('Non ho capito l\'importo. Scrivi ad esempio: "25.50 Spesa supermercato"')
        return {"ok": True}

    amount, description = parsed
    category_id = guess_category_id(db, description)

    movement = create_movement_and_notify(
        db,
        MovementCreate(
            type="expense",
            description=description,
            amount=amount,
            date=date.today(),
            category_id=category_id,
        ),
    )

    category_label = ""
    if category_id is not None:
        category = db.get(Category, category_id)
        if category:
            category_label = f" (categoria: {category.name})"

    send_telegram_message(f"✅ Registrato: {movement.amount:.2f}€ — {movement.description}{category_label}")
    return {"ok": True}
