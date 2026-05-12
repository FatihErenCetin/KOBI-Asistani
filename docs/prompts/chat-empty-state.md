# Prompt: AI Asistan `ChatPanel` Empty State + Genel İyileştirme

> Bu dosyanın TAMAMINI Claude Design'a (veya başka bir UI üretici LLM'e) tek mesaj olarak yapıştır.
> Çıktı: tek dosya `frontend/components/chat/ChatPanel.tsx` drop-in replacement.

---

Sen kıdemli bir Next.js + Tailwind UI tasarımcısısın. Aşağıdaki tasarım brief'ini oku ve **`ChatPanel.tsx` bileşenini yeniden yaz** — özellikle empty state'i ve mesaj balonlarını iyileştirerek.

## Kısıtlamalar (sıkı uy)

- **`"use client"` directive'i koru** (interaktif bileşen)
- Mevcut **state shape'i koru**: `Turn { role: "user" | "assistant", text, data? }`, `turns[]`, `input`, `busy`
- Mevcut **API çağrısı koru**: `api.panelChat(message)` → `{ text, data }`
- `RenderData` component'ini koru (data type'a göre `OrderListRender`, `SalesChart`, `StockOverviewRender` render eder) — bunu inline tut, ayrı dosyaya çıkarma
- Sadece Tailwind classes kullan; **yeni paket ekleme**
- `lucide-react` ikonları kullanabilirsin (zaten kurulu — örn. `Send, Sparkles, TrendingUp, Package, Users`)
- Tüm metinler Türkçe
- Tek dosya çıktı: `frontend/components/chat/ChatPanel.tsx` — drop-in replace
- **Açıklama yazma**, sadece kod blokunu döndür

## Hedefler (öncelik sırasıyla)

1. **Empty state**: şu an "Örnek: ..." tek satır var. Yerine:
   - Üstte küçük welcome message (icon + selamlama)
   - 4 adet **suggested prompt chip'i** (tıklanabilir, mesaj olarak gönderir)
   - Önerilen prompt'lar (kategorize edilmiş ikon'larla):
     - 📊 "Bu hafta satış grafiği" (sales_summary)
     - 📦 "Düşük stoklar" (stock_overview)
     - 👥 "Ayşe Yılmaz'ın son siparişi" (customer history)
     - ⚡ "Bugün acil siparişler" (list_orders pending urgent)
2. **Mesaj balonları daha business UX** havası — Telegram tarzı değil, Linear/Stripe Assistant tarzı:
   - User mesajı: sağa hizalı, koyu nötr (mevcut `bg-slate-900 text-white` korunabilir ama radius/padding zarif)
   - Assistant mesajı: sola hizalı, ince border, hafif shadow, **avatar/ikon yanında**
   - Assistant balonu + data widget **entegre** (data balonun alt tarafına kart içinde, görsel akış kesmesin)
3. **Loading indicator** "Düşünüyorum..." text yerine **3-dot pulsing** veya skeleton balon
4. **Form alanı (input + buton)** sticky alta yapışsın, daha "compose box" hissi (Linear/ChatGPT'deki gibi):
   - Input border kalın değil, focus'ta brand color
   - Send butonu icon (Send from lucide) + text yan yana
   - `Enter` ile gönder, `Shift+Enter` yeni satır (textarea'ya geçebilirsin ama auto-resize gerekirse single-line input kalabilir, kararı sen ver)

## Ürün Özeti

**Ürün:** Küçük/orta ölçekli işletmeler için Telegram tabanlı müşteri asistanı + yönetim paneli.

**Kullanıcı:** 35-55 yaş işletme sahibi. Pazar akşamı paneli açıp "Bu hafta ne sattım?" sorgusu yapacak. AI Asistan, **SQL bilmeden veri sorgulamanın doğal yolu**.

**Bu sayfa'nın yeri:** `/chat` route'unda full-page bileşen. Yan menüde "AI Asistan" link'i ile gelinir.

## Tasarım Vizyonu

Üç sıralı adjektif: **sakin, güvenilir, sıcak**.

**Referanslar:** Linear Copilot, Stripe Assistant, Notion AI, ChatGPT. Hava: profesyonel ama davetkar.

**Kaçınılacak:** Generic chatbot UI (büyük gradient header, bot mascot), Telegram clone, "ChatGPT klonu" hissi.

## Marka & Tonalite

- Resmi dil, 2. tekil ("siz")
- AI cevabı zaten backend'den geliyor (Türkçe, kibar) — sen sadece UI kalıbını tasarlıyorsun
- Welcome message örnek: "Doğal dilde sorabilirsiniz. Sistemdeki tüm veriye erişimim var." (kısa, davet edici)

## Renk Paleti (sabit)

```
brand-50:  #ecfdf5
brand-500: #10b981   ← suggested prompt chip border accent
brand-600: #059669   ← send buton bg, focus ring
brand-700: #047857
```

Yan tonlar: `slate-*` (nötr), `emerald-*` (success/accent).

**Suggested prompt chip'leri** için pastel/soft renkler kullanabilirsin (`bg-emerald-50`, `bg-blue-50`, `bg-amber-50` gibi) — kategoriye göre farklı tonlar.

## Tipografi

- System UI stack
- Mesaj metni: `text-sm` veya `text-[15px]` (okunabilir ama kompakt)
- Suggested chip'ler: `text-sm font-medium`
- Welcome message: `text-base`, biraz daha rahat satır aralığı

## Bu Sayfanın (AI Asistan) Detaylı Brief'i — Bölüm 8.6

**Mevcut sorunlar:**

1. **Boş ekran çok çıplak** — sadece "örnek soru" hint var, kullanıcı ne sorabileceğini bilmez
2. **Suggested prompts yok** (chip'ler gibi)
3. Mesaj balonu Telegram tarzı ama daha business UX havası olabilir
4. Render edilen tablo balonun **dışında** — görsel akış kesiliyor
5. **Loading hali** sadece "Düşünüyorum..." metni — daha sofistike olmalı

**İstenen iyileştirmeler:**

- **Empty state**: 4 öneri chip'i, tıklanınca otomatik gönderir
- **Tek-seferlik onboarding tooltip** (opsiyonel, atlanabilir) — "Doğal dilde sorabilirsiniz, sistem tüm veriye bakar"
- **Asistan balonu + data widget entegre** — balon altında değil, balon **içinde** veya kart bütünleşik
- **Streaming tarzı tipping indicator** (3-dot animasyon)

## UX Akış (referans için)

Pazar akşamı yönetici `/chat` açar:

1. **Açılış**: Welcome message + 4 öneri chip'i görür
2. "Bu hafta toplam ne sattım?" yazar → assistant cevap + sales chart
3. "Hangi ürün öne çıktı?" → top products listesi
4. "Ayşe Yılmaz bu hafta?" → müşteri detayı

Bu akışta sohbet **kümülatif bilgi** birikir — kullanıcı scroll back yapıp önceki cevaplara bakabilmeli. Şu an history sayfayı yenileyince kayboluyor (kabul edilebilir, mevcut behavior'u koru).

## Suggested Prompt Önerileri (öncelik)

Welcome state'te 4 chip:

| Chip | Prompt text (kullanıcı bunu görür) | API'ye gidecek mesaj | Beklenen tool |
|------|--------------------------------------|------------------------|---------------|
| 📊 | Bu hafta satış grafiği | "Bu hafta günlük satış grafiğini göster" | sales_summary |
| 📦 | Düşük stoklar | "Düşük stokta olan ürünleri listele" | stock_overview |
| 👥 | Ayşe Yılmaz'ın son siparişleri | "Ayşe Yılmaz'ın son siparişlerini göster" | customer_order_history |
| ⚡ | Bekleyen acil siparişler | "Bekleyen acil siparişleri listele" | list_orders |

Chip'in `onClick` davranışı: `input` state'ine prompt text'ini set et + `send()` çağır (kullanıcı butona basmadan direkt gönder).

## Responsive

- **Desktop**: full width, max-w-4xl ortalanmış (üst sayfada layout zaten yapıyor)
- **Tablet/mobil**: chip'ler 2x2 grid'e geçer, input bar sticky alt

## Erişibilirlik

- `<form>` semantik, Enter ile submit
- Loading sırasında `aria-busy="true"` mesaj listesinde
- Suggested chip'ler `<button>` semantik, klavye ile gezilebilir
- Focus ring `ring-2 ring-brand-500`
- Animasyonlar `prefers-reduced-motion` saygılı

## Tech Kısıtlamaları

- Next.js 14 App Router, **`"use client"` zorunlu** (state + interaktivite)
- Tailwind 3.4 — yeni paket ekleme
- **Mevcut import paths**: `@/lib/api`, `./OrderListRender`, `./SalesChart`, `./StockOverviewRender`, `lucide-react`

## Backend Kontratı (değişmez)

`api.panelChat(message)` döner:

```ts
{
  text: string,
  data: null | {
    type: "order_list" | "sales_summary" | "stock_overview",
    ...payload
  }
}
```

`RenderData` bunu `data.type`'a göre uygun child component'e geçirir. Bu mantığı koru.

## Test Verisi

Demo'da gerçek mesajlaşma örneği:

```
USER: "Bu hafta Ayşe Yılmaz'dan kaç sipariş geldi?"
ASSISTANT: { text: "Ayşe Yılmaz bu hafta 3 sipariş verdi, toplam 420 TL.",
             data: { type: "order_list", orders: [...] } }
```

Müşteri isimleri seed'de: Ayşe Yılmaz, Mehmet Kaya, Fatma Demir, Ahmet Şahin vs.

---

## Mevcut Kod (drop-in replace için referans)

`frontend/components/chat/ChatPanel.tsx`:

```tsx
"use client";
import { useState } from "react";

import { OrderListRender } from "./OrderListRender";
import { SalesChart } from "./SalesChart";
import { StockOverviewRender } from "./StockOverviewRender";
import { api } from "@/lib/api";

interface Turn {
  role: "user" | "assistant";
  text: string;
  data?: any;
}

function RenderData({ data }: { data: any }) {
  if (!data) return null;
  if (data.type === "order_list") return <OrderListRender data={data} />;
  if (data.type === "sales_summary") return <SalesChart data={data} />;
  if (data.type === "stock_overview") return <StockOverviewRender data={data} />;
  return null;
}

export function ChatPanel() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!input.trim() || busy) return;
    const userTurn: Turn = { role: "user", text: input };
    setTurns((t) => [...t, userTurn]);
    setInput("");
    setBusy(true);
    try {
      const resp = await api.panelChat(userTurn.text);
      setTurns((t) => [...t, { role: "assistant", text: resp.text, data: resp.data }]);
    } catch (e: any) {
      setTurns((t) => [...t, { role: "assistant", text: `Hata: ${e.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {turns.length === 0 && (
          <div className="text-slate-500 text-sm">
            Örnek: <em>&ldquo;Bu hafta Ayşe Yılmaz&apos;dan kaç sipariş geldi?&rdquo;</em>
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "text-right" : ""}>
            <div
              className={`inline-block max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                t.role === "user"
                  ? "bg-slate-900 text-white"
                  : "bg-white border border-slate-200"
              }`}
            >
              {t.text}
            </div>
            {t.role === "assistant" && t.data && (
              <div className="mt-2 max-w-[80%]">
                <RenderData data={t.data} />
              </div>
            )}
          </div>
        ))}
        {busy && <p className="text-sm text-slate-400">Düşünüyorum...</p>}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Doğal dilde sor..."
          className="flex-1 border border-slate-300 rounded px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={busy}
          className="px-4 py-2 bg-brand-600 text-white rounded text-sm disabled:opacity-50"
        >
          Gönder
        </button>
      </form>
    </div>
  );
}
```

## Dependency Bileşenler (bilgi için — değiştirmeyeceksin)

`OrderListRender`, `SalesChart`, `StockOverviewRender` import edilen 3 child component, mevcut kalacak. Kontratları:

- **OrderListRender** props: `{ data: { orders: [{order_id, customer_name, status, total, created_at}] } }`
- **SalesChart** props: `{ data: { rows: [{day, revenue, order_count}] | [{product, revenue, quantity}], group_by: "day"|"product" } }`
- **StockOverviewRender** props: `{ data: { products: [{id, name, stock, unit, is_low}] } }`

## Çıktı

Sadece yeni `ChatPanel.tsx` dosyasının tam içeriği. Açıklama yazma, kod blok dışında metin verme.
