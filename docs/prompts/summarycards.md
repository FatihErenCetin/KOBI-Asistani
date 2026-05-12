# Prompt: Dashboard `SummaryCards` Yeniden Tasarım

> Bu dosyanın TAMAMINI Claude Design'a (veya başka bir UI üretici LLM'e) tek mesaj olarak yapıştır.
> Çıktı: tek dosya `frontend/components/dashboard/SummaryCards.tsx` drop-in replacement.

---

Sen kıdemli bir Next.js + Tailwind UI tasarımcısısın. Aşağıdaki tasarım brief'ini oku ve **`SummaryCards.tsx` bileşenini yeniden yaz**.

## Kısıtlamalar (sıkı uy)

- Props interface'i **aynı kalsın**: `summary: { orders_last_24h, revenue_last_24h, orders_vs_yesterday_pct, pending_to_prepare, urgent_today, shipments_today, low_stock_count }`
- Sadece Tailwind classes kullan; **yeni paket ekleme**
- `lucide-react` ikonları kullanabilirsin (zaten kurulu — örn. `Package, AlertTriangle, Truck, TrendingUp, TrendingDown`)
- `formatTRY` helper'ını `@/lib/format` üzerinden import et (zaten var)
- Tüm metinler Türkçe
- Sayılar için `tabular-nums` class
- Tek dosya çıktı: `frontend/components/dashboard/SummaryCards.tsx` — drop-in replace
- **Açıklama yazma**, sadece kod blokunu döndür

## Hedefler (öncelik sırasıyla)

1. **"Hazırlanacak" kartı** `urgent_today > 0` ise dikkat çekici olsun (subtle, parlak değil — örn. ince renk şeridi, ikon vurgusu)
2. **"Düşük stok" kartında** mini progress bar veya sayısal+görsel sinyal birlikte
3. **Her kartta**: ikon + ana sayı + delta indicator (yukarı/aşağı %, varsa)
4. **4 kart aynı görünmesin**; bilgi hiyerarşisi olsun — kullanıcı 5 saniyede hangi karta öncelik vermesi gerektiğini anlasın
5. **Sub-text gözden kaçmasın** — şu an `text-slate-600` çok sönük

---

## Ürün Özeti

**Ürün:** Küçük/orta ölçekli işletmeler (KOBİ) ve tarım kooperatifleri için Telegram tabanlı müşteri asistanı + yönetim paneli.

**Kullanıcı:** 35-55 yaş, teknik altyapı eğitimi olmayan işletme sahibi. Günde 10-100 sipariş işliyor. Sabah ofisi açar açmaz panele bakar, kahve içerken durumu kavrar.

**Cihaz:** Birincil olarak desktop (1280px+). Tablet ikincil. Mobil ihmal edilebilir.

**Bu bileşenin yeri:** Dashboard sayfası (`/`), en üstte 4-up grid. Sayfayı açan kullanıcının **ilk gördüğü şey** bu kartlar.

## Tasarım Vizyonu

Üç sıralı adjektif:

1. **Sakin (calm):** Yönetici telefon, müşteri, kargo arasında panik içinde. Panel ferahlık sunmalı; göz yormamalı.
2. **Güvenilir (trustworthy):** Finansal veri. Saçma renkler, gereksiz animasyon, deneysel layout yok.
3. **Sıcak (warm):** Soğuk SaaS değil — kooperatif teması, toprak/yeşil çağrışımları.

**Referanslar:** Linear, Stripe Dashboard, Notion. Hava: "Stripe + Hey.com'un çocuğu, tarımda büyümüş."

**Kaçınılacak:** Banka panelleri (soğuk), Salesforce (info overload), B2C Shopify (satışçı).

## Marka & Tonalite

- Resmi dil, 2. tekil ("siz") kullanıcıya
- Mikrocopy örnek: ✅ "Bugün teslim edilecek 5 kargo var" (somut), ❌ "Aktif lojistik operasyonları" (kurumsalca)
- Para birimi TRY, format `tr-TR` locale

## Renk Paleti (sabit)

`tailwind.config.ts` şu palet:

```
brand-50:  #ecfdf5  (çok açık emerald, background highlight)
brand-500: #10b981  (ana yeşil, vurgu)
brand-600: #059669  (CTA, link)
brand-700: #047857  (hover)
```

Yan tonlar: `slate-*` (nötr gri), `amber-*` (uyarı), `rose-*` (kritik), `emerald-*` (başarı), `indigo-*` (info).

**emerald paleti korunmalı.** Status badge'ler için Tailwind tonları kullanabilirsin. Accent için terracotta veya hardal sarı opsiyonu da deneyebilirsin ama brand emerald birincil kalsın.

## Tipografi

- System UI stack
- Sayılar için **`tabular-nums`** ON (kartlar arasında sayılar hizalanmalı)
- Hiyerarşi: H1 → H2 → body → caption
- Türkçe karakterleri (ş, ç, ğ, İ) iyi desteklemeli

## Bu Sayfanın (Dashboard) Detaylı Brief'i — Bölüm 8.1

**Amaç:** Yönetici paneli açar açmaz son 24 saatin ve bugün yapılması gerekenlerin tam görünümü.

**Mevcut sorunlar:**

1. **4 kart aynı görünüyor** — hangi karta öncelik vermeli kullanıcı anlamıyor. "Acil" göstergeleri yok.
2. Kartlardaki ikinci satır (alt sub-text) çok sönük, gözden kaçıyor.
3. "Hazırlanacak" kartında "acil bugün" sayısı kritikse de tıklanabilir değil — drill-down'a link olmalı (`/orders?status=pending`).
4. Düşük stok listesi sıradan — bar/gauge ile "ne kadar düşük" hissedilmiyor.

**İstenen iyileştirme:**

- Kartlarda **ikon + sayı + delta indicator** (yukarı/aşağı %) tek satırda
- "Hazırlanacak" kartı kritik durumda **dikkat çekici renk değişimi** (subtle, parlak değil)
- Düşük stok için **mini progress bar** veya görsel sinyal ("Bal: 8/10 eşik" gibi düşünebilirsin ama summary'de detay yok — bu kartta sadece toplam sayı var, ama görsel olarak "biriken kritik" hissi olsun)
- Genel olarak: daha **havadar grid**, daha az "table density"
- Kartlar `<a>` veya `<Link>` ile drill-down'a yönlendirilsin (Next.js `next/link` kullan)

**Drill-down hedefleri:**

- "Son 24 saat" kartı → `/orders?since=24h` (henüz route yok ama placeholder ekle, sadece `/orders` linkleyebilirsin)
- "Hazırlanacak" kartı → `/orders?status=pending`
- "Bugün teslim" kartı → `/orders?status=shipped`
- "Düşük stok" kartı → `/products?low=1`

## Empty State

Dashboard tamamen boş ise (ilk kurulum): kart sayıları 0 olur. Bu durumda bile kartlar görünür kalsın; "henüz veri yok" gibi mesaj **gerek yok** — sayıların kendisi (0) yeterli sinyal.

## Responsive

- **1280px+ desktop**: 4 kart yan yana (mevcut)
- **768-1280px tablet**: 2x2 grid
- **<768px mobil**: 1 sütun, dikey stack

## Erişilebilirlik

- AA kontrast (4.5:1) — `text-slate-500` ve sub-text'leri kontrol et
- Tüm kart link'leri klavye ile erişilebilir + focus ring (`ring-2 ring-brand-500`)
- ikonlara `aria-hidden` (decorative) veya `aria-label` ver
- Status değişikliği (örn. urgent kart kırmızı oldu) sadece renkle değil **ikon/text ile** belirt

## Tech Kısıtlamaları

- Next.js 14 App Router (Server Components varsayılan; bu bileşen interaktif değil, server component kalabilir)
- Tailwind 3.4 — yeni paket ekleme
- **Mevcut import paths**: `@/lib/format`, `lucide-react`
- Türkçe locale `Intl.NumberFormat("tr-TR", ...)` (formatTRY helper'ı kullan)

## Test Verisi (mockup'ta gerçek görünümlü)

Demo seed'de şu değerler var:

```js
summary = {
  orders_last_24h: 2,
  revenue_last_24h: 3347.0,
  orders_vs_yesterday_pct: 30.3,  // pozitif değer = artış
  pending_to_prepare: 48,
  urgent_today: 48,
  shipments_today: 0,
  low_stock_count: 1,
}
```

(Demo'da sadece "Bal" düşük stokta: 8/10 kg. Bu summary view'da görünmüyor, sadece sayı 1. Detay `/products?low=1`'de.)

---

## Mevcut Kod (drop-in replace için referans)

`frontend/components/dashboard/SummaryCards.tsx`:

```tsx
import { formatTRY } from "@/lib/format";

interface Summary {
  orders_last_24h: number;
  revenue_last_24h: number;
  orders_vs_yesterday_pct: number;
  pending_to_prepare: number;
  urgent_today: number;
  shipments_today: number;
  low_stock_count: number;
}

export function SummaryCards({ summary }: { summary: Summary }) {
  const pctSign = summary.orders_vs_yesterday_pct >= 0 ? "▲" : "▼";
  const cards = [
    {
      title: "Son 24 saat",
      main: `${summary.orders_last_24h} sipariş`,
      sub: `${formatTRY(summary.revenue_last_24h)} • ${pctSign} %${Math.abs(summary.orders_vs_yesterday_pct)}`,
      tone: "bg-white",
    },
    {
      title: "Hazırlanacak",
      main: `${summary.pending_to_prepare}`,
      sub: `${summary.urgent_today} acil bugün`,
      tone: summary.urgent_today > 0 ? "bg-amber-50 border-amber-200" : "bg-white",
    },
    {
      title: "Bugün teslim",
      main: `${summary.shipments_today} kargo`,
      sub: "Aktif kargolar",
      tone: "bg-white",
    },
    {
      title: "Düşük stok",
      main: `${summary.low_stock_count}`,
      sub: summary.low_stock_count > 0 ? "Eşik altında" : "Hepsi iyi",
      tone: summary.low_stock_count > 0 ? "bg-rose-50 border-rose-200" : "bg-white",
    },
  ];
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {cards.map((c) => (
        <div key={c.title} className={`rounded-lg border border-slate-200 p-5 ${c.tone}`}>
          <p className="text-xs uppercase tracking-wider text-slate-500">{c.title}</p>
          <p className="text-2xl font-semibold mt-1">{c.main}</p>
          <p className="text-sm text-slate-600 mt-1">{c.sub}</p>
        </div>
      ))}
    </div>
  );
}
```

## Yardımcı Helper'lar (zaten mevcut, sadece import et)

`@/lib/format`'tan:

```ts
formatTRY(amount: number): string  // "₺1.250,50" formatı
```

## Çıktı

Sadece yeni `SummaryCards.tsx` dosyasının tam içeriği. Açıklama yazma, kod blok dışında metin verme.
