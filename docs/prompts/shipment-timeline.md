# Prompt: Sipariş Detay `ShipmentTimeline` Yeniden Tasarım

> Bu dosyanın TAMAMINI Claude Design'a (veya başka bir UI üretici LLM'e) tek mesaj olarak yapıştır.
> Çıktı: tek dosya `frontend/components/orders/ShipmentTimeline.tsx` drop-in replacement.

---

Sen kıdemli bir Next.js + Tailwind UI tasarımcısısın. Aşağıdaki tasarım brief'ini oku ve **`ShipmentTimeline.tsx` bileşenini yeniden yaz**.

## Kısıtlamalar (sıkı uy)

- Props interface'i **aynı kalsın**: `shipment: { tracking_no, carrier, status, current_location, estimated_delivery } | null`
- `status` değerleri: `"label_created" | "picked_up" | "in_transit" | "out_for_delivery" | "delivered"`
- Sadece Tailwind classes kullan; **yeni paket ekleme**
- `lucide-react` ikonları kullanabilirsin (zaten kurulu — örn. `Package, Truck, MapPin, CheckCircle2, Clock`)
- `formatDate` ve `statusLabel` helper'larını `@/lib/format` üzerinden import et (zaten var)
- Tüm metinler Türkçe
- Tek dosya çıktı: `frontend/components/orders/ShipmentTimeline.tsx` — drop-in replace
- **Açıklama yazma**, sadece kod blokunu döndür

## Hedefler (öncelik sırasıyla)

1. **Mevcut dikey 5 dot** zayıf — bunu daha sezgisel bir görsel'e çevir. Önerilen yön: **yatay step indicator** (5 aşama yan yana, geçilen adımlar yeşil, aktif adım büyük ve animasyonlu, sonraki adımlar soluk)
2. **Aktif adım vurgulansın** — kullanıcı "şu an neredeyiz" sorusuna 2 saniyede cevap bulmalı
3. **Konum + ETA** bilgileri timeline'ın hemen altında, görsel ağırlıkta — şu an çok küçük
4. **Kargo numarası + carrier** üst satırda, monospace ama küçük gri
5. **Empty state** (`shipment === null`): "kargo bilgisi yok" yerine "Bu sipariş henüz kargoya verilmedi" gibi spesifik mesaj + minimal illustration veya ikon

## Ürün Özeti

**Ürün:** Küçük/orta ölçekli işletmeler için Telegram tabanlı müşteri asistanı + yönetim paneli.

**Kullanıcı:** 35-55 yaş işletme sahibi. Müşteri telefonla arıyor: "Sipariş #128 nerede?" — yönetici 3 saniyede cevap vermeli.

**Bu bileşenin yeri:** Sipariş detay sayfası (`/orders/[id]`), sağ kolonda. Sayfanın "wow" momenti. Jüri buraya bakacak.

## Tasarım Vizyonu

Üç sıralı adjektif: **sakin, güvenilir, sıcak**.

**Referanslar:** Linear, Stripe Dashboard, Notion. Hava: "Stripe + Hey.com'un çocuğu, tarımda büyümüş."

**Kaçınılacak:** Aşırı animasyon, gradient yağmuru, "tracking app" parodisi.

## Marka & Tonalite

- Resmi dil, 2. tekil ("siz")
- Mikrocopy örnek: ✅ "İstanbul Anadolu Şubesi'nde, yarın teslim edilecek" (somut)
- Tarih formatı: `tr-TR` locale, örn. "13 May 2026"

## Renk Paleti (sabit)

```
brand-50:  #ecfdf5
brand-500: #10b981   ← aktif/tamamlanmış adımlar
brand-600: #059669
brand-700: #047857
```

Yan tonlar: `slate-*` (henüz ulaşılmamış adımlar, nötr text), `emerald-*` (success), `amber-*` (bekliyor).

**emerald paleti korunmalı.** Active step için subtle pulse animasyonu kabul (Tailwind `animate-pulse` ile).

## Tipografi

- System UI stack
- Tracking number için `font-mono`
- Status label'lar: `font-medium`, kompakt
- Konum (`current_location`) `font-semibold` çünkü en sık aranan bilgi

## Bu Sayfanın (Sipariş Detay) Detaylı Brief'i — Bölüm 8.3

**Amaç:** Tek siparişin tüm bilgisi tek ekranda.

**Bu bileşenle ilgili sorunlar:**

1. Kargo timeline **dikey 5 dot** — yatay progress bar veya step indicator daha sezgisel
2. Konum ve ETA çok küçük — kullanıcı **konum + saat**'e odaklanmalı

**İstenen iyileşmeler (bu bileşene özgü):**

- **Yatay step indicator**: 5 adımı yan yana, geçilen adımlar yeşil dolu daire, aktif adım daha büyük ve subtle pulse, sonraki adımlar boş daire + soluk text
- Adımlar arasında **çizgi/connector** — geçilen kısım yeşil, gelmeyen kısım slate-200
- **Aktif adım altında**: konum + ETA, görsel olarak vurgulu (örn. küçük kart veya beyaz çerçeveli alan)
- **Map preview gerekirse:** opsiyonel, atlanabilir. Şehir adı yeterli.

## Step Mapping (Türkçe label'lar)

```
label_created     → "Etiket Oluşturuldu"
picked_up         → "Teslim Alındı"
in_transit        → "Yolda"
out_for_delivery  → "Dağıtımda"
delivered         → "Teslim Edildi"
```

`statusLabel(status)` helper bunu zaten yapıyor.

## Empty State

`shipment === null` durumu: sipariş kargoya verilmemiş (status: pending/prepared) demek. Boş satır yerine:

- Sade bir kart: ikon (Package outline) + "Bu sipariş henüz kargoya verilmedi" + (opsiyonel) "Sipariş durumunu güncelleyince kargo bilgisi burada görünür"

## Responsive

- **Desktop**: yatay step indicator full width
- **Tablet/mobil**: step indicator yine yatay ama label'lar kısalır veya ikon-only fallback (ARIA label ile)

## Erişilebilirlik

- Step indicator için `<ol>` + `aria-current="step"` aktif step'te
- Sadece renkle değil **ikon + text** ile durumu belirt (renk körü kullanıcılar)
- Animasyon `prefers-reduced-motion` saygı göstermeli (animate-pulse'ı koşullu uygula)

## Tech Kısıtlamaları

- Next.js 14 App Router (Server Component kalabilir — interaktivite yok)
- Tailwind 3.4 — yeni paket ekleme
- **Mevcut import paths**: `@/lib/format`, `lucide-react`

## Test Verisi (mockup'ta gerçek görünümlü)

Demo seed'de **Sipariş #128** şu kargoya sahip:

```js
shipment = {
  tracking_no: "TRABC1234XY",
  carrier: "MockKargo",
  status: "in_transit",                     // aktif adım: "Yolda"
  current_location: "Istanbul Anadolu Subesi",
  estimated_delivery: "2026-05-13",         // bir gün sonrası (ETA)
}
```

Diğer demo değerler için kargo konumları arasında rotasyon yapılır:

```
Ankara Aktarma, Istanbul Anadolu Subesi, Istanbul Avrupa Subesi,
Izmir Dagitim, Bursa Subesi, Adana Aktarma, Antalya Subesi
```

---

## Mevcut Kod (drop-in replace için referans)

`frontend/components/orders/ShipmentTimeline.tsx`:

```tsx
import { formatDate, statusLabel } from "@/lib/format";

const STAGES = [
  "label_created",
  "picked_up",
  "in_transit",
  "out_for_delivery",
  "delivered",
];

interface Shipment {
  tracking_no: string;
  carrier: string;
  status: string;
  current_location: string | null;
  estimated_delivery: string | null;
}

export function ShipmentTimeline({ shipment }: { shipment: Shipment | null }) {
  if (!shipment) {
    return <p className="text-sm text-slate-500">Bu sipariş için kargo bilgisi yok.</p>;
  }
  const currentIdx = STAGES.indexOf(shipment.status);
  return (
    <div>
      <p className="text-xs text-slate-500 mb-2">
        {shipment.carrier} • <span className="font-mono">{shipment.tracking_no}</span>
      </p>
      <ol className="space-y-2">
        {STAGES.map((stage, idx) => {
          const reached = idx <= currentIdx;
          return (
            <li key={stage} className="flex items-center gap-3 text-sm">
              <span
                className={`h-3 w-3 rounded-full ${reached ? "bg-brand-500" : "bg-slate-300"}`}
              />
              <span className={reached ? "" : "text-slate-400"}>{statusLabel(stage)}</span>
            </li>
          );
        })}
      </ol>
      <p className="text-sm mt-3">
        Konum: <span className="font-medium">{shipment.current_location ?? "—"}</span>
      </p>
      <p className="text-sm">ETA: {formatDate(shipment.estimated_delivery)}</p>
    </div>
  );
}
```

## Yardımcı Helper'lar (zaten mevcut, sadece import et)

`@/lib/format`'tan:

```ts
formatDate(input: string | Date | null | undefined): string  // "13 May 2026" formatı
statusLabel(status: string): string  // tüm status değerleri için Türkçe label
```

## Çıktı

Sadece yeni `ShipmentTimeline.tsx` dosyasının tam içeriği. Açıklama yazma, kod blok dışında metin verme.
