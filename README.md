# Bilancio

App di gestione finanze personali. Fase attuale: categorie, movimenti e spese ricorrenti vivono su un backend FastAPI + Supabase Postgres, con bot Telegram per loggare spese e notifiche di superamento limite mensile; conti, obiettivi, persone e investimenti restano (per ora) in `localStorage` nel frontend, in attesa delle rispettive API.

```
Dashboard_finance/
├── bilancio.html       # prototipo originale (localStorage), lasciato com'è come riferimento
├── backend/             # FastAPI
├── supabase/schema.sql  # DDL completo da eseguire su Supabase
└── frontend/            # index.html (migrato) + js/api.js
```

## 1. Creare il progetto Supabase (da zero)

1. Vai su [supabase.com](https://supabase.com), crea un account e un nuovo progetto (free tier — scegli una regione vicina, es. `eu-central-1`).
2. Aspetta che il progetto finisca il provisioning (1-2 minuti).
3. Vai su **SQL Editor** → **New query**, incolla tutto il contenuto di [`supabase/schema.sql`](supabase/schema.sql) ed esegui (▶ Run). Questo crea tutte le tabelle (`categories`, `movements`, `accounts`, `persons`, `goals`, `investments`, `recurring_expenses`).
4. Vai su **Settings → Database → Connection string**, scheda **Connection pooling** (modalità *Transaction*, porta `6543`) — è la stringa compatibile con Render free tier. Copiala e sostituisci `[YOUR-PASSWORD]` con la password del database (quella scelta alla creazione del progetto, o resettabile dalla stessa pagina). Il backend usa il driver `psycopg` (v3): cambia il prefisso della stringa da `postgresql://` a `postgresql+psycopg://` (vedi `backend/.env.example`).

## 2. Backend — avvio in locale

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # poi apri .env e incolla la tua DATABASE_URL
uvicorn app.main:app --reload
```

- Swagger interattivo: http://localhost:8000/docs
- Health check: http://localhost:8000/health

`CORS_ORIGINS` in `.env` deve includere l'origine da cui apri `frontend/index.html` (es. `http://localhost:5500` se usi un live server, o `http://127.0.0.1:5500`).

## 3. Frontend — avvio in locale

`frontend/index.html` è un file statico: aprilo con un qualsiasi live server (es. estensione "Live Server" di VS Code, o `npx serve frontend`). Verifica che `API_BASE_URL` in `frontend/js/api.js` punti al backend locale (`http://localhost:8000` di default).

Apri la pagina: Dashboard, Movimenti e Categorie devono mostrare i dati provenienti dal backend (inizialmente vuoti — crea una categoria e un movimento dall'interfaccia per verificare). Conti, Obiettivi, Persone, Investimenti continuano a funzionare come nel prototipo originale (dati in `localStorage`).

## 4. Deploy backend su Render (free tier)

1. Pusha questa cartella su un repo Git (GitHub/GitLab).
2. Su [render.com](https://render.com), **New → Web Service**, collega il repo. Render rileva `backend/render.yaml` (oppure configuralo a mano: root directory `backend`, build command `pip install -r requirements.txt`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
3. Imposta le environment variable `DATABASE_URL` e `CORS_ORIGINS` (quest'ultima con l'URL del frontend su Vercel, vedi sotto) nel pannello Render.
4. Nota: il piano free di Render "dorme" dopo ~15 minuti di inattività — la prima richiesta dopo lo sleep impiega qualche secondo extra. Accettabile per uso personale.

## 5. Deploy frontend su Vercel

1. Su [vercel.com](https://vercel.com), **New Project**, importa il repo, imposta **Root Directory** = `frontend`.
2. Prima del deploy, aggiorna `API_BASE_URL` in `frontend/js/api.js` con l'URL pubblico del backend su Render (es. `https://bilancio-api.onrender.com`).
3. Deploy. Poi torna su Render e aggiorna `CORS_ORIGINS` con l'URL Vercel ottenuto (es. `https://bilancio.vercel.app`).

## 6. Bot Telegram — logging spese e notifiche limite

Il bot serve a due cose: (a) registrare una spesa scrivendo un messaggio in chat (es. `"25.50 Spesa supermercato"`), (b) avvisarti quando una categoria supera il limite mensile. Entrambe usano lo stesso bot/token, niente servizi aggiuntivi.

**Importante:** Telegram richiede un URL pubblico HTTPS per il webhook — non funziona contro `localhost`. Questi passi (in particolare l'ultimo) vanno fatti **dopo** il deploy su Render (punto 4); se vuoi testare prima, serve un tunnel come [ngrok](https://ngrok.com).

1. Su Telegram, apri una chat con **@BotFather**, manda `/newbot`, scegli nome e username. Ottieni un **token** tipo `123456789:AAExxxxxxx...`.
2. Trova il tuo **chat ID**: scrivi un qualsiasi messaggio al bot appena creato, poi apri nel browser `https://api.telegram.org/bot<TOKEN>/getUpdates` — nel JSON di risposta cerca `"chat":{"id":NNNNNNN...}`. Alternativa più comoda: scrivi a [@userinfobot](https://t.me/userinfobot), ti risponde subito con il tuo id.
3. Su Render, vai sul servizio backend → **Environment**, aggiungi `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` con i valori ottenuti sopra. Salva (Render fa il redeploy automatico).
4. Registra il webhook (una tantum, dopo che il backend è online su Render):
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<tuo-backend>.onrender.com/telegram/webhook"
   ```
5. Test: scrivi al bot `"12.50 Caffè"` — dovrebbe risponderti con una conferma e il movimento deve apparire nell'app. Se una categoria supera il limite mensile (sia da un movimento creato nell'app, sia da Telegram, sia da una ricorrenza generata in automatico), il bot manda un messaggio di avviso.

Senza queste due variabili configurate, il resto dell'app funziona comunque normalmente: webhook e notifiche restano no-op silenziosi.

## Prossimi step (non ancora fatti)

- API CRUD per `accounts`, `persons`, `goals`, `investments` + migrazione delle colonne FK reali su `movements`/`recurring_expenses` (oggi `account_name`/`person_name`/ecc. sono testo denormalizzato, vedi commenti in `supabase/schema.sql`).
- Supabase Auth + Row Level Security, quando si passerà a multi-utente (oggi l'app è single-user, nessuna autenticazione).
