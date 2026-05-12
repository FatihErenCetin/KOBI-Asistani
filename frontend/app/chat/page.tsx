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
