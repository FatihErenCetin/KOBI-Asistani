import { ChatPanel } from "@/components/chat/ChatPanel";

export default function ChatPage() {
  return (
    <div className="h-[calc(100vh-2rem)] overflow-hidden rounded-[2rem] border border-white/70 bg-white/80 shadow-card backdrop-blur lg:h-[calc(100vh-4rem)]">
      <ChatPanel />
    </div>
  );
}
