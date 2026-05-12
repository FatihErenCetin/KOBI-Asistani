# Akıllı KOBİ/Kooperatif Asistanı

> Telegram + Web Panel üzerinden müşteri iletişimini ve sipariş takibini otomatikleştiren AI ajan sistemi.

## Ne Yapar

- **Müşteri Telegram'dan** doğal dilde sipariş durumu sorar, ürün/fiyat öğrenir, inline buton ile tek tıkla sipariş açar.
- **İşletme yöneticisi web panelden** günün özetini görür, doğal dilde veri sorgular.

## Demo

5 senaryo: Onboarding, sipariş durumu, ürün sorgu + inline buton ile sipariş, geçmiş, panel dashboard, panel NL sorgu.

**Demo gününe hazırlık adımları:** [docs/demo-setup.md](docs/demo-setup.md) (Gemini key, BotFather, ngrok, webhook, test verisi).

**UI/UX tasarım brief'i (Claude Design / tasarımcıya verilecek):** [docs/ui-ux-brief.md](docs/ui-ux-brief.md).

**P0 bileşen redesign prompt'ları (kopyala-yapıştır hazır):**
- [docs/prompts/summarycards.md](docs/prompts/summarycards.md) — Dashboard özet kartları
- [docs/prompts/shipment-timeline.md](docs/prompts/shipment-timeline.md) — Sipariş detay kargo timeline
- [docs/prompts/chat-empty-state.md](docs/prompts/chat-empty-state.md) — AI Asistan empty state + balon iyileştirme

## Mimari

İki ajan (Customer / Panel) aynı **tool katmanını** farklı persona ve izinlerle kullanır:

- **Customer Agent** — sınırlı tool seti, yalnız çağıran müşterinin verisi
- **Panel Agent** — tüm tool'lara erişim, yönetici context'inde çalışır
- **Tool Layer** — plain async Python fonksiyonları, `AgentContext` ile permission scope
- **Gemini Function Calling Loop** — `google-genai` SDK, max 5 iterasyon

```
Telegram Bot --> /webhooks/telegram --+
                                       +-> Coordinator -> Customer Agent --+
Web Panel ----> /panel/chat --------+                                       +-> Tool Layer
                                       +-> Coordinator -> Panel Agent ----+         |
                                                                                     v
                                                              SQLAlchemy (Postgres) + Mock Cargo + Telegram API
```

## Hızlı Başlangıç

### Backend

```bash
# 1. Postgres'i ayaga kaldir
docker compose up -d postgres

# 2. Test DB'sini olustur (bir defalik)
docker compose exec -T postgres psql -U kobi -d kobi_db -c "CREATE DATABASE kobi_test_db;"

# 3. Python sanal ortami (Python 3.11+)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 4. Env hazirla
cp .env.example .env
# .env'yi doldur: GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, ADMIN_TOKEN

# 5. Migration + seed
alembic upgrade head
python -m app.db.seed --demo-fixtures

# 6. Calistir
uvicorn app.main:app --reload --port 8000
```

Telegram webhook için ayrı terminalde:

```bash
ngrok http 8000
bash scripts/set_telegram_webhook.sh https://xxx.ngrok-free.app
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
# NEXT_PUBLIC_ADMIN_TOKEN'i backend .env ile esleyin
npm install
npm run dev
# http://localhost:3000
```

### Hızlı test

1. Telegram'da botu bul, `/start` yaz
2. Telefon numarasını paylaş (seed'deki müşterinin numarasına eşitlemek için: `docker compose exec -T postgres psql -U kobi -d kobi_db -c "UPDATE customers SET phone='<numaran>' WHERE telegram_user_id=99999;"`)
3. "128 numaralı siparişim nerede?" → bot cevaplar
4. http://localhost:3000 → dashboard

## Kullanılan AI Yaklaşımı

- **LLM:** Google Gemini (`gemini-2.0-flash-exp`) — `google-genai` SDK
- **Mimari:** Agent-based, function calling
- **Persona ayrımı:** Müşteri Ajanı + Panel Ajanı, aynı tool layer
- **Sesli mesaj:** Altyapı hazır (`app/core/stt.py`), default kapalı; aktivasyon `.env` ile

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Backend | FastAPI, SQLAlchemy 2.x async, Pydantic v2 |
| LLM | Google Gemini SDK (`google-genai`) |
| DB | PostgreSQL 16 (Docker Compose) — `asyncpg` async + `psycopg[binary]` sync |
| Migration | Alembic |
| Scheduler | APScheduler |
| Frontend | Next.js 14, TypeScript, Tailwind, Recharts |
| Telegram | Bot API üzerinden raw httpx |

## Klasör Yapısı

```
app/                  # FastAPI backend
  agents/             # Customer + Panel agents
  tools/              # Function calling tool implementations
  core/               # config, logging, llm, identity, stt
  db/                 # models, crud, session, seed
  integrations/       # telegram_client, cargo_mock
  api/v1/             # REST endpoints
  schemas/            # Pydantic request/response models
  jobs/               # APScheduler jobs
frontend/             # Next.js panel
tests/                # pytest suite
scripts/              # helper scripts (set_telegram_webhook, reset_db)
```

## Test

```bash
pytest -v
```

## Notlar

- **Postgres portu 5434:** Yerel/başka container'larla çakışmayı önlemek için Docker Compose Postgres'i 5434'e map'liyor. `.env`'de bu kullanılıyor.
- **Telegram bot komutları (manuel):** BotFather'a `/setcommands` ile:
  ```
  start - Hosgeldin mesaji ve hesap eslemesi
  siparislerim - Son siparislerimi listele
  yardim - Yardim menusu
  ```

## Roadmap

- Sesli mesaj aktivasyonu (Whisper veya Gemini Audio)
- Proaktif şikayet riski tespiti
- Sabah brifingi push bildirimi
- Tedarikçi mail otomasyonu
- Çoklu işletme / multi-tenancy
- Ödeme entegrasyonu

## Lisans

MIT
