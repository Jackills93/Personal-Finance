import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def send_telegram_message(text: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram non configurato: messaggio non inviato (%s)", text)
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = httpx.post(url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text}, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError:
        logger.exception("Invio messaggio Telegram fallito")
