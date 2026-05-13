# KOBİ Asistanı

KOBİ Asistanı, küçük ve orta ölçekli işletmelerin günlük operasyonlarında yaşadığı sipariş takibi, stok kontrolü, kargo izleme, müşteri iletişimi ve tedarik süreçlerini yapay zeka destekli tek bir panelde toplayan operasyon asistanıdır.

Sistem yalnızca soru cevap veren bir chatbot değildir. Sipariş, müşteri, ürün, stok ve kargo verileriyle çalışır; kritik durumları tespit eder, kullanıcıya öneri sunar ve onay alındığında tedarikçi maili gibi aksiyonları gerçekleştirebilir.

## Problem

KOBİ’ler sipariş, stok ve kargo süreçlerini çoğunlukla Excel, telefon, WhatsApp, e-posta ve farklı kargo panelleri üzerinden manuel olarak takip eder. Bu durum zaman kaybına, hatalı müşteri bilgilendirmesine, geç fark edilen stok problemlerine ve operasyonel gecikmelere yol açar.

Özellikle “Siparişim nerede?”, “Bu ürün stokta var mı?”, “Bugün hangi siparişler hazırlanmalı?”, “Hangi ürün bitmek üzere?” gibi tekrar eden sorular işletme sahiplerinin ciddi zamanını alır.

## Çözüm

KOBİ Asistanı, bu süreçleri web paneli ve Telegram botu üzerinden yönetilebilir hale getirir. Yönetici panelden günlük operasyon özetini, siparişleri, müşterileri, ürünleri, kritik stokları ve kargo risklerini takip edebilir. AI chat alanı doğal dilde sorulan soruları anlayarak ilgili veriyi getirir ve gerektiğinde aksiyon önerir.

Telegram entegrasyonu sayesinde kullanıcılar metin, sesli mesaj veya görsel göndererek sistemle etkileşime geçebilir. Sesli mesajlar yazıya çevrilir, görseller analiz edilir ve elde edilen bilgi mevcut operasyon akışına aktarılır.

## Ana Özellikler

- Günlük operasyon özeti
- Sipariş durumu sorgulama
- Müşteri bazlı sipariş listeleme
- Ürün ve stok sorgulama
- Kritik stok tespiti
- Tedarikçi sipariş mesajı hazırlama
- Onay sonrası Gmail üzerinden gerçek tedarikçi maili gönderme
- Kargo gecikme riski analizi
- Telegram üzerinden metin, sesli mesaj ve görsel işleme
- Demo verisiyle çalışan gerçekçi senaryolar
- Gemini API çoklu key fallback yapısı
- AI erişilemezse temel işlemler için backend tabanlı fallback cevaplar

## AI Kullanımı

Sistemde yapay zeka üç ana amaçla kullanılır.

Birinci amaç doğal dil anlama ve yönlendirmedir. Kullanıcının sorusu sipariş, stok, kargo, müşteri veya tedarik süreciyle ilgiliyse sistem bunu ilgili fonksiyona yönlendirir.

İkinci amaç ses ve görsel mesajları işlenebilir metne dönüştürmektir. Telegram’dan gelen sesli mesajlar Gemini ile yazıya çevrilir. Görseller Gemini ile analiz edilerek ürün, miktar veya sipariş niyeti gibi bilgiler çıkarılır.

Üçüncü amaç operasyonel cevapları kullanıcıya anlaşılır şekilde sunmaktır. Sistem veritabanından aldığı bilgileri sade ve aksiyon odaklı cevaplara dönüştürür.

Önemli nokta: Sipariş, stok ve kargo verileri yapay zeka tarafından uydurulmaz. AI yalnızca niyet anlama, yorumlama ve cevap üretme katmanında kullanılır. Temel veriler backend ve veritabanından gelir.

## Demo Senaryosu

Demo sırasında aşağıdaki akış gösterilebilir.

1. Dashboard açılır ve AI önerileri gösterilir.
2. Chat alanına “Bugünkü operasyon özetini çıkar” yazılır.
3. “128 numaralı sipariş nerede?” sorusu ile sipariş takibi gösterilir.
4. “Düşük stoktaki ürünleri listele” sorusu ile kritik stoklar gösterilir.
5. “Kritik stoklar için tedarikçi mesajı hazırla” komutu çalıştırılır.
6. “Onayla ve mail gönder” butonu ile tedarikçi maili gönderilir.
7. Telegram üzerinden sesli mesajla sipariş oluşturma akışı gösterilir.
8. Telegram üzerinden ürün görseli gönderilerek görselden ürün tespiti ve sipariş önerisi gösterilir.

## Örnek Sorular

- Bugünkü operasyon özetini çıkar
- Bu hafta günlük satış grafiğini göster
- 128 numaralı sipariş nerede?
- Ayşe Yılmaz’ın son siparişlerini göster
- Düşük stokta olan ürünleri listele
- Kritik stoklar için tedarikçi mesajı hazırla
- Kargo gecikme riski olan siparişleri göster
- Geciken kargo için müşteri mesajı hazırla
- 6 kilo çay siparişi vermek istiyorum

## Teknik Mimari

Sistem aşağıdaki ana bileşenlerden oluşur.

- Frontend: Next.js tabanlı web paneli
- Backend: FastAPI ve Python
- Veritabanı: PostgreSQL
- AI Katmanı: Gemini API
- Mesajlaşma Kanalı: Telegram Bot Webhook
- Mail Servisi: Gmail API
- Veritabanı Migrasyonu: Alembic
- Demo Verisi: Seed script ile oluşturulan sentetik KOBİ verileri

Genel akış:

```text
Kullanıcı / Telegram / Web Chat
        ↓
Next.js Frontend veya Telegram Webhook
        ↓
FastAPI Backend
        ↓
Intent ve veri işleme katmanı
        ↓
PostgreSQL + Gemini + Gmail API
        ↓
Cevap, öneri veya aksiyon
```

## Kurulum

### 1. Projeyi indir

```powershell
git clone <repo-url>
cd KOBI-Asistani-main
```

### 2. Docker ile PostgreSQL’i başlat

Docker Desktop açık olmalıdır.

```powershell
docker compose up -d
```

Kontrol için:

```powershell
docker ps
```

### 3. Backend sanal ortamını oluştur

```powershell
py -m venv .venv
.\.venv\Scripts\activate
```

### 4. Backend bağımlılıklarını kur

```powershell
pip install fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" asyncpg "psycopg[binary]" alembic pydantic pydantic-settings httpx google-genai apscheduler python-multipart groq google-auth-oauthlib google-api-python-client
```

### 5. Backend ortam değişkenlerini oluştur

Proje ana klasöründe `.env` dosyası oluşturulmalıdır. Gerçek tokenlar GitHub’a yüklenmemelidir.

```env
DATABASE_URL=postgresql+asyncpg://kobi:kobi@localhost:5434/kobi_db
DATABASE_SYNC_URL=postgresql+psycopg://kobi:kobi@localhost:5434/kobi_db
ADMIN_TOKEN=change_me
CORS_ORIGINS=http://localhost:3000

GEMINI_API_KEYS=gemini_key_1,gemini_key_2
STT_PROVIDER=gemini

TELEGRAM_BOT_TOKEN=telegram_bot_token_here
SUPPLIER_EMAIL=tedarikci@example.com
```

Tek Gemini key kullanılacaksa alternatif olarak şu kullanılabilir:

```env
GEMINI_API_KEY=gemini_key_here
```

### 6. Veritabanı tablolarını oluştur ve demo verisini yükle

```powershell
alembic upgrade head
python -m app.db.seed --clear --demo-fixtures
python -m app.db.normalize_product_names
```

### 7. Backend’i çalıştır

```powershell
uvicorn app.main:app --reload --port 8000
```

Backend başarılı çalışırsa terminalde şu ifade görülür:

```text
Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

### 8. Frontend ortam değişkenlerini oluştur

`frontend/.env.local` dosyası oluşturulmalıdır.

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_ADMIN_TOKEN=change_me
```

Buradaki token ile backend `.env` içindeki `ADMIN_TOKEN` aynı olmalıdır.

### 9. Frontend’i çalıştır

Yeni bir terminal açılır.

```powershell
cd frontend
npm install
npm run dev
```

Uygulama şu adresten açılır:

```text
http://localhost:3000
```

## Telegram Webhook Kurulumu

Telegram webhook için local backend’in dış dünyaya açılması gerekir. Bunun için ngrok kullanılabilir.

### 1. Ngrok’u çalıştır

```powershell
ngrok http 8000
```

Ngrok şu formatta bir adres verir:

```text
https://example.ngrok-free.dev -> http://localhost:8000
```

### 2. Webhook’u Telegram’a tanıt

PowerShell’de aşağıdaki komut çalıştırılır.

```powershell
$BOT_TOKEN="telegram_bot_token_here"
$WEBHOOK_URL="https://example.ngrok-free.dev/api/v1/webhooks/telegram"
Invoke-RestMethod "https://api.telegram.org/bot$BOT_TOKEN/setWebhook?url=$WEBHOOK_URL"
```

### 3. Webhook kontrolü

```powershell
Invoke-RestMethod "https://api.telegram.org/bot$BOT_TOKEN/getWebhookInfo"
```

`url` alanında ngrok webhook adresi görünmelidir.

### 4. Test

Telegram botuna metin, sesli mesaj veya ürün görseli gönderilir. Backend terminalinde şu tarz log görülmelidir.

```text
POST /api/v1/webhooks/telegram 200 OK
```

## Gmail Entegrasyonu

Tedarikçi maili göndermek için Gmail API bağlantısı kullanılmaktadır. Kullanıcı chat alanında kritik stoklar için tedarikçi mesajı hazırladığında sistem bir taslak oluşturur. Kullanıcı “Onayla ve mail gönder” butonuna bastığında mail gerçek olarak tedarikçiye gönderilir.

Gmail yetkilendirme dosyaları ve token dosyaları GitHub’a yüklenmemelidir.

## Güvenlik ve GitHub’a Hazırlama

Bu projeyi GitHub’da paylaşmadan önce gizli bilgiler mutlaka temizlenmelidir.

Aşağıdaki dosyalar repoya yüklenmemelidir:

```text
.env
.env.local
frontend/.env.local
credentials.json
token.json
gmail_token.json
google_token.json
client_secret*.json
ngrok.yml
.venv/
node_modules/
frontend/node_modules/
.next/
frontend/.next/
__pycache__/
*.log
```

`.gitignore` içinde en az şu kurallar bulunmalıdır:

```gitignore
.env
.env.*
!.env.example
frontend/.env.local
credentials.json
token.json
gmail_token.json
google_token.json
client_secret*.json
ngrok.yml
.venv/
node_modules/
frontend/node_modules/
.next/
frontend/.next/
__pycache__/
*.pyc
*.log
```

Eğer gizli dosyalar yanlışlıkla Git’e eklendiyse, lokal dosyayı silmeden takipten çıkarmak için:

```powershell
git rm --cached .env
git rm --cached frontend/.env.local
git rm --cached credentials.json
git rm --cached token.json
```

Sonra commit atılır.

```powershell
git add .
git commit -m "Clean secrets and finalize project documentation"
```

Eğer herhangi bir API key, Gmail token veya Telegram bot token daha önce GitHub’a pushlandıysa sadece dosyayı silmek yeterli değildir. O token artık sızmış kabul edilmeli ve ilgili platformdan yenilenmelidir.

Paylaşmadan önce proje içinde gizli bilgi aramak için PowerShell’de şu komut kullanılabilir:

```powershell
Select-String -Path .\* -Pattern "GEMINI_API_KEY|GEMINI_API_KEYS|TELEGRAM_BOT_TOKEN|SUPPLIER_EMAIL|AIza|bot[0-9]|client_secret|token" -Recurse
```

## Teslim İçin Kontrol Listesi

- Backend çalışıyor mu?
- Frontend açılıyor mu?
- Dashboard verileri geliyor mu?
- Chat günlük özet çıkarıyor mu?
- 128 numaralı sipariş sorgulanıyor mu?
- Kritik stoklar listeleniyor mu?
- Tedarikçi mail taslağı hazırlanıyor mu?
- Onay sonrası Gmail maili gidiyor mu?
- Telegram metin mesajı çalışıyor mu?
- Telegram sesli mesaj çalışıyor mu?
- Telegram görsel mesaj çalışıyor mu?
- `.env` ve token dosyaları GitHub’a eklenmemiş mi?
- README güncel mi?
- Demo videosu maksimum 1 dakika içinde akıcı mı?

## 1 Dakikalık Demo Metni

KOBİ Asistanı, küçük işletmelerin sipariş, stok, kargo ve müşteri iletişimi süreçlerini tek bir yapay zeka destekli panelde toplar. KOBİ’ler normalde bu işleri Excel, telefon, WhatsApp ve farklı kargo panelleri üzerinden manuel takip ederken, bu sistem tüm operasyonu tek ekranda izlenebilir hale getirir.

Dashboard’da günlük operasyon özeti, kritik stoklar ve kargo riskleri görünür. AI chat üzerinden “128 numaralı sipariş nerede?” gibi sorular sorulduğunda sistem veritabanındaki gerçek sipariş bilgisini getirir. “Düşük stokları listele” dediğimizde kritik ürünleri bulur ve tedarik önerisi oluşturur. Onay verildiğinde Gmail üzerinden tedarikçiye gerçek mail gönderilir.

Ayrıca Telegram entegrasyonu sayesinde kullanıcılar sesli mesaj veya ürün görseliyle de işlem yapabilir. Sistem sesi yazıya çevirir, görseli analiz eder, sipariş veya stok niyetini anlayarak aksiyon önerir. Böylece proje sadece cevap veren bir chatbot değil, veriyle çalışan ve işlem yapabilen bir KOBİ operasyon asistanıdır.

## Lisans

Bu proje hackathon prototipi olarak geliştirilmiştir. Demo verileri sentetiktir ve gerçek müşteri verisi içermez.
