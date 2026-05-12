# Demo Öncesi Hazırlık Kılavuzu

> Bu kılavuz, kodlama bittikten sonra demo gününe kadar yapılması gereken **dış servis kayıtları** ve **canlı bağlantı kurulumlarını** uçtan uca anlatır.

**Toplam süre:** İlk seferinde 25-35 dakika. Sonraki çalıştırmalarda 5 dakika (sadece ngrok + webhook).

**Önkoşul:** Backend ve frontend kuruldu, Postgres ayakta, seed çalıştı. (Bkz. [README](../README.md))

---

## İçindekiler

1. [Gemini API anahtarı alma](#1-gemini-api-anahtari)
2. [Telegram bot oluşturma (BotFather)](#2-telegram-bot-olusturma)
3. [.env dosyasını doldurma](#3-env-dosyasini-doldurma)
4. [ngrok kurulumu ve public URL](#4-ngrok-kurulumu)
5. [Telegram webhook kaydı](#5-telegram-webhook-kaydi)
6. [Bot komutlarını register etme (BotFather)](#6-bot-komutlarini-register-etme)
7. [Test müşterisini kendi numaranıza bağlama](#7-test-musterisini-baglama)
8. [Uçtan uca smoke test](#8-uctan-uca-smoke-test)
9. [Demo sırasında sık karşılaşılan sorunlar](#9-sorun-giderme)

---

## 1. Gemini API anahtarı

Yeni `google-genai` SDK Google AI Studio'dan ücretsiz API key ile çalışıyor.

**Adımlar:**

1. Tarayıcıdan [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) adresine git.
2. Google hesabınla giriş yap.
3. **"Create API key"** butonuna bas.
4. Bir Google Cloud projesi seçmen istenebilir; mevcut yoksa "Create API key in new project" seç.
5. Üretilen key'i kopyala. Format: `AIzaSy...` ile başlar, ~40 karakter.

**Önemli:**
- Bu key **kişiseldir**. Repo'ya commit etme — `.env` zaten `.gitignore`'da.
- Ücretsiz tier şu an cömert: dakikada 15 istek, günde 1500 istek. Hackathon için fazlasıyla yeterli.
- Hata olursa: rate limit yiyebilirsin (429 dönerse 60 saniye bekle).

**Doğrulama:**

```bash
source .venv/bin/activate
python -c "
import os
from google import genai
client = genai.Client(api_key='YAPISTIR_KEY_BURAYA')
r = client.models.generate_content(model='gemini-2.0-flash-exp', contents='Merhaba')
print(r.text)
"
```

Beklenen: kısa bir selamlama metni. Hata dönerse key yanlış veya quota dolmuş.

---

## 2. Telegram bot oluşturma

Bot oluşturma, Telegram'da **BotFather** adlı resmi bot üzerinden yapılır.

**Adımlar:**

1. Telegram uygulamasında arama kutusuna `@BotFather` yaz, ilk sonucu (mavi tikli) aç.
2. `/start` yaz (zaten konuşma açıksa atla).
3. `/newbot` yaz.
4. **Bot display name** sor: örn `KOBI Asistanı Test`. (Bu kullanıcılara görünen isim.)
5. **Bot username** sor: `_bot` ile bitmeli, unique olmalı. Örn `kobi_asistani_test_bot`. Username zaten doluysa BotFather sana söyler, başka dene.
6. BotFather sana **HTTP API token** verir. Format: `7891234567:AAEabc...`, ~46 karakter.
7. Token'i kopyala, **kaybetme**. (Kaybedersen `/revoke` ile yenisini alabilirsin.)

**Doğrulama:**

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | python -m json.tool
```

Beklenen: `"ok": true`, bot bilgileri (`first_name`, `username`).

---

## 3. .env dosyasını doldurma

Backend kök dizinindeki `.env` dosyasını aç ve şu alanları doldur:

```
GEMINI_API_KEY=AIzaSy...                # Bölüm 1'den
TELEGRAM_BOT_TOKEN=7891234567:AAEabc... # Bölüm 2'den
TELEGRAM_WEBHOOK_SECRET=<rastgele>       # Aşağıda üret
ADMIN_TOKEN=<rastgele>                   # Aşağıda üret
```

**Rastgele secret üretmek için:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Çıktı örn: 7K8m_nQz4PrXvBcDe1FgHi-Jk2LmNo3pQrS4tUv5Wx
```

İki kez çalıştır, biri `TELEGRAM_WEBHOOK_SECRET` için, biri `ADMIN_TOKEN` için.

**Önemli — Frontend ile sync:**

`ADMIN_TOKEN` değiştirdiğinde `frontend/.env.local` dosyasını da güncelle:

```
NEXT_PUBLIC_ADMIN_TOKEN=<aynı_değer>
```

Frontend dev server'ı yeniden başlatmazsan değer eski kalır → yeniden başlat:

```bash
# Frontend terminal'inde Ctrl+C, sonra:
cd frontend && npm run dev
```

**Doğrulama:**

```bash
source .venv/bin/activate
python -c "from app.core.config import settings; print('GEMINI key set:', bool(settings.GEMINI_API_KEY)); print('TG token set:', bool(settings.TELEGRAM_BOT_TOKEN))"
```

Beklenen: `True True`.

---

## 4. ngrok kurulumu

Telegram webhook'u localhost'a vuramaz; HTTPS public URL gerekiyor. ngrok bu boşluğu doldurur.

**İlk kurulum (bir defalik):**

```bash
brew install ngrok
```

Sonra [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup) adresinden ücretsiz hesap aç, dashboard'da authtoken'i kopyala, terminal'de:

```bash
ngrok config add-authtoken <senin_authtoken>
```

**Her demo çalışmasında:**

Backend ayakta olduğundan emin ol:

```bash
source .venv/bin/activate
uvicorn app.main:app --port 8000
```

Ayrı terminal'de:

```bash
ngrok http 8000
```

Çıktı şuna benzer:

```
Session Status   online
Forwarding       https://abc1-23-45-67-89.ngrok-free.app -> http://localhost:8000
```

**HTTPS URL'i kopyala** — sonraki adımda gerekecek. Ngrok terminal'i kapatma; URL ngrok çalıştığı sürece geçerli.

> Not: ücretsiz ngrok'ta URL her başlatmada değişir. Bu durumda webhook'u **yeniden kaydetmen** gerekiyor (Bölüm 5).

---

## 5. Telegram webhook kaydı

Yardımcı script var:

```bash
bash scripts/set_telegram_webhook.sh https://abc1-23-45-67-89.ngrok-free.app
```

Beklenen çıktı:

```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

**Doğrulama (Telegram'ın webhook'u bildiğini doğrula):**

```bash
source .env && curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" | python -m json.tool
```

Beklenen `result` içinde:
- `url`: senin ngrok URL'in + `/api/v1/webhooks/telegram`
- `has_custom_certificate`: false
- `pending_update_count`: 0 ya da küçük sayı

**Yaygın hata:**
- `Wrong response from the webhook: 401 Unauthorized` → script `.env`'i okumamış veya `TELEGRAM_WEBHOOK_SECRET` boş. `.env`'i kontrol et, secret'in dolu olduğundan emin ol.
- `SSL certificate problem` → ngrok URL'in HTTPS olduğunu doğrula. HTTP başlatıldıysa `ngrok http 8000` HTTPS verir, manuel başka URL girme.

---

## 6. Bot komutlarını register etme

Bot komutu register etmek opsiyonel ama Telegram menüsünde otomatik tamamlama gösterdiği için demo'yu cilalıyor.

**BotFather konuşması:**

1. `@BotFather`'da `/setcommands` yaz.
2. BotFather hangi bot'u soracak — listenden seçili olanı seç (yeni oluşturduğun).
3. Şu metni **tek mesajda** yapıştır:

```
start - Hosgeldin mesaji ve hesap eslemesi
siparislerim - Son siparislerimi listele
yardim - Yardim menusu
```

Her satır `komut - aciklama` formatında. Türkçe karakter kullanma, BotFather rejecte edebiliyor.

BotFather "Success!" der. Telegram client'ında bot konuşmasını yeniledikten sonra `/` yazınca menü açılır.

> Not: Bot'taki actual command handling **AI ajan tarafından** yapılıyor — `/start` veya `/yardim` mesaj olarak Customer Agent'a gidiyor, agent gerekli tool'ları çağırıp cevaplıyor. Yani komutlar Telegram menüsünde görünüyor ama özel handler yazmaya gerek yok.

---

## 7. Test müşterisini bağlama

Seed'de `Ayse Yilmaz` adlı müşteri var, `telegram_user_id=99999` ile sahte bağlı. Demo'da sen bota gerçek hesabınla yazacağın için bu sahte ID'yi temizleyip kendi telefonunu eklemek gerekir.

**İki yöntem var, sen seç:**

### Yöntem A: Telefonu güncelle, Telegram contact ile bağla

```bash
# .env'deki Postgres'e gir, telefonu kendininkiyle değiştir
docker compose exec -T postgres psql -U kobi -d kobi_db -c \
  "UPDATE customers SET phone='+905XXXXXXXXX', telegram_user_id=NULL WHERE name='Ayse Yilmaz';"
```

`+905XXXXXXXXX` yerine **kendi numaranı** uluslararası formatta yaz (E.164: `+90` + numara, boşluksuz).

Sonra Telegram'da:
1. Bot'a `/start` yaz
2. Bot telefon paylaşımı butonu gösterir, **"Numaramı paylaş"** dokun.
3. Telegram numaranı bota gönderir. Bot kendisi `phone` field'i ile veritabanındaki müşteriyi bulup `telegram_user_id`'sini bağlıyor.
4. Bot: *"Teşekkürler Ayse Yilmaz, hesabınızı eşledim..."* der.
5. Demo'ya hazır. "128 numaralı siparişim ne durumda?" yazınca cevap gelir.

### Yöntem B: Direkt Telegram ID'yi update et (numara paylaşımı atla)

Kendi Telegram numerical ID'ni öğrenmek için bota mesaj at, sonra:

```bash
source .env && curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getUpdates" | python -m json.tool | grep -m1 '"id":' | head -1
# Çıktıda en üstteki büyük sayı senin Telegram user_id'in
```

Sonra:

```bash
docker compose exec -T postgres psql -U kobi -d kobi_db -c \
  "UPDATE customers SET telegram_user_id=<senin_id> WHERE name='Ayse Yilmaz';"
```

Bu yöntem daha hızlı ama eğer bota daha önce hiç mesaj atmadıysan `getUpdates` boş döner.

---

## 8. Uçtan uca smoke test

Demo'yu çekmeden önce 5 senaryo arka arkaya çalışıyor mu kontrol et.

**Backend + frontend + ngrok ayakta olmalı.**

### Senaryo 0 — Onboarding (sadece Yöntem A için)

- Bot'a `/start` yaz → telefon paylaşım butonu görmeli
- Numara paylaş → "Hesabınızı eşledim" mesajı

### Senaryo 1 — Sipariş durumu

Bota:
> 128 numaralı siparişim ne durumda?

Beklenen: Bot Order #128'in kargoda olduğunu, lokasyonunu (İstanbul Anadolu Şubesi) ve ETA'sını söyler. ~3-5 saniye sürer.

### Senaryo 2 — Ürün sorgu + sipariş onayı

Bota:
> 3 kilo domates ne kadar tutar? Stokta var mı?

Beklenen: Domates fiyatı + stok durumu + iki inline buton: **Evet, ac** / **Vazgec**.

**Evet, ac** bas → "Siparişiniz alındı. Sipariş no: #...".

### Senaryo 3 — Geçmiş sipariş

Bota:
> Geçen ay senden ne almıştım?

Beklenen: Liste — bal, zeytinyağı vb. Toplam sayı + tarih bilgisi.

### Senaryo 4 — Panel dashboard

Tarayıcıda `http://localhost:3000` aç:

- Üst satırda 4 özet kart (son 24 saat sipariş, hazırlanacak, bugün teslim, düşük stok)
- "Bekleyen Siparişler" tablosunda satırlar var
- Düşük Stok bölümünde **Bal** görünmeli

`/orders/128` adresine git → kalemler + kargo timeline. **Yolda** noktasına kadar (3. dot) yeşil olmalı.

### Senaryo 5 — Panel NL sorgu

`/chat` sayfasına gel:
> Bu hafta Ayşe Yılmaz'dan kaç sipariş geldi?

Beklenen: Metin cevabı + altında sipariş tablosu.

**Hepsi geçtiyse demo'ya hazırsın.**

---

## 9. Sorun Giderme

| Belirti | Olası neden | Çözüm |
|---------|-------------|-------|
| Bot mesaj atmıyor | Webhook kayıtlı değil | `getWebhookInfo` çağrısı yap, URL'i kontrol et |
| Bot 401 dönüyor (logda) | `TELEGRAM_WEBHOOK_SECRET` yanlış | `.env`'i kontrol et, scripti yeniden çalıştır |
| Bot "Üzgünüm, bir hata oluştu" diyor | Gemini key yanlış veya quota dolu | `uvicorn` logunu kontrol et, `Tool error` satırlarına bak |
| Bot tanımıyor, telefon istiyor | Müşteri eşlemesi yanlış | Bölüm 7'yi tekrar yap; numara `+90` ile başlamalı |
| Dashboard 401 dönüyor | Frontend token backend ile uyumsuz | `frontend/.env.local` ve `.env` `ADMIN_TOKEN` aynı olmalı, `npm run dev` yeniden başlat |
| Bot mesaja cevap vermiyor (silent) | BackgroundTask hata yutuyor | `uvicorn` terminalinde traceback aramaya bak; Gemini API key ya da network sorunu olabilir |
| ngrok URL süresi doluyor | Ücretsiz tier 2 saat oturum limiti | ngrok'u yeniden başlat, webhook'u yeniden kaydet (Bölüm 5) |
| Inline buton bastığımda hata | TelegramSession draft süresi dolmuş | Bot'a yeniden ürün sorgu yap → yeni draft üret |
| Sipariş #128 SHIPPED değil | Seed yapılmamış veya cargo auto-advance taşımış | `bash scripts/reset_db.sh` ile yeniden seed et |

**Log incelemek için:**

```bash
# Backend logları
tail -f /tmp/uvicorn.log
# Veya uvicorn'u önplanda çalıştır, doğrudan terminal'de gör
```

**Tüm sistemi sıfırdan reset:**

```bash
bash scripts/reset_db.sh
# Sonra Bölüm 7'yi tekrar yap
```

---

## Demo Çekimi İpuçları

- **Ekran kaydı:** macOS native `Cmd+Shift+5` veya Loom. Hem Telegram client'ı hem tarayıcıyı yan yana göster.
- **Bot konuşması yumuşak görünsün** diye senaryo 1-3'ten önce bot'a birkaç deneme mesajı atıp tekrar başla — soğukken AI bazen ilk yanıtta tereddüt eder.
- **Panel'i gösterirken cursor yavaş hareket etsin** — drill-down (`/orders/128`'e tıklama) ekranda görünür olsun.
- **Hata olursa kayda devam etme** — durdurup yeniden başla. Editing post-process'ten daha hızlı.

---

## Demo Sonrası

- Webhook'u temizlemek istersen (boşa istek gelmesin):
  ```bash
  source .env && curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook"
  ```
- Container'ı durdurmak için: `docker compose down`
- ngrok ve uvicorn terminal'lerini Ctrl+C ile kapat.
