# Telegram Bot — Test Senaryoları

Hackathon demo'su için 9 uçtan uca senaryo. Her senaryo bağımsız çalışır; jüriye gösterirken sırayla denenebilir veya tek tek seçilebilir.

> **Bot adı:** [@kobi_asistani_bot](https://t.me/kobi_asistani_bot) (örnek — gerçek isim BotFather'da set edildi)
> **Panel:** https://kobi-panel.fatiherencetin.com
> **Backend:** https://kobi-asistan.fatiherencetin.com

## 🔧 Hazırlık (Bir Defalık)

1. **Seed verisi kurulu olmalı**: `bash scripts/reset_db.sh` çalıştırıldı veya `/expiring` sayfasında "Demo Veriyi Yükle" tıklandı.
2. **`.env` flag'ları** demo için aktif olmalı:
   ```bash
   STT_ENABLED=true
   STT_PROVIDER=gemini
   PROACTIVE_NOTIFICATIONS_ENABLED=true
   ADMIN_TELEGRAM_ID=<jüri admin'in TG chat_id'si>
   ```
3. **Webhook kayıtlı**: `bash scripts/set_telegram_webhook.sh https://kobi-asistan.fatiherencetin.com`

---

## S1 — Yeni Müşteri Onboarding (Numara Eşleme)

**Amaç:** Bot ile ilk kez konuşan kullanıcının kimlik eşleştirmesi.

**Ön koşul:** Bu Telegram hesabı daha önce eşlenmemiş (yeni hesap veya seed sonrası reset).

**Adımlar:**
1. Telegram'da botu aç, `/start` veya herhangi bir metin yaz (örn. "merhaba")
2. **Beklenen yanıt:**
   > Merhaba 👋 Sizi tanıyabilmem için telefon numaranızı paylaşır mısınız?
   > [📱 Numaramı paylaş]
3. Klavyenin altındaki "📱 Numaramı paylaş" butonuna tıkla
4. Telegram contact paylaşma onayı çıkar → **Paylaş**

**Beklenen sonuç:**
> Teşekkürler **{adınız}**, hesabınızı eşledim ✅
> Size nasıl yardımcı olabilirim?

**Doğrulama (panelden):**
- `/customers` sayfasında yeni satır görünmeli, "Telegram" sütunu boş değil.

---

## S2 — Sipariş Durumu Sorgusu (Yazılı Metin)

**Amaç:** Mevcut bir siparişin durumu sorgulansın, kargo bilgisi dönsün.

**Ön koşul:** Onboarding tamamlanmış. Seed verisinde **Sipariş #128 (Ayşe Yılmaz)** `SHIPPED` + `IN_TRANSIT` durumda. (Kendi hesabınız Ayşe'ye eşleniyorsa: `docker compose exec -T postgres psql -U kobi -d kobi_db -c "UPDATE customers SET telegram_user_id=<senin_tg_id> WHERE name='Ayse Yilmaz';"`)

**Adımlar:**
1. Bot'a yaz: `128 numaralı siparişim ne zaman gelir?`

**Beklenen yanıt:**
- Bot kargo durumunu ve tahmini teslim tarihini açıklar
- Örnek format:
  > 128 numaralı siparişiniz şu anda **İstanbul Anadolu Şubesi**'nde, yarın teslim edilmesi bekleniyor 📦
  > Kargo durumu: Yolda • Tahmini teslimat: 2026-05-14

**Doğrulama:** Cevapta sipariş numarası, kargo durumu, konum, ETA görünmeli.

---

## S3 — 📸 Fotoğrafla Ürün Tanıma + Sipariş (YENİ — Vision)

**Amaç:** Müşteri ne istediğini fotoğrafla anlatır; bot Gemini Vision ile tanır.

**Ön koşul:** Onboarding tamamlanmış. `GEMINI_API_KEY` (veya `GEMINI_API_KEYS`) tanımlı.

**Adımlar:**
1. Telefonla bir **bal kavanozu** veya **zeytinyağı şişesi** fotoğrafı çek (veya internetten bir görsel indir)
2. Telegram'da bota gönder. **Caption (isteğe bağlı):** `2 kilo istiyorum`

**Beklenen yanıt akışı:**
1. (anında) Bot: `📸 Fotoğrafta Bal gördüm. Anlıyorum…`
2. (~3-5 sn) Agent fiyat + stok bilgisi:
   > Süzme balımızdan stoğumuzda **8 kg** kaldı, kilosu **280 TL**.
   > 2 kg sipariş açayım mı?
   > [✅ Evet, aç] [❌ Vazgeç]

**Doğrulama:** Backend log'da `Vision identified product=Bal confidence=high` satırı görünür.

**Alternatif testler:**
- Fotoğrafı tanıyamadığında (örn. araba fotoğrafı): `Fotoğraftaki ürünü net tanıyamadım. Hangi üründen bahsettiğinizi yazabilir misiniz?`
- Caption verilirse caption öncelikli kabul edilir (Vision sadece doğrulama amaçlı kullanılır)

---

## S4 — 🎤 Sesli Mesaj (STT — Speech-to-Text)

**Amaç:** Müşteri yazmak yerine konuşur, bot anlar.

**Ön koşul:** `.env`'de `STT_ENABLED=true`, `STT_PROVIDER=gemini` (veya `whisper` + `OPENAI_API_KEY`).

**Adımlar:**
1. Telegram'da bota **sesli mesaj** kaydet ve gönder: `"5 kilo süzme bal istiyorum"`
2. Bot ses dosyasını Gemini'ye yollar, transkripti yapar

**Beklenen yanıt:**
- Bot mesajı yazıya çevirir, agent sipariş draft'ı sunar:
  > Süzme balımızdan 5 kg, toplam **1.400,00 TL** tutuyor.
  > Siparişi açayım mı?
  > [✅ Evet, aç] [❌ Vazgeç]

**Negatif test:** `STT_ENABLED=false` ile → "Sesli mesaj desteği yakında geliyor. Yazılı olarak iletebilir misiniz?"

---

## S5 — Ürün Sorgu + Inline Buton ile Sipariş Onayı

**Amaç:** Müşteri sipariş için onay verir, sipariş DB'ye düşer, stok azalır.

**Ön koşul:** Onboarding tamamlanmış. **Bal** ürünü stokta (≥2 kg).

**Adımlar:**
1. Yaz: `2 kilo süzme bal istiyorum`
2. Bot fiyat + onay butonu sunar
3. **✅ Evet, aç** butonuna tıkla

**Beklenen yanıt:**
> Siparişiniz alındı ✨
> Sipariş no: **#{yeni_id}**
> Tutar: **560,00 TL**
> Durum: hazırlanmaya alındı.

**Doğrulama (panelden):**
- `/orders` sayfasında yeni sipariş **Yeni (Pending)** durumda görünür
- Tıkla → kalemler tabloda **Bal 2 kg × 280 TL**
- `/products/1` (Bal) sayfasında: **Stok 8 → 6** düşmüş
- `/products/1` Stok Hareketleri tablosu: **Satış -2 kg** + bakiye 6 + "Kullanıcı" sütunu boş (Telegram müşteri girişi)

**FIFO doğrulaması:** Eğer Bal için lot kaydı varsa (BAL-2510-01), o lot'un quantity'si 2 birim düşmeli.

---

## S6 — Geçmiş Sipariş Listesi (Doğal Dil)

**Amaç:** Müşteri "geçen ay" gibi sorularla geçmişini öğrenir.

**Ön koşul:** Test eden hesap geçmiş siparişlere sahip (Ayşe Yılmaz fixture'ında 3 sipariş + #128 var).

**Adımlar:**
1. Bot'a yaz: `Geçen ay senden ne almıştım?`

**Beklenen yanıt:**
- Liste + insight:
  > Son 30 günde **4 siparişiniz** olmuş, toplam **{tutar} TL**:
  > • Bal 2 kg
  > • Zeytinyağı 1 lt
  > • Bal 1.5 kg
  > • Zeytinyağı 2 lt + Domates 3 kg
  > 
  > En çok aldığınız ürünler: **Bal** ve **Zeytinyağı** 🍯

---

## S7 — Şikayet Sinyali (Otomatik Tespit)

**Amaç:** Müşteri olumsuz bir şey yazınca panel'de algılansın.

**Ön koşul:** Onboarding tamamlanmış. `GEMINI_API_KEY` aktif.

**Adımlar:**
1. Bot'a yaz: `Ürün bozuk geldi, çok kötü kalitede, iade istiyorum!`

**Görünür sonuç (Telegram):**
- Agent normal cevap verir: özür mesajı + "size yardımcı olmak için iade sürecini başlatalım"

**Arka planda otomatik:**
- Regex filtre: `iade`, `bozuk`, `kötü` sinyalleri yakalar
- Gemini'ye risk skoru sorulur (paralel)
- Skor ≥ 0.7 → `CustomerComplaint` tablosuna kayıt düşer

**Doğrulama (panelden):**
1. `/complaints` sayfasını aç
2. Yeni mesaj **rose/amber border** ile listede görünür
3. Rozet: 🔴 **Telegram Mesajı** + Risk %{N}
4. Mesaj metni alıntı şeklinde gözükür
5. Sinyaller: `iade`, `bozuk`, `kötü` rozetleri

**Bonus:** `/complaints` üst kısımdaki **"Şimdi Tara"** butonu ile proaktif kategoriler de tetiklenebilir (kargo gecikmesi, bayat sipariş vb.).

---

## S8 — 🚚 Proaktif Kargo Gecikme Bildirimi

**Amaç:** Sistem otomatik olarak geciken kargoları tespit edip müşteriye özür mesajı + admin'e uyarı gönderir.

**Ön koşul:**
- `.env`'de `PROACTIVE_NOTIFICATIONS_ENABLED=true`
- `ADMIN_TELEGRAM_ID=<admin Telegram chat_id'si>` set edilmiş (admin'e bildirim için)
- DB'de en az 1 sipariş: `estimated_delivery < bugün`, `status != DELIVERED`. Seed'deki #128 için manuel olarak:
  ```bash
  docker compose exec -T postgres psql -U kobi -d kobi_db -c \
    "UPDATE shipments SET estimated_delivery = CURRENT_DATE - INTERVAL '3 days' WHERE order_id=128;"
  ```

**Tetikleme yöntemleri:**
- **Otomatik:** APScheduler saatte bir tetikler (her saatin 15. dakikası)
- **Manuel (demo için):** Panelde `/complaints` sayfasını aç → **"Şimdi Tara"** butonuna tıkla

**Beklenen sonuç:**
1. **Müşteriye Telegram mesajı:**
   > Merhaba {ad}, #128 numaralı siparişinizin kargo teslim tarihi 3 gün geçti (mevcut konum: İstanbul Anadolu Şubesi). Gecikme için özür dileriz. Durumu yakından takip ediyoruz ve en kısa zamanda elinize ulaşması için kargo firmasıyla görüşüyoruz.

2. **Admin'e Telegram bildirimi** (eğer `ADMIN_TELEGRAM_ID` set ise):
   > ⚠️ Kargo gecikme alarmı
   >
   > Sipariş #128 (Ayşe Yılmaz)
   > Takip: TR... (MockKargo)
   > Gecikme: 3 gün
   > Mevcut konum: İstanbul Anadolu Şubesi
   > Müşteriye otomatik özür mesajı iletildi.

3. **Panel `/complaints`'a yeni kayıt:**
   - Rozet: 🟡 **Kargo Gecikmesi** + 🤖 **AI tespiti**
   - Konu: AI tarafından yazılmış (örn. "Kargo gecikmesi: Sipariş #128 (Ayşe Yılmaz)")
   - Açıklama: AI tarafından yazılmış uzun paragraf

**İdempotent:** Aynı şipment için 24 saat içinde tekrar tarama yapılırsa yeni complaint düşmez.

---

## S9 — Bilinmeyen Kullanıcı Sipariş Açmaya Çalışır

**Amaç:** Eşlenmemiş bir kullanıcı yetkisiz iş yapamasın.

**Ön koşul:** Bu Telegram hesabı eşlenmemiş.

**Adımlar:**
1. Bot'a: `5 kilo bal istiyorum`

**Beklenen sonuç:**
> Merhaba 👋 Sizi tanıyabilmem için telefon numaranızı paylaşır mısınız?
> [📱 Numaramı paylaş]

Onboarding'e geri döner — sipariş açma akışı başlamaz.

---

## 📊 Senaryo Özet Tablosu

| # | Senaryo | Yeni Özellik | Tahmini Süre |
|---|---------|--------------|--------------|
| S1 | Onboarding (numara paylaş) | — | 30 sn |
| S2 | Sipariş durumu (yazılı) | — | 30 sn |
| S3 | Fotoğrafla ürün tanıma | ✨ Vision | 1 dk |
| S4 | Sesli mesaj (STT) | — | 1 dk |
| S5 | Ürün sorgu + onaylı sipariş | — | 1 dk |
| S6 | Geçmiş sipariş listesi | — | 30 sn |
| S7 | Şikayet sinyali tespiti | — | 1 dk |
| S8 | Proaktif gecikme bildirimi | ✨ Notify | 2 dk |
| S9 | Bilinmeyen kullanıcı engeli | — | 30 sn |

**Demo süresi (sıralı tüm senaryolar):** ~8 dakika.

## 🐛 Sorun Giderme

- **"Bot cevap vermiyor"**: `bash scripts/set_telegram_webhook.sh` ile webhook'u yeniden kaydet.
- **"Sesli mesajı çözemedim"**: `.env`'de `STT_ENABLED=true` ve `STT_PROVIDER=gemini` set olmalı. Yeniden başlat.
- **"Vision tanımadı"**: `GEMINI_API_KEY` veya `GEMINI_API_KEYS` set olmalı. Quota dolduysa multi-key fallback devreye girer.
- **"Proaktif notify çalışmadı"**: `PROACTIVE_NOTIFICATIONS_ENABLED=true` ve `ADMIN_TELEGRAM_ID` set olmalı. Manuel tetikleme için panel `/complaints` → "Şimdi Tara".
