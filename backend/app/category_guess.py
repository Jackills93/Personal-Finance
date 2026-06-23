import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Category

# Stesso spirito di CAT_KEYWORDS/guessCategory in frontend/index.html (import CSV):
# parole chiave nella descrizione -> categoria la cui name contiene una delle sottostringhe
# associate. Coperti solo i topic riconoscibili in modo affidabile da parole chiave;
# categorie più specifiche (Oggetti, Benessere, Spesa regalo, Spese extra, Altro, PAC, ecc.)
# non hanno un set di parole chiave affidabile e restano senza guess automatico.
TOPIC_RULES: list[tuple[list[str], list[str]]] = [
    (
        ["supermercato", "coop", "esselunga", "lidl", "aldi", "conad", "eurospin", "spesa", "alimentari",
         "ristorante", "trattoria", "pizzeria", "bar", "caffè", "caffetteria", "delivery", "deliveroo",
         "just eat", "uber eat"],
        ["alimentari", "cibo"],
    ),
    (
        ["benzina", "carburante", "eni", "agip", "q8", "tamoil", "parking", "parcheggio", "autostrada",
         "telepass", "trenitalia", "italo", "atm", "autobus", "metro", "taxi"],
        ["trasporto", "trasp"],
    ),
    (
        ["enel", "terna", "gas", "acqua", "luce", "bolletta", "utenza", "vodafone", "tim", "wind",
         "fastweb", "internet", "telefono", "affitto", "mutuo", "condominio", "manutenzione", "ikea",
         "leroy", "brico"],
        ["casa"],
    ),
    (
        ["cinema", "teatro", "netflix", "spotify", "amazon prime", "disney", "playstation", "xbox",
         "concerto", "palestra", "sport", "fitness"],
        ["tempo libero", "svago"],
    ),
    (
        ["zara", "h&m", "abbigliamento", "scarpe", "negozio abiti", "vestiti"],
        ["abbigliamento"],
    ),
    (
        ["hotel", "volo", "ryanair", "easyjet", "booking", "airbnb", "treno", "aeroporto", "vacanza"],
        ["viagg"],
    ),
    (
        ["sigarette", "tabaccheria", "tabacco"],
        ["tabacco"],
    ),
]


def guess_category_id(db: Session, description: str) -> uuid.UUID | None:
    text = description.lower()
    for keywords, name_hints in TOPIC_RULES:
        if any(keyword in text for keyword in keywords):
            category = db.query(Category).filter(
                or_(*[Category.name.ilike(f"%{hint}%") for hint in name_hints])
            ).first()
            if category:
                return category.id
    return None
