import uuid

from sqlalchemy.orm import Session

from app.models import Category

# Stesso spirito di CAT_KEYWORDS/guessCategory in frontend/index.html (import CSV):
# parole chiave nella descrizione -> "topic" -> categoria la cui name contiene quel topic.
# A differenza della versione JS (che puntava a id fissi tipo cat_cibo), qui le categorie
# sono create liberamente dall'utente: il match è quindi per sottostringa sul nome.
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "cibo": [
        "supermercato", "coop", "esselunga", "lidl", "aldi", "conad", "eurospin", "spesa", "alimentari",
        "ristorante", "trattoria", "pizzeria", "bar", "caffè", "caffetteria", "delivery", "deliveroo",
        "just eat", "uber eat",
    ],
    "trasp": [
        "benzina", "carburante", "eni", "agip", "q8", "tamoil", "parking", "parcheggio", "autostrada",
        "telepass", "trenitalia", "italo", "atm", "autobus", "metro", "taxi",
    ],
    "casa": [
        "enel", "terna", "gas", "acqua", "luce", "bolletta", "utenza", "vodafone", "tim", "wind",
        "fastweb", "internet", "telefono", "affitto", "mutuo", "condominio", "manutenzione", "ikea",
        "leroy", "brico",
    ],
    "svago": [
        "cinema", "teatro", "netflix", "spotify", "amazon prime", "disney", "playstation", "xbox",
        "svago", "concerto", "palestra", "sport", "fitness",
    ],
}


def guess_category_id(db: Session, description: str) -> uuid.UUID | None:
    text = description.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            category = db.query(Category).filter(Category.name.ilike(f"%{topic}%")).first()
            if category:
                return category.id
    return None
