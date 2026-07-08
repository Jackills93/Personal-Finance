# Personal Finance Dashboard

App di gestione finanze personali con backend API, bot Telegram e analisi del portafoglio investimenti.

[![Deploy on Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Jackills93/Personal-Finance)
&nbsp;&nbsp;
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/Jackills93/Personal-Finance)

> **Render** è gratuito (cold start ~30s dopo 15 min di inattività). **Railway** offre 30 giorni di prova poi è a pagamento (~$5/mese).

---

## Funzionalità

- **Dashboard** — saldo totale, entrate/uscite del mese, grafico spese per categoria
- **Movimenti** — CRUD completo con filtri, vista lista e vista mensile, export CSV
- **Spese ricorrenti** — mutuo, abbonamenti e rate generate automaticamente ogni mese
- **Obiettivi di risparmio** — traccia l'avanzamento verso traguardi finanziari
- **Investimenti** — portafoglio con P&L, grafici e analisi del profilo di rischio
- **Bot Telegram** — registra spese con un messaggio (`"25 Spesa supermercato #Alimentari"`)
- **Notifiche limite** — avviso Telegram quando una categoria supera il budget mensile
- **Wizard onboarding** — configurazione guidata al primo accesso (conti, categorie, persone)
- **Multi-persona** — supporto per più utenti (es. coppia) con filtro per persona
- **Tema scuro** — interfaccia dark con supporto valute e lingua configurabili

## Stack

| Layer | Tecnologia |
|---|---|
| Backend | FastAPI + SQLAlchemy (Python) |
| Database | PostgreSQL (Supabase free) |
| Frontend | HTML/CSS/JS puro (nessun framework) |
| Backend hosting | Render (free) o Railway |
| Frontend hosting | Vercel (free) |
| Notifiche | Telegram Bot API |

---

## Deploy in produzione

### 1. Database — Supabase (gratuito)

1. Crea un progetto su [supabase.com](https://supabase.com)
2. Vai su **SQL Editor** → incolla il contenuto di [`supabase/schema.sql`](supabase/schema.sql) → esegui
3. Vai su **Settings → Database → Connection string → Connection pooling**
   - Modalità **Transaction**, porta **6543**
   - Copia la stringa e cambia il prefisso da `postgresql://` a `postgresql+psycopg://`

### 2. Backend su Render (gratuito)

1. Clicca il pulsante **Deploy on Render** in cima a questo file
2. Render rileva automaticamente il file `backend/render.yaml`
3. Aggiungi le variabili d'ambiente nella dashboard Render:

| Variabile | Obbligatoria | Descrizione |
|---|---|---|
| `DATABASE_URL` | ✓ | Stringa connessione Supabase (pooler Transaction, porta 6543) |
| `CORS_ORIGINS` | ✓ | URL del frontend Vercel (es. `https://tuo-progetto.vercel.app`) |
| `APP_PASSWORD` | ✓ | Password a piacere per proteggere l'app |
| `TELEGRAM_BOT_TOKEN` | — | Token del bot da @BotFather |
| `TELEGRAM_CHAT_ID` | — | Chat ID numerico dell'utente principale |
| `TELEGRAM_CHAT_ID_NAME` | — | Nome dell'utente (usa il first_name Telegram se vuoto) |
| `TELEGRAM_CHAT_ID_GRETA` | — | Chat ID secondo utente (opzionale) |
| `TELEGRAM_CHAT_ID_GRETA_NAME` | — | Nome secondo utente (opzionale) |

> **Cold start**: il piano free di Render mette il backend in sleep dopo 15 minuti di inattività. La prima apertura dell'app mostrerà uno schermo di caricamento per ~30 secondi. Dopo, tutto funziona normalmente.

### 3. Frontend su Vercel (gratuito)

1. Su [vercel.com](https://vercel.com) → **New Project** → importa questo repo
2. Lascia **Root Directory vuoto** (il `vercel.json` alla root gestisce tutto)
3. Aggiungi le variabili d'ambiente:
   - `API_BASE_URL` = URL del backend Render (es. `https://bilancio-api.onrender.com`)
   - `APP_PASSWORD` = stessa password impostata su Render
4. Clicca **Deploy**
5. Copia l'URL Vercel ottenuto → torna su Render e aggiorna `CORS_ORIGINS`

### 4. Bot Telegram (opzionale)

Il bot permette di registrare spese via messaggio e ricevere notifiche quando si supera un budget mensile. Richiede un URL pubblico HTTPS — funziona solo dopo il deploy.

1. Crea il bot con **@BotFather** → `/newbot` → ottieni il token
2. Trova il tuo chat ID: scrivi al bot, poi apri `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Genera un secret per il webhook (es. `openssl rand -hex 16`)
4. Imposta su Render: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` e `TELEGRAM_WEBHOOK_SECRET`
5. Registra il webhook (una tantum, dopo il deploy) passando **lo stesso** secret:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<tuo-backend>.onrender.com/telegram/webhook&secret_token=<TELEGRAM_WEBHOOK_SECRET>"
   ```
   Così l'endpoint accetta solo le chiamate autentiche di Telegram (che inviano il secret nell'header `X-Telegram-Bot-Api-Secret-Token`) e ignora eventuali richieste di sconosciuti che conoscono l'URL.

**Sintassi messaggi:**
```
25.50 Spesa supermercato              → uscita, categoria auto-rilevata
25.50 Spesa supermercato #Alimentari  → categoria esplicita
25.50 Spesa supermercato #Alimentari #Revolut  → categoria + conto
+1200 Stipendio #Entrate              → entrata (+ davanti all'importo)
```
La persona viene rilevata automaticamente dal chat ID — non serve indicarla.

---

## Sviluppo locale

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
cp .env.example .env         # compila DATABASE_URL e le altre variabili
uvicorn app.main:app --reload

# Swagger: http://localhost:8000/docs
```

```bash
# Frontend
# Apri frontend/index.html con un live server (es. estensione VS Code "Live Server")
# oppure:
npx serve frontend
```

In `.env` imposta `CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500`.

---

## Sicurezza

L'app usa una password condivisa (`APP_PASSWORD`) che protegge tutti gli endpoint dati tramite header `X-App-Password`. Il frontend mostra una schermata di login al primo accesso e salva la password nel `localStorage` del browser.

- `/health` e il webhook Telegram sono pubblici (non richiedono password)
- Il webhook è protetto dal controllo del `TELEGRAM_CHAT_ID` — solo i chat ID configurati possono scrivere dati
- Non condividere l'URL del backend — usa sempre l'URL Vercel del frontend

> Per uso multi-utente con autenticazione per-account, servirebbe integrare Supabase Auth con Row Level Security — non è incluso in questa versione.
