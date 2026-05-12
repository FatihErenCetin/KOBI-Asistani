# Prompt: AI Asistan `ChatPanel` — Persistent Chips + History Sidebar v2

> Bu dosyanın TAMAMINI Claude Design'a tek mesaj olarak yapıştır.
> Çıktı: `frontend/components/chat/ChatPanel.tsx` drop-in replacement (history sidebar dahil inline veya küçük helper component'lerle aynı dosya içinde).

---

Sen kıdemli bir Next.js + Tailwind UI tasarımcısısın. Aşağıdaki tasarım brief'ini oku ve **`ChatPanel.tsx` bileşenini yeniden yaz**. Bu **v2** versiyondur — mevcut bileşen zaten welcome state + suggested chip'leri içeriyor; bu iterasyonda **3 yeni özellik** eklemen gerek.

## v2 Yeni Özellikler (zorunlu)

### A. Suggested chip'ler her zaman erişilebilir

Mevcut tasarımda chip'ler sadece **empty state**'te görünüyor. Kullanıcı ilk mesajı atınca chip'ler kayboluyor.

**Yeni davranış:** Chip'ler **input bar'ın hemen üstünde** kompakt bir şerit olarak **kalıcı** kalsın (sticky). Empty state'te büyük kart'lar + altta kompakt şerit; konuşma başlayınca büyük kartlar kaybolur ama kompakt şerit kalır.

- Empty state chip'leri: 2x2 grid, iconlu büyük kartlar (mevcut)
- Konuşma başlayınca: input'un hemen üzerinde **tek satır horizontal scroll** chip'leri (yatay kaydırılabilir, telefon stickers gibi)
- Aynı 4 prompt; ama compact varyant daha küçük (`text-xs px-3 py-1.5 rounded-full`)

### B. Sol tarafta Chat History Sidebar

`/chat` sayfasına geldiğinde **sayfanın sol tarafında** (ana app sidebar'ı **yanında**, ana içerikten önce) yeni bir history panel görünmeli:

- **Genişlik:** ~260px (tablet'te collapse'a düşer)
- **Üstte "+ Yeni Sohbet" butonu**
- Altında **geçmiş sohbet listesi** — her satır:
  - Başlık: ilk kullanıcı mesajının ilk 40 karakteri
  - Alt satır: relative time ("2 saat önce", "dün")
  - Hover state, aktif sohbet vurgulu
  - Sağ tarafta küçük `×` ikonu — tek sohbeti silme
- **Boş history:** "Henüz sohbet yok" + minimal illustration veya ikon
- Sidebar'ın **kendi scroll'u** olmalı; ana içerik scroll'undan bağımsız

### C. Türkçe karakter beklentisi (bilgi)

Backend (panel_persona.md) Türkçe karakterleri (ş, ç, ğ, ü, ö, ı, İ) kullanmaya zorlanacak. UI tarafında **hiçbir karakter dönüşümü yapma** — backend'den ne gelirse aynen render et. Sadece UI'da kendi yazdığın label/placeholder/welcome text'lerde Türkçe karakter eksiksiz olsun:

- ❌ "Dusuk stoklar"
- ✅ "Düşük stoklar"

## Persistence (localStorage)

Chat history için **backend gerekmiyor**, frontend-only çözüm:

```ts
// localStorage key: "kobi-chat-conversations"
type Conversation = {
  id: string;          // crypto.randomUUID()
  title: string;       // ilk kullanıcı mesajının ilk 40 karakteri
  turns: Turn[];
  created_at: string;  // ISO
  updated_at: string;  // ISO
};
```

**Davranış:**
- Sayfa yüklenince `localStorage.getItem("kobi-chat-conversations")` okur, listeyi sidebar'a doldurur
- Aktif sohbet ID'si bir state'te tutulur — yoksa "yeni sohbet" durumu (empty state)
- Kullanıcı mesaj atınca:
  - Eğer aktif sohbet yoksa yeni `Conversation` yaratılır, title = ilk mesajın ilk 40 char
  - Mevcut conversation `turns` array'i güncellenir
  - `updated_at` yenilenir
  - localStorage'a tamamı serialize edilir
- "+ Yeni Sohbet" → aktif ID null, turns state boşalır, empty state görünür
- Sidebar'da bir sohbete tıklanınca → aktif ID set, turns o sohbetin turns'ünden yüklenir
- Sohbet silme → confirm dialog (`window.confirm` yeterli, ek lib yok), localStorage'dan kaldır

**Edge case:** SSR sırasında localStorage yok → `useEffect` içinde okumalısın, ilk render boş list.

## Kısıtlamalar (sıkı uy)

- **`"use client"` directive'i koru**
- **Backend kontratı değişmez**: `api.panelChat(message)` → `{ text, data }`
- **Child component'ler değişmez**: `OrderListRender`, `SalesChart`, `StockOverviewRender` import'ları korunur
- `RenderData` mevcut mantıkla devam — `data.type`'a göre child'ı seç
- Sadece Tailwind classes kullan; **yeni paket ekleme**
- `lucide-react` ikonları kullanabilirsin (zaten kurulu — `MessageSquarePlus, Trash2, Send, Sparkles, TrendingUp, Package, Users, Zap, Clock` vb.)
- Tüm UI metinleri Türkçe (Türkçe karakterleri tam kullan)
- Tek dosya çıktı: `frontend/components/chat/ChatPanel.tsx`
- **Açıklama yazma**, sadece kod blokunu döndür

## Mevcut Sayfa Yapısı (referans)

`frontend/app/chat/page.tsx` (DEĞİŞMEYECEK):

```tsx
import { ChatPanel } from "@/components/chat/ChatPanel";

export default function ChatPage() {
  return (
    <div className="max-w-4xl">
      <header className="mb-4">
        <h1 className="text-2xl font-bold">AI Asistan</h1>
        <p className="text-slate-600 text-sm">Doğal dilde sor, sistem cevap üretsin.</p>
      </header>
      <ChatPanel />
    </div>
  );
}
```

> **Önemli:** Page-level `max-w-4xl` constraint var — history sidebar bunu **kıracak**. Çözüm: `ChatPanel` kendi içinde `max-w-none` ile bu constraint'i override edebilir veya page.tsx'i de güncellemek için bir not düş. Tercihen **ChatPanel** içinde `-mx-{N}` veya `w-screen` trick'i ile sidebar full height kullansın.

## Ana App Layout (referans)

`frontend/app/layout.tsx` zaten 224px (`w-56`) sol sidebar içeriyor. Senin yeni history sidebar'ı bu **ana sidebar'ın hemen yanında** olacak — yani toplam iki dikey panel, ardından ana content.

```
| Ana App Sidebar (224px) | Chat History Sidebar (260px) | Chat Area (flex-1) |
```

## Ürün Özeti

**Ürün:** KOBİ/kooperatif için Telegram tabanlı müşteri asistanı + yönetim paneli.

**Kullanıcı:** 35-55 yaş işletme sahibi. Pazar akşamı paneli açıp "Bu hafta ne sattım?" sorgusu yapar. Sonraki Pazar tekrar açar — **geçmiş haftanın konuşmasını** görebilmek ister, karşılaştırma yapmak için.

## Tasarım Vizyonu

Üç sıralı adjektif: **sakin, güvenilir, sıcak**.

**Referanslar:** Claude.ai chat history sidebar, ChatGPT sidebar, Linear copilot. Hava: profesyonel ama davetkar.

**Kaçınılacak:** Gradient bombardımanı, mascot, bot avatar abartısı.

## Marka & Tonalite

- Resmi dil, 2. tekil ("siz")
- Welcome message örnek: "Doğal dilde sorabilirsiniz. Sistemdeki tüm veriye erişimim var."
- "+ Yeni Sohbet" butonu metni: kısa, eylem odaklı
- Boş history mesajı: "Henüz sohbet yok. İlk soruyu sorduğunuzda burada görünür."

## Renk Paleti (sabit)

```
brand-50:  #ecfdf5
brand-500: #10b981
brand-600: #059669
brand-700: #047857
```

Yan tonlar: `slate-*` (nötr), `emerald-*` (success/accent).

**History sidebar:**
- Arka plan: `bg-slate-50` (ana area `bg-slate-50` ile uyumlu, hafif ayrım için `border-r border-slate-200`)
- Aktif sohbet: `bg-brand-50 text-brand-700 border-l-2 border-brand-500`
- Hover: `hover:bg-slate-100`

**Compact chip şeridi (input üstü):**
- Açık pastel, `bg-slate-100 hover:bg-slate-200` veya kategoriye göre soft tonlar

## Tipografi

- System UI
- History title: `text-sm font-medium` (1 satır, `truncate`)
- History timestamp: `text-xs text-slate-500`
- Compact chip: `text-xs font-medium`
- Welcome: `text-base`

## Suggested Prompt Önerileri (DEĞİŞMEZ — empty state + compact şerit ikisinde aynı)

| Chip | Görünen text | Gönderilen mesaj | Beklenen tool |
|------|--------------|------------------|---------------|
| 📊 | Bu hafta satış grafiği | "Bu hafta günlük satış grafiğini göster" | sales_summary |
| 📦 | Düşük stoklar | "Düşük stokta olan ürünleri listele" | stock_overview |
| 👥 | Ayşe Yılmaz'ın son siparişleri | "Ayşe Yılmaz'ın son siparişlerini göster" | customer_order_history |
| ⚡ | Bekleyen acil siparişler | "Bekleyen acil siparişleri listele" | list_orders |

**Chip click race condition uyarısı:** `setInput(text); send()` çağırırsan `send` eski state'i okur. Doğru pattern: `send(textParam)` doğrudan parametre alsın veya `setInput` sonrası `setTimeout(send, 0)` (idealden uzak), en temizi:

```ts
async function send(messageOverride?: string) {
  const text = (messageOverride ?? input).trim();
  if (!text || busy) return;
  // ... rest using `text`
}
```

## UX Akışı

1. **İlk açılış (history boş):**
   - Sol: ana app sidebar + history sidebar (boş, "Henüz sohbet yok")
   - Sağ: welcome + 4 büyük chip kartı + compose box
2. **İlk mesaj:**
   - Welcome kaybolur, sohbet başlar
   - History sidebar'da yeni satır görünür (title = mesajın ilk 40 char)
   - Compact chip şeridi compose box üstünde görünür
3. **Yeni sohbet butonu:**
   - History listesinde aktif highlight kalkar
   - Sağ alan empty state'e döner (welcome + 4 kart)
4. **Sohbet geri çağırma:**
   - Sidebar'da bir sohbete tık → o sohbetin tüm turns'ü yüklenir, scroll en alta
   - Aktif highlight güncellenir
5. **Sohbet silme:**
   - Sidebar satırında `×` ikonuna hover → kırmızı tonu
   - Tık → confirm → silinir
   - Aktif sohbet silindiyse otomatik "yeni sohbet" moduna geç

## Responsive

- **Desktop (>1280px):** 3 panel yan yana (ana sidebar, history, chat)
- **Tablet (768-1280px):** History sidebar collapse'a girer — bir hamburger/clock ikonu ile aç-kapa olabilir
- **Mobile:** History sidebar tamamen overlay (full screen modal), chat area full width

## Erişilebilirlik

- History satırları `<button>` semantik (klavye ile gezilebilir)
- Aktif sohbet `aria-current="true"`
- Silme butonu `aria-label="Sohbeti sil"`
- Compact chip şeridi `role="toolbar"` veya semantic `<nav>` aria-label ile
- Loading sırasında `aria-busy="true"`
- Focus ring `ring-2 ring-brand-500`
- `prefers-reduced-motion` saygılı

## Tech Kısıtlamaları

- Next.js 14 App Router, **`"use client"` zorunlu**
- Tailwind 3.4 — yeni paket ekleme
- localStorage kullanımı `useEffect` içinde (SSR güvenli)
- `crypto.randomUUID()` SSR'da yok → client-only, sorun değil
- Mevcut import paths: `@/lib/api`, `./OrderListRender`, `./SalesChart`, `./StockOverviewRender`, `lucide-react`

## Backend Kontratı (DEĞİŞMEZ)

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

Backend'e history göndermek **gerekmiyor** — her mesaj stateless çağrılır. Conversation context UI tarafında turns array'inde tutulur, ama API isteği sadece o mesajı geçer.

> **Future-proof not:** `api.panelChat(message, history)` 2. parametre destekliyor ama şu an UI bunu kullanmıyor (boş bırakabilirsin). v2'de gerekmiyor.

## Test Senaryoları

Aşağıdaki adımlar tasarımcının kafasında çalışırken doğrulasın:

1. **İlk yükleme:** localStorage temiz → history sidebar boş, sağda welcome + 4 kart
2. **İlk soru:** "Bu hafta satış" yazılır → sidebar'da 1 sohbet, compact şerit görünür, chat alanı dolu
3. **İkinci soru aynı conversation:** Compose'tan "Hangi ürün önde?" → aynı sohbet güncellenir, sidebar başlık değişmez
4. **+ Yeni Sohbet:** Empty state'e döner, yeni soru yeni conversation yaratır → sidebar'da 2 satır
5. **Sohbet 1'e dön:** Tıklanır → eski turns yüklenir
6. **Sohbet sil:** × tıkla → confirm → satır gider
7. **Sayfa refresh:** Tüm sohbetler hâlâ orda (localStorage)

## Mevcut Kod (DEĞİŞTİRİLECEK kod — drop-in replace için)

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
        {/* ... existing UI ... */}
      </div>
      <form onSubmit={(e) => { e.preventDefault(); send(); }} className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Doğal dilde sor..." className="..." />
        <button type="submit" disabled={busy} className="...">Gönder</button>
      </form>
    </div>
  );
}
```

> Yukarıdaki kod **v1**; **mevcut dosya** zaten v1.5 (welcome + chip'ler ekli) — onu da göz önünde bulundur, ama tasarımcıya kafa karışıklığı yaratmamak için v1 referansı yeterli. Asıl önemli: state shape, API çağrısı, RenderData mantığı.

## Dependency Bileşenler (DEĞİŞMEZ)

- **OrderListRender** props: `{ data: { orders: [{order_id, customer_name, status, total, created_at}] } }`
- **SalesChart** props: `{ data: { rows: [...], group_by: "day"|"product" } }`
- **StockOverviewRender** props: `{ data: { products: [{id, name, stock, unit, is_low}] } }`

## Bonus: Relative Time Helper

Sidebar'da "2 saat önce" / "dün" formatı için inline helper yazabilirsin:

```ts
function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return "az önce";
  if (min < 60) return `${min} dk önce`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} saat önce`;
  const day = Math.floor(hr / 24);
  if (day === 1) return "dün";
  if (day < 7) return `${day} gün önce`;
  return new Date(iso).toLocaleDateString("tr-TR");
}
```

## Çıktı

Sadece yeni `ChatPanel.tsx` dosyasının tam içeriği. Açıklama yazma, kod blok dışında metin verme. History sidebar inline component olarak aynı dosyada kalabilir veya küçük yardımcı component'ler aynı dosyada üstte tanımlanabilir — ihracat sadece `ChatPanel` named export.
