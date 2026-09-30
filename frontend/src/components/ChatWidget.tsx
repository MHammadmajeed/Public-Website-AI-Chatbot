// src/components/ChatWidget.tsx
import { useChatSession } from "../hooks/useChatSession";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";

export function ChatWidget() {
  const { messages, isLoading, error, sendMessage } = useChatSession({
    sourcePage: window.location.href,
  });

  return (
    <div
      role="region"
      aria-label="MoinSystems AI chat widget"
      style={{
        display: "flex",
        flexDirection: "column",
        width: "360px",
        height: "500px",
        border: "1px solid #e5e5e5",
        borderRadius: "12px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        fontFamily: "system-ui, sans-serif",
        overflow: "hidden",
        backgroundColor: "#fff",
      }}
    >
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #e5e5e5",
          fontWeight: 600,
          fontSize: "15px",
        }}
      >
        MoinSystems AI Assistant
      </div>

      <MessageList messages={messages} isLoading={isLoading} />

      {error && (
        <p
          role="alert"
          style={{
            color: "#dc2626",
            fontSize: "13px",
            padding: "0 12px",
            margin: 0,
          }}
        >
          {error}
        </p>
      )}

      <MessageInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}