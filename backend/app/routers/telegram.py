import logging
import re
from datetime import date

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.category_guess import guess_category_id
from app.config import settings
from app.database import get_db
from app.models import Category
from app.schemas.movement import MovementCreate, MovementType
from app.services import create_movement_and_notify
from app.telegram_client import send_telegram_message

router = APIRouter(prefix="/telegram", tags=["telegram"])
logger = logging.getLogger(__name__)

AMOUNT_RE = re.compile(r"([+-]?)\s*(\d+(?:[.,]\d+)?)")


def extract_hashtags(text: str) -> tuple[str, list[str]]:
    """Separa il testo principale dagli hashtag finali.
    Formato: "<importo> <descrizione> #categoria #persona #conto" — gli hashtag
    vanno messi dopo la descrizione, in quest'ordine, tutti facoltativi.
    """
    parts = text.split("#")
    main_text = parts[0]
    tags = [p.strip() for p in parts[1:] if p.strip()]
    return main_text, tags


def parse_message(text: str) -> tuple[MovementType, float, str] | None:
    match = AMOUNT_RE.search(text)
    if not match:
        return None
    sign, digits = match.groups()
    amount = float(digits.replace(",", "."))
    movement_type: MovementType = "income" if sign == "+" else "expense"
    description = (text[: match.start()] + text[match.end() :]).strip()
    default_desc = "Entrata da Telegram" if movement_type == "income" else "Spesa da Telegram"
    return movement_type, amount, description or default_desc


def find_category_by_name(db: Session, name: str) -> Category | None:
    return (
        db.query(Category).filter(Category.name.ilike(name)).first()
        or db.query(Category).filter(Category.name.ilike(f"%{name}%")).first()
    )


def _authorized_chat_map() -> dict[str, str]:
    """Restituisce {chat_id: nome_persona} per tutti gli ID configurati."""
    mapping: dict[str, str] = {}
    if settings.TELEGRAM_CHAT_ID:
        mapping[settings.TELEGRAM_CHAT_ID] = settings.TELEGRAM_CHAT_ID_NAME
    if settings.TELEGRAM_CHAT_ID_GRETA:
        mapping[settings.TELEGRAM_CHAT_ID_GRETA] = settings.TELEGRAM_CHAT_ID_GRETA_NAME
    return mapping


@router.post("/webhook")
def telegram_webhook(payload: dict = Body(...), db: Session = Depends(get_db)):
    message = payload.get("message")
    if not message or "text" not in message:
        return {"ok": True}

    chat_id = str(message.get("chat", {}).get("id", ""))
    chat_map = _authorized_chat_map()

    if not chat_map or chat_id not in chat_map:
        logger.warning("Messaggio Telegram da chat non autorizzata: %s", chat_id)
        return {"ok": True}

    # Persona dedotta dall'account che ha scritto — non serve #hashtag
    auto_person = chat_map[chat_id]

    main_text, tags = extract_hashtags(message["text"])
    parsed = parse_message(main_text)
    if parsed is None:
        send_telegram_message(
            'Non ho capito l\'importo. Scrivi ad esempio: "25.50 Spesa supermercato #Alimentari #Conto Principale" '
            'per una uscita, o "+1200 Stipendio #Entrate #Conto Principale" per una entrata '
            "(categoria e conto sono facoltativi, la persona viene rilevata automaticamente).",
            chat_id=chat_id,
        )
        return {"ok": True}

    movement_type, amount, description = parsed
    # Sintassi: "importo descrizione #categoria #conto"
    # La persona è automatica dal chat_id, non serve più come hashtag
    person_name = auto_person
    category_name = tags[0] if len(tags) > 0 else None
    account_name = tags[1] if len(tags) > 1 else None

    category = find_category_by_name(db, category_name) if category_name else None
    if category:
        category_id = category.id
    elif movement_type == "expense":
        category_id = guess_category_id(db, description)
    else:
        category_id = None

    movement = create_movement_and_notify(
        db,
        MovementCreate(
            type=movement_type,
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

    icon = "💰" if movement_type == "income" else "✅"
    send_telegram_message(
        f"{icon} Registrato: {movement.amount:.2f}€ — {movement.description}{suffix}",
        chat_id=chat_id,
    )
    return {"ok": True}
