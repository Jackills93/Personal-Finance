import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _all_chat_ids() -> list[str]:
    ids = []
    if settings.TELEGRAM_CHAT_ID:
        ids.append(settings.TELEGRAM_CHAT_ID)
    if settings.TELEGRAM_CHAT_ID_GRETA:
        ids.append(settings.TELEGRAM_CHAT_ID_GRETA)
    return ids


def send_telegram_message(text: str, chat_id: str | None = None) -> None:
    """Invia un messaggio Telegram.
    Se chat_id è specificato manda solo a quell'utente,
    altrimenti fa broadcast a tutti i chat_id configurati.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram non configurato: messaggio non inviato (%s)", text)
        return
    targets = [chat_id] if chat_id else _all_chat_ids()
    if not targets:
        logger.warning("Nessun chat_id configurato: messaggio non inviato (%s)", text)
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    for cid in targets:
        try:
            response = httpx.post(url, json={"chat_id": cid, "text": text}, timeout=10)
            response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("Invio messaggio Telegram fallito (chat_id=%s)", cid)
