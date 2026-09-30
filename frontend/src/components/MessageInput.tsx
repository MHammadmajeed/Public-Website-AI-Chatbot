// src/components/MessageInput.tsx
import { useState, useRef, useEffect, type KeyboardEvent } from "react";

interface MessageInputProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Send focus to the input once, when the widget first mounts,
  // so keyboard/screen-reader users land straight in the conversation.
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        display: "flex",
        gap: "8px",
        padding: "12px",
        borderTop: "1px solid #e5e5e5",
      }}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message…"
        rows={1}
        disabled={disabled}
        aria-label="Type your message"
        style={{
          flex: 1,
          resize: "none",
          padding: "8px 10px",
          borderRadius: "8px",
          border: "1px solid #ccc",
          fontSize: "14px",
          fontFamily: "inherit",
        }}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label={disabled ? "Sending message" : "Send message"}
        style={{
          padding: "8px 16px",
          borderRadius: "8px",
          border: "none",
          backgroundColor: disabled || !value.trim() ? "#ccc" : "#2563eb",
          color: "#fff",
          fontSize: "14px",
          cursor: disabled || !value.trim() ? "not-allowed" : "pointer",
        }}
      >
        Send
      </button>
    </div>
  );
}