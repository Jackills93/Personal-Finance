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


def extract_hashtags(text: str) -> tuple[str, list[str]]:
    """Separa il testo principale dagli hashtag finali.
    Formato: "<importo> <descrizione> #categoria #persona #conto" — gli hashtag
    vanno messi dopo la descrizione, in quest'ordine, tutti facoltativi.
    """
    parts = text.split("#")
    main_text = parts[0]
    tags = [p.strip() for p in parts[1:] if p.strip()]
    return main_text, tags


def parse_expense_message(text: str) -> tuple[float, str] | None:
    match = AMOUNT_RE.search(text)
    if not match:
        return None
    amount = float(match.group(0).replace(",", "."))
    description = (text[: match.start()] + text[match.end() :]).strip()
    return amount, description or "Spesa da Telegram"


def find_category_by_name(db: Session, name: str) -> Category | None:
    return (
        db.query(Category).filter(Category.name.ilike(name)).first()
        or db.query(Category).filter(Category.name.ilike(f"%{name}%")).first()
    )


@router.post("/webhook")
def telegram_webhook(payload: dict = Body(...), db: Session = Depends(get_db)):
    message = payload.get("message")
    if not message or "text" not in message:
        return {"ok": True}

    chat_id = str(message.get("chat", {}).get("id", ""))
    if not settings.TELEGRAM_CHAT_ID or chat_id != settings.TELEGRAM_CHAT_ID:
        logger.warning("Messaggio Telegram da chat non autorizzata: %s", chat_id)
        return {"ok": True}

    main_text, tags = extract_hashtags(message["text"])
    parsed = parse_expense_message(main_text)
    if parsed is None:
        send_telegram_message(
            'Non ho capito l\'importo. Scrivi ad esempio: "25.50 Spesa supermercato #Alimentari #Pietro #Conto Principale" '
            "(categoria/persona/conto sono facoltativi)."
        )
        return {"ok": True}

    amount, description = parsed
    category_name = tags[0] if len(tags) > 0 else None
    person_name = tags[1] if len(tags) > 1 else None
    account_name = tags[2] if len(tags) > 2 else None

    category = find_category_by_name(db, category_name) if category_name else None
    category_id = category.id if category else guess_category_id(db, description)

    movement = create_movement_and_notify(
        db,
        MovementCreate(
            type="expense",
            description=description,
            amount=amount,
            date=date.today(),
            category_id=category_id,
            person_name=person_name,
            account_name=account_name,
        ),
    )

    details = []
    if category_id is not None:
        cat = category or db.get(Category, category_id)
        if cat:
            details.append(f"categoria: {cat.name}")
    if person_name:
        details.append(f"persona: {person_name}")
    if account_name:
        details.append(f"conto: {account_name}")
    suffix = f" ({', '.join(details)})" if details else ""

    send_telegram_message(f"✅ Registrato: {movement.amount:.2f}€ — {movement.description}{suffix}")
    return {"ok": True}
