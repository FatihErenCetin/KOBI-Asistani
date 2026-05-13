// app/page.tsx — Landing page (public)
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  Check,
  ChevronRight,
  Image as ImageIcon,
  Instagram,
  MessageSquare,
  Mic,
  Package,
  Quote,
  Send,
  ShieldCheck,
  ShoppingBag,
  Sparkles,
  Sun,
  TrendingUp,
  Truck,
} from "lucide-react";

import { VideoModalButton } from "@/components/landing/VideoModalButton";

/* -------------------------------------------------------------------------- */
/*  Mock data — sayfayı tek dosyada tutmak için inline                        */
/* -------------------------------------------------------------------------- */

const PAINS = [
  {
    title: "WhatsApp'tan gelen siparişler karışıyor",
    body:
      "Hangi müşterinin neyi istediğini, ne zaman söz verdiğini hatırlamak gittikçe zor. Bir not defteri yetmiyor.",
    icon: MessageSquare,
  },
  {
    title: "Son kullanma tarihi atlanıyor",
    body:
      "Rafta unutulan üç-beş ürün ay sonunda ciddi bir zarar. Kimse her şeyi tek başına takip edemez.",
    icon: AlertTriangle,
  },
  {
    title: "Sosyal medyaya zaman kalmıyor",
    body:
      "Müşteri yeni kampanyayı duymadan ay bitiyor. Her gün post atmak ayrı bir iş, ama atmasan unutuluyorsun.",
    icon: Instagram,
  },
];

const FEATURES = [
  {
    icon: Bot,
    title: "Telegram Asistan",
    body:
      "Müşterin botla mesajlaşır, sen panelde takip edersin. Sesli mesajı bile yazıya çevirir.",
    accent: "amber",
  },
  {
    icon: Package,
    title: "Stok ve Son Kullanma",
    body:
      "Stok azaldığında veya SKT yaklaştığında uyarır, doğru anda indirim önerir.",
    accent: "emerald",
  },
  {
    icon: ShoppingBag,
    title: "Akıllı Sipariş Önerisi",
    body:
      "Hangi tedarikçiden ne kadar almalı? Karşılaştırır, sana mail taslağını hazır verir.",
    accent: "amber",
  },
  {
    icon: Truck,
    title: "Kargo Bildirimleri",
    body:
      "Sipariş alındı, yola çıktı, teslim edildi — her aşamada müşteriye kişisel mesaj otomatik gider.",
    accent: "emerald",
  },
  {
    icon: Instagram,
    title: "Sosyal Medya Asistanı",
    body:
      "Instagram, TikTok ve YouTube için metni de görseli de hazırlar. Sen sadece onaylarsın.",
    accent: "amber",
  },
  {
    icon: TrendingUp,
    title: "Finansal Görünürlük",
    body:
      "Kâr-zarar, aylık trend, en çok kazandıran ürünler — formül yok, otomatik tablo.",
    accent: "emerald",
  },
  {
    icon: AlertTriangle,
    title: "Şikayet Riski Tespiti",
    body:
      "Müşterinin tonu değişti mi, kargo geç mi kaldı? Sorun büyümeden senin önüne gelir.",
    accent: "amber",
  },
  {
    icon: Sun,
    title: "Sabah Brifingi",
    body:
      "Her sabah 09:00'da Telegram'a günün özeti düşer: satış, stok, dikkat edilmesi gerekenler.",
    accent: "emerald",
  },
] as const;

const STEPS = [
  {
    n: "01",
    title: "Hesap aç",
    body: "30 saniye sürer. Sadece bir telefon numarası ve mağaza adı.",
  },
  {
    n: "02",
    title: "Telegram'ı bağla, ürünleri yükle",
    body: "Excel dosyan varsa olduğu gibi at — ürünleri biz okuyup düzeniyoruz.",
  },
  {
    n: "03",
    title: "İlk müşterini karşıla",
    body:
      "Bot mesaj alır almaz panelde görürsün. Bir tıkla onayla, sipariş çıksın.",
  },
];

const TESTIMONIALS = [
  {
    name: "Mehmet Aksoy",
    role: "Anadolu Bal Kooperatifi · Muğla",
    body:
      "Bal kavanozlarının hangisi yakında bitecek, hangisi raflarda fazla kalmış — sabah aç bakıyorum, panel söylüyor. Şubat ayında zayiatımız üçte bire düştü.",
    initials: "MA",
  },
  {
    name: "Ayşe Demir",
    role: "Ege Zeytin Market · İzmir",
    body:
      "Instagram postlarını asistan yazıyor. Yine ben okuyorum tabii, ama bir saatlik işim on dakikaya indi. Müşterinin geri dönüşü de daha hızlı geliyor.",
    initials: "AD",
  },
  {
    name: "Cemil Yıldız",
    role: "Yıldız Kasap · Ankara",
    body:
      "Eskiden WhatsApp'ta sipariş alırken hangisi hazırlanmış, hangisi yola çıkmış kaybediyordum. Şimdi her sipariş bir kart, bir defa dokunuyorum.",
    initials: "CY",
  },
] as const;

const PRICING = [
  {
    name: "Başlangıç",
    price: "0",
    period: "ay",
    desc: "Yeni başlayan veya küçük dükkânlar için yeterli temel paket.",
    features: [
      "50 ürüne kadar",
      "Telegram bot ve panel",
      "Temel stok takibi",
      "Aylık özet rapor",
    ],
    cta: "Ücretsiz Başla",
    featured: false,
  },
  {
    name: "Profesyonel",
    price: "299",
    period: "ay",
    desc: "Bu paket esnafın çoğunluğu için. AI ve sosyal medya dahil.",
    features: [
      "Sınırsız ürün",
      "AI sipariş ve stok önerileri",
      "Sosyal medya asistanı",
      "Finansal analiz ve trendler",
      "Otomatik kargo bildirimleri",
    ],
    cta: "Demo İste",
    featured: true,
  },
  {
    name: "Premium",
    price: "599",
    period: "ay",
    desc: "Çok çalışanlı veya yoğun sipariş alan mağazalar için.",
    features: [
      "Profesyonel'in tüm özellikleri",
      "Sınırsız Gemini AI çağrısı",
      "Çoklu çalışan ve rol",
      "Öncelikli destek",
      "Özel entegrasyonlar",
    ],
    cta: "Demo İste",
    featured: false,
  },
] as const;

const FAQS = [
  {
    q: "Verilerim güvende mi?",
    a:
      "Evet. Tüm veriler KVKK uyumlu, Türkiye'deki sunucularda tutulur. Şifreler hash'lenir, müşteri verilerini hiçbir üçüncü partiyle paylaşmayız.",
  },
  {
    q: "Telegram bot için ek bir ücret ödeyecek miyim?",
    a:
      "Hayır. Telegram'ın kendisi ücretsiz, botu da bizim platforma dahil. Sen sadece KOBİ Asistanı abonelik planını ödüyorsun.",
  },
  {
    q: "Eski siparişlerim ve ürünlerim panele nasıl gelir?",
    a:
      "Excel veya CSV dosyanı yüklersin, biz okuyup düzeniriz. Devam eden siparişlerini de tek tek elle ekleyebilirsin.",
  },
  {
    q: "Hangi sosyal medya platformlarına post atabilirim?",
    a:
      "Şu an Instagram, TikTok ve YouTube. Facebook ve X (Twitter) yakında. Mevcut hesabını bir tıkla bağlayabilirsin.",
  },
  {
    q: "İnternet kesintisinde ne olur?",
    a:
      "Panel internet ister, ama Telegram bot mesaj geçmişini tutar. Bağlantı geri geldiğinde her şey olduğu yerden devam eder.",
  },
  {
    q: "Vazgeçersem verilerim ne olur?",
    a:
      "Tek tıkla tüm ürün ve müşteri verilerini CSV olarak indirirsin, hesabını kapatabilirsin. Kalıcı silme talep edersen 30 gün içinde işleriz.",
  },
];

/* -------------------------------------------------------------------------- */
/*  Page                                                                      */
/* -------------------------------------------------------------------------- */

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-slate-900">
      <TopNav />
      <Hero />
      <PainPoints />
      <Features />
      <HowItWorks />
      <Testimonials />
      <Pricing />
      <Faq />
      <FinalCta />
      <Footer />
      <MobileStickyCta />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Top nav                                                                   */
/* -------------------------------------------------------------------------- */

function TopNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500 text-white shadow-sm">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </span>
          <span className="text-base font-semibold tracking-tight">
            KOBİ Asistanı
          </span>
        </Link>
        <nav
          aria-label="Ana menü"
          className="hidden items-center gap-7 text-sm text-slate-600 md:flex"
        >
          <a href="#ozellikler" className="hover:text-slate-900">
            Özellikler
          </a>
          <a href="#nasil-calisir" className="hover:text-slate-900">
            Nasıl çalışır
          </a>
          <a href="#fiyat" className="hover:text-slate-900">
            Fiyatlandırma
          </a>
          <a href="#sss" className="hover:text-slate-900">
            SSS
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="text-sm font-medium text-slate-700 hover:text-slate-900"
          >
            Giriş Yap
          </Link>
          <Link
            href="/register"
            className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3.5 py-2 text-sm font-semibold text-white shadow-sm shadow-amber-500/30 transition hover:bg-amber-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
          >
            Ücretsiz Dene
            <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </header>
  );
}

/* -------------------------------------------------------------------------- */
/*  Hero                                                                      */
/* -------------------------------------------------------------------------- */

function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Soft amber → krem geçişi: marka sıcaklığı için */}
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-10 bg-gradient-to-b from-amber-50 via-amber-50/50 to-white"
      />
      <div
        aria-hidden="true"
        className="absolute -top-32 right-[-10%] -z-10 h-[480px] w-[480px] rounded-full bg-amber-200/40 blur-3xl"
      />

      <div className="mx-auto max-w-7xl px-4 pb-16 pt-12 sm:px-6 lg:px-8 lg:pb-24 lg:pt-20">
        {/* Trust strip */}
        <div className="mb-8 flex justify-center lg:justify-start">
          <span className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-white/70 px-3 py-1 text-xs font-medium text-amber-900 shadow-sm backdrop-blur">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            Şu an 1.200+ esnaf kullanıyor
          </span>
        </div>

        <div className="grid items-center gap-12 lg:grid-cols-[1.1fr_1fr] lg:gap-10">
          <div className="text-center lg:text-left">
            <h1 className="text-balance text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Bakkalın da{" "}
              <span className="bg-gradient-to-br from-amber-500 to-amber-600 bg-clip-text text-transparent">
                yapay zekâsı
              </span>{" "}
              olsun.
            </h1>
            <p className="mt-5 text-pretty text-lg leading-relaxed text-slate-600 sm:text-xl">
              Sipariş, stok, müşteri ve sosyal medya — hepsi tek bir Telegram
              botu ve panelden. Asistan senin için takip eder, sen mağazana
              bak.
            </p>

            <div className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:flex-row lg:justify-start">
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-5 py-3 text-base font-semibold text-white shadow-sm shadow-amber-500/30 transition hover:bg-amber-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2"
              >
                Ücretsiz Dene
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <VideoModalButton />
            </div>

            <p className="mt-5 text-sm text-slate-500">
              Kredi kartı gerekmez · 5 dakikada kurulum
            </p>
          </div>

          <HeroMockup />
        </div>
      </div>
    </section>
  );
}

/* Hero'da görsel ağırlığı için kompoze mockup: Telegram chat + panel preview.
   Stock screenshot yerine CSS ile çizmek hem hızlı yüklenir hem daha
   karakterli görünür. */
function HeroMockup() {
  return (
    <div className="relative mx-auto w-full max-w-md lg:max-w-none">
      <div
        aria-hidden="true"
        className="absolute -inset-6 -z-10 rounded-[2rem] bg-gradient-to-br from-amber-200/40 to-emerald-200/30 blur-2xl"
      />

      {/* Panel kartı (arka katman) */}
      <div className="relative rounded-2xl border border-slate-200 bg-white p-4 shadow-xl shadow-slate-900/10 lg:p-5">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
          </div>
          <span className="text-xs font-medium text-slate-500">
            Bugünün özeti
          </span>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          <PanelStat label="Sipariş" value="42" delta="+18%" tone="emerald" />
          <PanelStat label="Ciro" value="₺8.4K" delta="+12%" tone="emerald" />
          <PanelStat label="Stok uyarı" value="3" delta="acil" tone="amber" />
        </div>

        <div className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-3">
          <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
            En son sipariş
          </p>
          <div className="mt-1.5 flex items-center justify-between">
            <p className="text-sm font-medium text-slate-800">
              Ayşe Yılmaz · 2 ürün
            </p>
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
              Hazırlanıyor
            </span>
          </div>
        </div>
      </div>

      {/* Telegram chat (öne çıkan ön katman) */}
      <div className="absolute -bottom-6 -right-3 w-[58%] rotate-[2deg] rounded-2xl border border-slate-200 bg-white p-3 shadow-2xl shadow-slate-900/15 sm:-right-6 sm:w-[55%] lg:-bottom-8 lg:-left-10 lg:right-auto lg:w-[62%] lg:-rotate-3">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-amber-500 text-xs font-bold text-white">
            BA
          </span>
          <div className="min-w-0">
            <p className="text-xs font-semibold text-slate-800">
              Bakkal Asistanı
            </p>
            <p className="text-[10px] text-emerald-600">çevrimiçi</p>
          </div>
        </div>

        <div className="mt-3 space-y-2">
          <ChatBubble side="them">
            Merhaba, kahvaltılık bal var mı?
          </ChatBubble>
          <ChatBubble side="me">
            Merhaba 👋 Çiçek balı 500g 145₺, çam balı 500g 165₺. Stokta var.
          </ChatBubble>
          <ChatBubble side="them" voice>
            <Mic className="h-3 w-3" />
            Sesli mesaj · 0:08
          </ChatBubble>
          <ChatBubble side="me" small>
            &quot;İki çiçek balı istiyorum, akşama lazım&quot; — sipariş
            açıldı, kargo planlandı.
          </ChatBubble>
        </div>

        <div className="mt-3 flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5">
          <Mic className="h-3 w-3 text-slate-400" aria-hidden="true" />
          <ImageIcon className="h-3 w-3 text-slate-400" aria-hidden="true" />
          <span className="flex-1 text-[10px] text-slate-400">
            Bir şey yaz…
          </span>
          <Send className="h-3 w-3 text-amber-500" aria-hidden="true" />
        </div>
      </div>
    </div>
  );
}

function PanelStat({
  label,
  value,
  delta,
  tone,
}: {
  label: string;
  value: string;
  delta: string;
  tone: "emerald" | "amber";
}) {
  const toneClass =
    tone === "emerald"
      ? "bg-emerald-50 text-emerald-700"
      : "bg-amber-50 text-amber-800";
  return (
    <div className="rounded-lg border border-slate-100 bg-white p-2.5">
      <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">
        {label}
      </p>
      <p className="mt-1 text-xl font-bold text-slate-900 tabular-nums">
        {value}
      </p>
      <span
        className={`mt-1 inline-block rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${toneClass}`}
      >
        {delta}
      </span>
    </div>
  );
}

function ChatBubble({
  side,
  children,
  voice,
  small,
}: {
  side: "me" | "them";
  children: React.ReactNode;
  voice?: boolean;
  small?: boolean;
}) {
  const isMe = side === "me";
  const base = small ? "text-[10px] italic" : "text-[11px]";
  return (
    <div className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-2.5 py-1.5 leading-snug ${base} ${
          isMe
            ? "rounded-br-md bg-amber-500 text-white"
            : voice
              ? "rounded-bl-md bg-slate-100 text-slate-600 inline-flex items-center gap-1.5"
              : "rounded-bl-md bg-slate-100 text-slate-700"
        }`}
      >
        {children}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Pain points                                                               */
/* -------------------------------------------------------------------------- */

function PainPoints() {
  return (
    <section className="border-y border-slate-100 bg-white py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionEyebrow>Bu tanıdık geliyorsa…</SectionEyebrow>
        <h2 className="mt-2 max-w-2xl text-balance text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Esnafın gerçek dertleri,
          <br className="hidden sm:block" /> kahveler arası çözülmüyor.
        </h2>

        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 lg:gap-6">
          {PAINS.map((p) => {
            const Icon = p.icon;
            return (
              <div
                key={p.title}
                className="group relative rounded-2xl border border-slate-200 bg-amber-50/40 p-6 transition hover:border-amber-200 hover:bg-amber-50"
              >
                <span
                  aria-hidden="true"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-white text-amber-600 ring-1 ring-amber-100"
                >
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">
                  {p.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">
                  {p.body}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Features                                                                  */
/* -------------------------------------------------------------------------- */

function Features() {
  return (
    <section
      id="ozellikler"
      className="relative bg-gradient-to-b from-white to-amber-50/40 py-20 sm:py-24"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <SectionEyebrow>Çözüm</SectionEyebrow>
          <h2 className="mt-2 text-balance text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Bir asistan, sekiz iş yükünden seni kurtarıyor.
          </h2>
          <p className="mt-4 text-pretty text-base text-slate-600 sm:text-lg">
            Her özellik yıllardır esnafın eliyle yapılan tekrarlı işi
            otomatikleştirir. Karar yine sende, takip artık sende değil.
          </p>
        </div>

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-5">
          {FEATURES.map((f) => {
            const Icon = f.icon;
            const accent =
              f.accent === "amber"
                ? "bg-amber-100 text-amber-700"
                : "bg-emerald-100 text-emerald-800";
            return (
              <article
                key={f.title}
                className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
              >
                <span
                  aria-hidden="true"
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-xl ${accent}`}
                >
                  <Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-base font-semibold text-slate-900">
                  {f.title}
                </h3>
                <p className="mt-1.5 flex-1 text-sm leading-relaxed text-slate-600">
                  {f.body}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  How it works                                                              */
/* -------------------------------------------------------------------------- */

function HowItWorks() {
  return (
    <section id="nasil-calisir" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <SectionEyebrow>Nasıl çalışır?</SectionEyebrow>
          <h2 className="mt-2 text-balance text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            İki kahve molasında kurulur.
          </h2>
        </div>

        <ol className="mt-12 grid gap-6 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li
              key={s.n}
              className="relative rounded-2xl border border-slate-200 bg-white p-6"
            >
              <span className="text-5xl font-bold tracking-tight text-amber-500/30 tabular-nums">
                {s.n}
              </span>
              <h3 className="mt-2 text-lg font-semibold text-slate-900">
                {s.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {s.body}
              </p>
              {i < STEPS.length - 1 && (
                <ChevronRight
                  aria-hidden="true"
                  className="absolute -right-3 top-1/2 hidden h-5 w-5 -translate-y-1/2 text-slate-300 md:block"
                />
              )}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Testimonials                                                              */
/* -------------------------------------------------------------------------- */

function Testimonials() {
  return (
    <section className="bg-emerald-900 py-20 text-white sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <SectionEyebrow tone="dark">Esnaftan</SectionEyebrow>
          <h2 className="mt-2 text-balance text-3xl font-bold tracking-tight sm:text-4xl">
            Bizi kullanan dükkânlardan, kendi sözleriyle.
          </h2>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-3 lg:gap-6">
          {TESTIMONIALS.map((t) => (
            <figure
              key={t.name}
              className="flex h-full flex-col rounded-2xl bg-emerald-800/40 p-6 ring-1 ring-white/10"
            >
              <Quote aria-hidden="true" className="h-6 w-6 text-amber-300/80" />
              <blockquote className="mt-3 flex-1 text-base leading-relaxed text-emerald-50">
                {t.body}
              </blockquote>
              <figcaption className="mt-5 flex items-center gap-3 border-t border-white/10 pt-4">
                <span
                  aria-hidden="true"
                  className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-amber-400 text-sm font-bold text-emerald-900"
                >
                  {t.initials}
                </span>
                <div>
                  <p className="text-sm font-semibold">{t.name}</p>
                  <p className="text-xs text-emerald-200/80">{t.role}</p>
                </div>
              </figcaption>
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Pricing                                                                   */
/* -------------------------------------------------------------------------- */

function Pricing() {
  return (
    <section id="fiyat" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <SectionEyebrow center>Fiyatlandırma</SectionEyebrow>
          <h2 className="mt-2 text-balance text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Şeffaf paketler. Gizli ücret yok.
          </h2>
          <p className="mt-4 text-pretty text-base text-slate-600 sm:text-lg">
            Aylık iptal edebilirsin. Vergiler dahil değildir.
          </p>
        </div>

        <div className="mx-auto mt-12 grid max-w-5xl gap-5 md:grid-cols-3">
          {PRICING.map((p) => (
            <div
              key={p.name}
              className={`relative flex flex-col rounded-2xl border p-6 ${
                p.featured
                  ? "border-amber-300 bg-amber-50/40 shadow-lg shadow-amber-500/10 md:scale-[1.03]"
                  : "border-slate-200 bg-white"
              }`}
            >
              {p.featured && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-amber-500 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-white shadow-sm">
                  En Popüler
                </span>
              )}
              <h3 className="text-lg font-semibold text-slate-900">{p.name}</h3>
              <p className="mt-1 text-sm text-slate-600">{p.desc}</p>
              <div className="mt-5 flex items-baseline gap-1">
                <span className="text-4xl font-bold tracking-tight tabular-nums">
                  ₺{p.price}
                </span>
                <span className="text-sm text-slate-500">/ {p.period}</span>
              </div>

              <ul className="mt-5 flex-1 space-y-2.5 text-sm text-slate-700">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <Check
                      aria-hidden="true"
                      className={`mt-0.5 h-4 w-4 shrink-0 ${
                        p.featured ? "text-amber-600" : "text-emerald-600"
                      }`}
                    />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href="/register"
                className={`mt-6 inline-flex items-center justify-center gap-1.5 rounded-xl px-4 py-2.5 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ${
                  p.featured
                    ? "bg-amber-500 text-white shadow-sm shadow-amber-500/30 hover:bg-amber-600 focus-visible:ring-amber-500"
                    : "border border-slate-200 bg-white text-slate-900 hover:border-slate-300 hover:bg-slate-50 focus-visible:ring-slate-500"
                }`}
              >
                {p.cta}
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Link>
            </div>
          ))}
        </div>

        <p className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500">
          <ShieldCheck
            className="h-4 w-4 text-emerald-600"
            aria-hidden="true"
          />
          KVKK uyumlu · Türkiye'de barındırılan veriler
        </p>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  FAQ                                                                       */
/* -------------------------------------------------------------------------- */

/* <details>/<summary> kullanıyoruz: JS gerekmiyor, klavye ile erişilebilir,
   server component'te sorunsuz çalışır. */
function Faq() {
  return (
    <section
      id="sss"
      className="border-t border-slate-100 bg-amber-50/30 py-20 sm:py-24"
    >
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <SectionEyebrow center>SSS</SectionEyebrow>
          <h2 className="mt-2 text-balance text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Aklındaki ilk sorular.
          </h2>
        </div>

        <div className="mt-10 divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-white">
          {FAQS.map((f) => (
            <details key={f.q} className="group px-5 py-4 sm:px-6">
              <summary className="flex cursor-pointer list-none items-start justify-between gap-4 text-left text-base font-semibold text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2">
                <span>{f.q}</span>
                <span
                  aria-hidden="true"
                  className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition group-open:rotate-45 group-open:bg-amber-100 group-open:text-amber-700"
                >
                  <svg
                    viewBox="0 0 24 24"
                    className="h-3.5 w-3.5"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  >
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                </span>
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">
                {f.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Final CTA                                                                 */
/* -------------------------------------------------------------------------- */

function FinalCta() {
  return (
    <section className="relative overflow-hidden bg-slate-900 py-20 text-white sm:py-24">
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-40 [background-image:radial-gradient(circle_at_top_right,theme(colors.amber.500/0.35),transparent_50%),radial-gradient(circle_at_bottom_left,theme(colors.emerald.500/0.25),transparent_50%)]"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 -z-0 [background-image:linear-gradient(to_right,theme(colors.white/0.04)_1px,transparent_1px),linear-gradient(to_bottom,theme(colors.white/0.04)_1px,transparent_1px)] [background-size:48px_48px]"
      />

      <div className="relative mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-balance text-3xl font-bold tracking-tight sm:text-5xl">
          Müşterin bekliyor — sen panele bakmaya başla.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-pretty text-base text-slate-300 sm:text-lg">
          KOBİ Asistanı şu an 1.200+ esnafa eşlik ediyor. Aralarına katılmak
          beş dakika alır.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-amber-500/30 transition hover:bg-amber-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
          >
            Şimdi Ücretsiz Dene
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 rounded-xl border border-white/15 px-6 py-3.5 text-base font-medium text-white/90 transition hover:border-white/30 hover:text-white"
          >
            Giriş Yap
          </Link>
        </div>
        <p className="mt-4 text-sm text-slate-400">
          Kredi kartı gerekmez · 5 dakikada kurulum
        </p>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------------------- */
/*  Footer                                                                    */
/* -------------------------------------------------------------------------- */

function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.5fr_1fr_1fr_1fr] lg:px-8">
        <div>
          <Link href="/" className="flex items-center gap-2">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500 text-white">
              <Sparkles className="h-4 w-4" aria-hidden="true" />
            </span>
            <span className="text-base font-semibold tracking-tight">
              KOBİ Asistanı
            </span>
          </Link>
          <p className="mt-3 max-w-xs text-sm leading-relaxed text-slate-600">
            Türk esnafı için yapay zekâ destekli işletme asistanı. Bakkaldan
            kasaba, manavdan kooperatife.
          </p>
        </div>

        <FooterCol title="Ürün">
          <FooterLink href="#ozellikler">Özellikler</FooterLink>
          <FooterLink href="#fiyat">Fiyatlandırma</FooterLink>
          <FooterLink href="/login">Giriş Yap</FooterLink>
          <FooterLink href="/register">Kayıt Ol</FooterLink>
        </FooterCol>

        <FooterCol title="Şirket">
          <FooterLink href="#nasil-calisir">Nasıl çalışır</FooterLink>
          <FooterLink href="#sss">SSS</FooterLink>
        </FooterCol>

        <FooterCol title="Destek">
          <FooterLink href="#sss">Yardım</FooterLink>
        </FooterCol>
      </div>

      <div className="border-t border-slate-100">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 py-5 text-xs text-slate-500 sm:flex-row sm:px-6 lg:px-8">
          <p>
            © {new Date().getFullYear()} KOBİ Asistanı · Tüm hakları
            saklıdır.
          </p>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </p>
      <ul className="mt-3 space-y-2 text-sm text-slate-700">{children}</ul>
    </div>
  );
}

function FooterLink({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  // Next.js Link soft-navigation için; "#..." anchor'lar otomatik scroll
  const isAnchor = href.startsWith("#");
  return (
    <li>
      {isAnchor ? (
        <a href={href} className="hover:text-amber-600">
          {children}
        </a>
      ) : (
        <Link href={href} className="hover:text-amber-600">
          {children}
        </Link>
      )}
    </li>
  );
}

/* -------------------------------------------------------------------------- */
/*  Mobile sticky CTA                                                         */
/* -------------------------------------------------------------------------- */

function MobileStickyCta() {
  return (
    <div className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-2 gap-2 border-t border-slate-200 bg-white/95 p-3 backdrop-blur md:hidden">
      <Link
        href="/login"
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700"
      >
        Giriş Yap
      </Link>
      <Link
        href="/register"
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-amber-500 px-4 py-3 text-sm font-semibold text-white shadow-sm shadow-amber-500/30"
      >
        Ücretsiz Dene
        <ArrowRight className="h-4 w-4" aria-hidden="true" />
      </Link>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Shared bits                                                               */
/* -------------------------------------------------------------------------- */

function SectionEyebrow({
  children,
  tone = "light",
  center,
}: {
  children: React.ReactNode;
  tone?: "light" | "dark";
  center?: boolean;
}) {
  const color = tone === "dark" ? "text-amber-300" : "text-amber-700";
  return (
    <span
      className={`inline-flex items-center text-xs font-semibold uppercase tracking-[0.14em] ${color} ${center ? "" : ""}`}
    >
      <span className="mr-2 inline-block h-px w-6 bg-current opacity-60" />
      {children}
    </span>
  );
}
