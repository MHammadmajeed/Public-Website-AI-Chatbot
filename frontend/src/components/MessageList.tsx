// src/components/MessageList.tsx
import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types/chat";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest message whenever the list changes.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div
      role="log"
      aria-live="polite"
      aria-label="Chat conversation"
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: "8px",
      }}
    >
      {messages.length === 0 && !isLoading && (
        <p style={{ color: "#888", fontSize: "14px", textAlign: "center" }}>
          Ask us anything about MoinSystems AI.
        </p>
      )}

      {messages.map((msg) => (
        <div
          key={msg.id}
          style={{
            alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
            maxWidth: "80%",
            padding: "8px 12px",
            borderRadius: "12px",
            backgroundColor: msg.role === "user" ? "#2563eb" : "#f1f1f1",
            color: msg.role === "user" ? "#fff" : "#111",
            fontSize: "14px",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
          }}
        >
          {msg.content}
        </div>
      ))}

      {isLoading && (
        <div
          aria-label="Assistant is typing"
          style={{
            alignSelf: "flex-start",
            padding: "8px 12px",
            borderRadius: "12px",
            backgroundColor: "#f1f1f1",
            color: "#888",
            fontSize: "14px",
          }}
        >
          Typing…
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}