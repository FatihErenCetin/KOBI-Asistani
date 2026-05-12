# UI/UX Tasarım Brief'i — Akıllı KOBİ/Kooperatif Asistanı Paneli

> Bu doküman, Claude'a (veya başka bir AI design asistanına) verilerek mevcut Next.js panelinin UI/UX'ini yeniden tasarlatmak için kullanılır.
> Her bölüm bağımsız olarak referans edilebilir; "ben sadece Dashboard sayfasını yenilemek istiyorum" desen Bölüm 8.1'i seçip atabilirsin.

---

## 1. Ürün Özeti

**Ürün:** Küçük/orta ölçekli işletmeler (KOBİ) ve tarım kooperatifleri için Telegram tabanlı müşteri asistanı + yönetim paneli.

**Bu brief'in kapsamı:** Yönetim paneli. (Telegram tarafı Telegram'ın kendi UI'ı — değiştiremiyoruz.)

**Hedef Kullanıcı:** 35-55 yaş aralığında, teknik altyapı eğitimi olmayan, **günde 10-100 sipariş işleyen** işletme sahibi veya kooperatif yöneticisi. Sabah ofisi açar açmaz paneli aç, kahve içerken durumu kavrar, sonra siparişleri işlemeye geçer.

**Kullanım sıklığı:** Günde 3-5 kez kısa oturumlar (özet kontrol) + 1-2 kez derin oturum (sipariş drill-down).

**Cihaz:** Birincil olarak **desktop** (1280px+). Tablet ikincil. Mobil ihmal edilebilir (mobil için zaten Telegram bot var).

---

## 2. Tasarım Vizyonu

Sıralı önemli üç adjektif:

1. **Sakin (calm):** Yönetici telefon, müşteri, kargo arasında zaten panik içinde. Panel `digital ferahlık` sunmalı; göz yormamalı.
2. **Güvenilir (trustworthy):** Bu finansal veri. Saçma renkler, gereksiz animasyon, deneysel layout yok. Tablolar, sayılar, açık hiyerarşi.
3. **Sıcak (warm):** Soğuk SaaS hissi yerine kooperatif teması — toprak/yeşil çağrışımları. Müşteri adları, ürün isimleri, paydaş hissi.

**Karşıt referanslar (kaçınılacak):**
- Banka panelleri (çok soğuk, çok teknik)
- Salesforce/SAP (info overload, gri-mavi monotonluk)
- B2C Shopify dashboard (çok parlak/satışçı)

**İyi referanslar (esinlenilecek):**
- **Linear** (linear.app): bilgi yoğunluğu + ferahlık dengesi
- **Stripe Dashboard**: sayı sunumu, finansal güven hissi
- **Notion**: tipografi ve nefes alma boşluğu
- **Hey.com (Basecamp)**: sıcak ton, marka dilinde duygu

Genel hava: "**Stripe + Hey'in çocuğu, tarımda büyümüş.**"

---

## 3. Marka & Tonalite

**İsim:** Akıllı KOBİ/Kooperatif Asistanı (geçici, son adlandırma kullanıcıya bırakılmış).

**Logo:** Henüz yok. Brief'te bir text-mark veya çok minimal bir ikon (örn. yaprak, başak, sepet) önerebilirsin.

**Dil:** Tamamen Türkçe. Resmi 2. tekil ("siz") kullanıcıya, samimi 2. tekil ("sen") asistan kişiliğine — ama bu Telegram tarafında, panelde formal kalıyoruz.

**Mikrocopy örnekleri (panel):**
- ✅ "Bugün teslim edilecek 5 kargo var" (net, somut)
- ❌ "Aktif lojistik operasyonları" (kurumsalca, soğuk)
- ✅ "Stok azalıyor: Bal (8 kg)" (uyarı + spesifik)
- ❌ "Envanter uyarısı: Bal" (jargon)

---

## 4. Renk Paleti

### Mevcut (`tailwind.config.ts`):

```
brand-50:  #ecfdf5  (çok açık emerald, background highlight)
brand-500: #10b981  (ana yeşil, vurgu)
brand-600: #059669  (CTA buton, link)
brand-700: #047857  (hover state)
```

Yan tonlar (Tailwind default): `slate-*` (nötr gri), `amber-*` (uyarı), `rose-*` (kritik), `emerald-*` (başarı), `indigo-*` (kargoda durum), `blue-*` (hazırlandı durum).

### Brief için soru:

Bu palet **kasıtlı seçildi** (emerald = kooperatif/tarım çağrışımı). Tasarım iterasyonunda korunmalı **ama** şu noktalarda iyileştirme bekliyoruz:

- **Tek-renk monotonluğu var.** brand-500 her yerde — buton, link, kargo timeline dot, hover. Daha çok katman gerekiyor: koyu/açık varyantlar, accent color (örn. terracotta veya hardal sarı uyarılar için).
- **Dark mode** yok. Eklemek priority 3 değerinde — sabah 8 öncesi panele bakan yönetici için iyi olur.
- **Status badge renkleri** Tailwind tonlarından kapma; bütünleşik bir status palette tasarlanabilir.

### Önerilen genişletme (sen önerebilirsin):

- **Toprak accent:** terracotta `#c2410c` veya umber `#92400e` — özellikle "düşük stok" gibi durumlar için emerald'dan ayrışmalı.
- **Sıcak nötr arka plan:** mevcut `slate-50` çok soğuk; `stone-50` (#fafaf9) veya hafif sepia tona kayma denenebilir.

---

## 5. Tipografi

**Mevcut:** System UI stack (`ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto`).

**Brief için soru:**

Türkçe karakterleri (ş, ç, ğ, İ) iyi destekleyen, **finansal sayılarda monospace numerik özelliği olan** bir font ailesi öner.

İyi adaylar (kişisel önerim, değiştirebilirsin):
- **Inter** (Rasmus Andersson) — UI standard, Türkçe iyi, tabular nums seçeneği var
- **Geist** (Vercel) — modern, Türkçe destekli, monospace varyantı mevcut
- **DM Sans** + **DM Mono** kombinasyonu — pair olarak çalışır

**Tipografi ihtiyaçları:**
- **Sayılar (TRY, miktar):** `tabular-nums` ON — tablolarda sütunlar hizalanmalı
- **Hiyerarşi:** H1 (sayfa başlığı) → H2 (kart/section başlığı) → body → caption (4 seviye)
- **Müşteri adları:** insan ismi olduğunu vurgulamak için `font-medium` veya küçük tipografik nüans

---

## 6. Mevcut Sayfa Envanteri

Brief'in 8. bölümünde her sayfa için detaylı tasarım talebi var. Burada özet:

| Yol | Sayfa | Birincil amaç | Bilgi yoğunluğu |
|-----|-------|---------------|----------------|
| `/` | Dashboard | "Bugün ne var?" — özet | Yüksek (4 kart + 4 panel) |
| `/orders` | Sipariş listesi | Filtrelenebilir tablo | Yüksek |
| `/orders/[id]` | Sipariş detay | Drill-down + kargo timeline | Orta |
| `/products` | Ürün/stok tablosu | Stok seviyesi görünür | Orta |
| `/customers` | Müşteri listesi | Arama + tablo | Düşük |
| `/customers/[id]` | Müşteri detay | KPI kartları + sipariş geçmişi | Orta |
| `/chat` | AI Asistan | Sohbet + dinamik render | Düşük başlar, dolu olur |

**Sabit shell:** Sol sidebar (5 link), sağ ana içerik. Sidebar şu an `bg-slate-900` (koyu). Bu kontrastı brief'te koruyabilir veya alternatif sunabilirsin.

---

## 7. Tasarım Sistemi — Bileşen Listesi

Mevcut bileşenler (her birinin redesign'a açık olduğu özelliği parantezde):

- `SummaryCards` (4-up grid, ikonsuz — **ikon eklenmesi gerek**)
- `PendingOrdersTable` (basit HTML tablo — **density/zebra striping yok**)
- `LowStockList` (text only — **görsel indikator zayıf**)
- `TodaysShipments` (liste — **kargo durum chip'leri görünmüyor**)
- `OrderStatusBadge` (renkli pill — yeterli, koruabilir)
- `ShipmentTimeline` (5 dot dikey — **görsel olarak zayıf, "progress" hissi yok**)
- `ChatPanel` (basit balon + form — **yapay tip stok**)
- `OrderListRender`, `SalesChart` (recharts), `StockOverviewRender` (chat içinde render edilen mini-bileşenler)

**Eklenmesi önerilen bileşenler (brief'e dahil etmen iyi olur):**
- **Empty state** (sipariş yok, stok yok vb.) — şu an sadece "Kayıt yok" yazıyor
- **Loading skeleton** — Next.js Server Components fetch sırasında ekran boş kalıyor
- **Toast/notification** — durum değiştirme aksiyonları için
- **Confirmation dialog** — sipariş iptal etmek gibi geri-alınamaz aksiyonlar
- **Tooltip** — sayılar üzerinde detay (örn. % değişim açıklaması)

---

## 8. Sayfa Sayfa Brief

Her sayfa için: **amaç, mevcut durum, sorun, beklenen iyileşme**.

### 8.1 Dashboard (`/`)

**Amaç:** Yönetici paneli açar açmaz son 24 saatin ve bugün yapılması gerekenlerin tam görünümü.

**Mevcut layout:**
```
[Üst: 4 özet kartı (sipariş, hazırlanacak, kargo, stok)]
[Sol 2/3: bekleyen siparişler + son 24h tablosu]
[Sağ 1/3: düşük stok listesi + bugün kargolar]
```

**Sorunlar:**
1. **4 kart aynı görünüyor** — hangi karta öncelik vermeli kullanıcı anlamıyor. **"Acil" göstergeleri yok.**
2. Kartlardaki ikinci satır (alt sub-text) çok sönük, gözden kaçıyor.
3. "Hazırlanacak" kartında "acil bugün" sayısı kritikse de tıklanabilir değil — drill-down'a link olmalı.
4. Düşük stok listesi sıradan bir UL — **bar/gauge** ile "ne kadar düşük" hissedilmiyor.
5. Bugün kargolar bölümünde ETA çok küçük, kullanıcı **konum + saat**'e odaklanmalı.

**İstenen iyileştirme:**
- Kartlarda **ikon + sayı + delta indicator** (yukarı/aşağı %) tek satırda
- "Hazırlanacak" kartı kritik durumda **dikkat çekici renk değişimi** (subtle, parlak değil)
- Düşük stok için **mini progress bar** ("8/10 eşik")
- Kargo paneli için **kart-tarzı satırlar** (her kargo bir tile)
- Genel olarak: daha **havadar grid**, daha az "table density"

**Soru tasarımcıya:** Bu dashboard sabah ilk açılan ekran. Kullanıcı kahvesini içerken bakacak. "İlk 10 saniyede ne öğrenmeli?"

### 8.2 Sipariş Listesi (`/orders`)

**Amaç:** Filtreli tablo. Durum filtreleri: tüm / pending / prepared / shipped / delivered.

**Mevcut:**
- Üst sağda 5 buton (filtre chip'leri)
- Tablo: # / Müşteri / Durum / Tutar / Tarih
- Tıklanan satır → drill-down

**Sorunlar:**
1. Filtre butonları **link tabanlı** (URL state) ama görünümleri net bir tab/segmented control değil. Hangi aktif belli ama "loading" yok.
2. Tablo zebra striping yok, çok satır olunca göz kayıyor.
3. **Sayfalama yok** — şu an `limit=50` hardcoded. 200 sipariş varsa eski olanlar görünmüyor.
4. **Arama** yok (sipariş #128 nasıl bulurum eğer hatırlıyorsam?).
5. Sütun sıralama yok.

**İstenen iyileştirme:**
- **Üst sağ arama kutusu** (#sipariş, müşteri adı)
- **Sayfalama veya virtualization** (load more)
- **Sütun sıralama** (tıklanabilir başlıklar)
- **Durum chip'leri** filtre kısmında sayaç göstersin (örn. "pending (8)", "shipped (15)")
- **Mevcut filtrenin** seçili görünümü daha net olsun

### 8.3 Sipariş Detay (`/orders/[id]`)

**Amaç:** Tek siparişin tüm bilgisi tek ekranda.

**Mevcut:**
```
[Üst başlık: sipariş #128, status badge sağda]
[Müşteri kartı (tek satır)]
[Sol: sipariş kalemleri tablosu]
[Sağ: kargo timeline]
```

**Sorunlar:**
1. **Aksiyon butonları yok** — durum güncellemek için endpoint var ama UI yok ("Hazırlandı olarak işaretle" gibi).
2. Müşteri kartı çok ince — telefon numarası ve isim arasında daha fazla görsel hierarchy gerekir.
3. Kargo timeline **dikey 5 dot** — yatay progress bar veya step indicator daha sezgisel olurdu.
4. Sipariş kalemleri tablosunda ürün resmi yok (varsa). Sadece text → görsel zayıf.
5. **Note** alanı modeli var ama UI'da hiç görünmüyor.

**İstenen iyileştirme:**
- **Sticky aksiyon bar** (sağ üst veya alt): "Hazırlandı", "Kargoya ver", "İptal et" butonları
- **Müşteri kartı tıklanabilir** olsun (müşteri detayına gitsin) + son sipariş sayısı/toplam harcama mini-KPI
- **Yatay kargo step indicator** (5 adımı yan yana, geçilen adımlar yeşil)
- **Map preview** (opsiyonel premium) — kargonun "İstanbul Anadolu Şubesi" konumu mini harita
- **Notes** sahiyse panele alt boşlukta gösterilsin

### 8.4 Ürünler (`/products`)

**Amaç:** 30 ürünün stok durumunu görmek, düşük olanları filtrelemek.

**Mevcut:**
- "Tümü / Düşük Stok" iki buton
- Tablo: Ürün / Birim / Stok / Eşik / Fiyat
- Düşük stok satırları kırmızımsı (`bg-rose-50`)

**Sorunlar:**
1. **Stok seviyesini görsel olarak hissetmek zor** — 50 kg ile 8 kg arasında sayısal fark dışında bir görsel yok.
2. **Stok ayarlama UI yok** — `PATCH /products/{id}/stock` endpoint var ama buton yok.
3. **Kategori veya gruplandırma** yok — 30 ürün düz liste, "süt ürünleri", "kuru gıda" gibi grup olabilir.
4. Arama kutusu yok.

**İstenen iyileştirme:**
- Her satırda **mini stok bar** (yeşil → sarı → kırmızı) eşiğe göre dolmuş
- **Inline stok düzenleme** (tıkla, düzenle, kaydet)
- **Kategori chip'leri** (top'ta filtre)
- **Arama** + **fiyat aralığı filtresi**

### 8.5 Müşteriler (`/customers` ve `/customers/[id]`)

**Liste sayfası mevcut durum:**
- Arama formu (üstte)
- Tablo: # / Ad / Telefon / Telegram ID

**Detay sayfası mevcut:**
- 3 KPI kartı (toplam sipariş, harcama, son sipariş)
- Sipariş geçmişi tablosu

**Sorunlar:**
1. Liste sayfası çok minimal — **toplam harcama**, **son sipariş tarihi** gibi sinyal yok (bu liste üstünden segment ayırmak imkansız).
2. Telegram ID `99999` gibi sayı — kullanıcı dostu değil, ya çıkar ya da "Bağlı/Bağlı değil" badge'i koy.
3. Detay sayfası KPI kartları minimal — **müşterinin favori ürünü**, **ortalama sepet** gibi insight yok.
4. **Müşteriyle iletişim** butonu yok — "Telegram'dan mesaj at" linki olabilir (`t.me/<bot>` veya direct chat).

**İstenen iyileştirme:**
- Liste sayfasında **toplam harcama** + **son aktivite** sütunları
- Telegram ID yerine ✅/❌ ikonu
- Detay sayfası: **müşteri profil header'ı** (avatar/initials, ad, telefon, bağlantı durumu yan yana)
- "Mesaj at" butonu (Telegram link)
- En sık aldığı 3 ürün kartı

### 8.6 AI Asistan (`/chat`)

**Amaç:** Doğal dilde sistem sorgusu — "Bu hafta Ayşe'den kaç sipariş geldi?" → cevap + tablo render.

**Mevcut:**
- Üstte başlık + bir tip
- Mesaj listesi (kullanıcı sağda koyu, asistan solda beyaz)
- Asistan mesajının altında dinamik veri render (`order_list`, `sales_summary`, `stock_overview`)
- Alt: input + Gönder butonu

**Sorunlar:**
1. **Boş ekran çok çıplak** — sadece "örnek soru" hint var, kullanıcı ne sorabileceğini bilmez.
2. **Suggested prompts** yok (chip'ler gibi: "Bugün gelen siparişler", "Bu hafta satış", "Düşük stok").
3. Mesaj balonu Telegram tarzı ama daha **business UX** havası olabilir (Linear copilot, Stripe Assistant gibi).
4. Render edilen tablo balonun **dışında** — görsel akış kesiliyor.
5. **Loading hali** sadece "Düşünüyorum..." metni — daha sofistike olmalı (skeleton/thinking indicator).
6. **Sohbet geçmişi kalıcı değil** — sayfa yenilerse kaybolur. Bu OK olabilir ama session içinde scrollback kaybolmamalı (şu an OK).

**İstenen iyileştirme:**
- **Empty state**: 3-4 öneri chip'i ("Bu hafta satış grafiği", "Düşük stoklar", "Ayşe'nin son siparişi", "Bugün acil siparişler") — tıklayınca otomatik gönderiyor.
- **Tek-seferlik onboarding tooltip** ("Doğal dilde sorabilirsiniz, sistem tüm veriye bakar")
- **Asistan balonu + data widget** entegre — balon altında değil, balon **içinde** veya kart bütünleşik
- **Streaming tarzı tipping indicator** (Linear/ChatGPT'deki gibi nokta animasyonu)
- Asistan mesajlarında "**Bu cevap nasıl üretildi?**" küçük link → tool çağrılarını gösteren expandable detay (transparency için, opsiyonel)

---

## 9. UX Akışları

### Akış 1: "Sabah brifingi" (en sık kullanım)

1. Yönetici browser'i açar → `/` (dashboard)
2. Üst kartlardan durumu kapar (5 saniye)
3. "Hazırlanacak: 8 (3 acil)" görür → kartı tıklar → `/orders?status=pending&urgent=1` (filtre)
4. Acil olan ilk siparişi tıklar → `/orders/123` (detay)
5. "Hazırlandı" butonuna basar → status değişir → toast bildirim → bir sonraki sipariş
6. Bittiğinde geri dönüş `/orders` → `/` (dashboard)

**Tasarım gereksinimi:** Bu akışta **breadcrumb** veya **back navigation** olmalı. Şu an kullanıcı `/orders/123`'ten dashboard'a dönmek için sidebar tıklıyor — verimsiz.

### Akış 2: "Müşteri sorgu" (orta sıklık)

1. Müşteri telefonla arar: "Sipariş #156 ne durumda?"
2. Yönetici `/orders/156` direkt URL'yi yazar veya sipariş listesinde arar
3. Detayı söyler, gerekirse kargo durumunu canlı kontrol eder (mock cargo auto-advance var)
4. Çağrı biter

**Tasarım gereksinimi:** `/orders` sayfasında **direkt # araması** (Cmd+K palette gibi olabilir, ambitious).

### Akış 3: "Hafta sonu raporu" (haftalık)

1. Pazar akşamı yönetici `/chat` açar
2. "Bu hafta toplam ne sattım?" yazar → tablo + grafik
3. "Hangi ürün öne çıktı?" → top products listesi
4. "Ayşe Yılmaz bu hafta?" → müşteri detayı

**Tasarım gereksinimi:** Chat'te **history**, ardı ardına sorularla derinleşen bir analiz akışı doğal hissetmeli.

---

## 10. Boş Durumlar (Empty States)

Her sayfa için **veri yok** durumu ne göstermeli:

| Sayfa | Boş durum | Mesaj örnek |
|-------|-----------|-------------|
| Dashboard | İlk kez kurulum, hiç sipariş yok | "Henüz sipariş yok. Telegram bot'unu kuralım." + CTA |
| Sipariş listesi | Filtre eşleşmedi | "Bu durumda sipariş yok." (sade) |
| Sipariş detay | 404 | "Bu sipariş bulunamadı." + geri dön linki |
| Ürünler | Hepsi stokta (`?low=1`) | "🌱 Tüm stoklarınız sağlıklı." (pozitif) |
| Müşteriler | Arama sonuçsuz | "'{q}' için sonuç yok." |
| Chat | İlk açılış | Önceki bölümdeki öneri chip'leri |

**Tasarım gereksinimi:** Boş durumlar **negative space** olmamalı — illustration veya icon + mesaj + opsiyonel CTA.

---

## 11. Hata Durumları

- **API down:** "Sistem'e ulaşılamadı." + retry butonu
- **401 / unauthorized:** "Oturumunuz sona erdi." + login redirect (login UI henüz yok, ama placeholder olabilir)
- **Form validation:** Inline error mesaj (alttaki açıklama satırı)
- **Toast for transient:** "Sipariş güncellendi" / "Hata: {msg}"

---

## 12. Responsive

**Birinci öncelik: 1280px+ desktop**

**Sekiz öncelik: 768-1280px tablet**
- Sidebar collapse'a girer (icon-only veya off-canvas)
- Dashboard 4-up kartlar 2x2 olur
- Sipariş detay sol/sağ panel alt alta gelir

**Üçüncü öncelik (do-not-break, optimize-not-needed): 375-768px mobil**
- Sidebar hamburger
- Tüm tablolar horizontal scroll kabul edilebilir
- Chat sayfası mobil için en kritik (operatör yolda da bot'a soru sorabilir)

---

## 13. Erişilebilirlik (a11y)

- **Renk kontrast oranı:** AA (4.5:1 metin) standartı zorunlu — özellikle `text-slate-500` arka planda kontrol et
- **Focus states:** Tüm interactive elementlerde net focus ring (Tailwind `ring-2 ring-brand-500`)
- **Keyboard navigation:** Tab order doğal, modal'lar trap focus
- **ARIA:** Tablolarda doğru rol/header, badge'lerde aria-label
- **Türkçe ekran okuyucu:** "ş", "ğ" karakterleri sorunsuz okunur (font seçiminde önemli)

---

## 14. Priority Listesi

Tasarımcı bütün liste için zaman ayıramazsa öncelik:

**P0 — Demo öncesi mutlaka:**
- Dashboard summary cards yeniden tasarımı (ilk izlenim)
- Sipariş detay sayfası (jüri buraya bakacak)
- Chat sayfası boş durum + öneri chip'leri

**P1 — Demo cilası:**
- Empty states (her sayfa)
- Loading skeletons
- Toast notifications
- Yatay shipment timeline

**P2 — Sonraki sürüm:**
- Dark mode
- Cmd+K palette
- Mobile optimization
- Müşteri detay zenginleştirme

---

## 15. Tasarım Çıktısı Beklentisi

Claude Design'dan istediğin şekilde **birden çok format** seçilebilir. Spesifik isteğini şöyle yapılandır:

### Seçenek A: Yüksek seviye yön

> "Yukarıdaki brief'i okuyup, **Dashboard** sayfası için 3 farklı tasarım yön önerisi sun. Her birinde tipografi, palet, layout temel kararlarını açıkla. ASCII mockup ya da bileşen listesi yeterli."

### Seçenek B: Spesifik bileşen tasarımı

> "Şu mevcut bileşen kodunu paylaşıyorum: `SummaryCards.tsx`. Bunu yukarıdaki brief'e göre yeniden yaz, tek dosya halinde, Tailwind classes ile. Mevcut interface'i koru (props aynı)."

### Seçenek C: Tam mockup üretimi (görsel)

> "Brief'in 8.1, 8.3, 8.6 bölümlerinde tarif edilen sayfaların **hi-fi mockup'ları**nı üret. PNG veya Figma frame referansı yerine, **JSX kod halinde** üret — ben Next.js projeme drop edebilirim."

### Seçenek D: Tasarım sistemi tabanı

> "Brief'i temel alarak `tailwind.config.ts` palet genişletmesi + 4-5 yeniden kullanılabilir component (Card, Button, Badge, EmptyState, Toast) üret. Her birinin kullanım örneği ile."

---

## 16. Kısıtlamalar

Bunlar değişemez, tasarım bu kısıtların etrafında çalışmalı:

- **Tech stack:** Next.js 14 App Router + Tailwind. shadcn/ui *eklenebilir* ama zorunlu değil.
- **Backend kontratı:** REST endpoint'ler ve response formatları **dondu** (`app/schemas/*.py`). UI bu JSON'a göre çalışacak — yapı değişmek istiyorsa not düş, backend de güncelleriz.
- **Türkçe locale:** `Intl.NumberFormat("tr-TR", ...)` ve `Intl.DateTimeFormat("tr-TR", ...)` kullanılıyor. Para birimi TRY. Tarih format örnek: "12 May 2026 14:30".
- **No auth UI:** Şu an `NEXT_PUBLIC_ADMIN_TOKEN` env'de — login sayfası planı yok ama placeholder eklemek tasarım kararı, yapabilir.

---

## 17. Bilgi Mimarisi (Sitemap)

```
/                           Dashboard (varsayilan)
├── /orders                 Sipariş listesi
│   ├── ?status=pending     Filtre query
│   ├── ?status=shipped
│   ├── ?status=delivered
│   └── /orders/[id]        Detay
├── /products
│   └── ?low=1              Düşük stok filtresi
├── /customers
│   ├── ?q=...              Arama
│   └── /customers/[id]     Detay + sipariş geçmişi
└── /chat                   AI Asistan
```

Gelecekteki sayfalar (brief'te yer ayır):
- `/login` — auth sayfası
- `/settings` — env, API anahtarları, kullanıcı tercihleri
- `/reports` — haftalık/aylık özet (NL chat'in dışında)

---

## 18. Test İçeriği (Seed Data Referansı)

Tasarım mockup'larında **gerçek görünümlü** veri kullanmak için:

**Ürünler:** Bal, Zeytinyağı, Domates, Biber, Salça, Reçel, Peynir, Yoğurt, Tereyağı, Yumurta (devamı 30'a kadar — `app/db/seed.py:PRODUCT_CATALOG`).

**Müşteriler:** Ayşe Yılmaz, Mehmet Kaya, Fatma Demir, Ahmet Şahin, Zeynep Çelik vb. (50 adet — `app/db/seed.py:CUSTOMER_NAMES`).

**Demo sipariş:** #128, müşteri Ayşe Yılmaz, durum SHIPPED, kargo IN_TRANSIT, lokasyon "İstanbul Anadolu Şubesi", ETA yarın.

**Düşük stok demo:** Bal (8 kg, eşik 10), Domates (49 kg, eşik 30) — Bal kritik, Domates yakın.

**Kargo lokasyonları:** Ankara Aktarma, İstanbul Anadolu Şubesi, İstanbul Avrupa Şubesi, İzmir Dağıtım, Bursa Şubesi, Adana Aktarma, Antalya Şubesi.

---

## 19. Brief Sonu Notu

Bu doküman **canlı bir spec**. Tasarımcı kararlar verdikçe geri dön ve güncelle.

Tasarım sonuçları geldiğinde:

1. **Mockup/kod'u** önce `frontend/components/` altına bir alt klasörde **paralel** tut (örn. `frontend/components/dashboard-v2/`)
2. Mevcut sayfayı sıfırla değil, yan yana geliştir → demo gününde **A/B karşılaştırma** mümkün olsun
3. Tasarımcı önerilerinin hangisini benimsediğin **ADR** olarak `docs/decisions/` altına yaz (gelecek için referans)

**Sorular varsa:** Brief'i tarayan tasarımcı şu üçü mutlaka teyit etsin:
- Hedef kullanıcı yaş/teknik seviyesi (Bölüm 1)
- Marka tonu — sıcak vs profesyonel dengesi (Bölüm 2)
- Renk palet değişmeli mi yoksa mevcut emerald sabit mi (Bölüm 4)
