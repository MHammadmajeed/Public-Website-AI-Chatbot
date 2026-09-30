// src/components/ChatWidget.tsx
import { useChatSession } from "../hooks/useChatSession";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { LeadCaptureForm } from "./LeadCaptureForm";

export function ChatWidget() {
  const {
    sessionToken,
    messages,
    isLoading,
    error,
    showLeadPrompt,
    setLeadSubmitted,
    sendMessage,
    retryLastMessage,
  } = useChatSession({
    sourcePage: window.location.href,
  });

  return (
    
        <div role="region" aria-label="MoinSystems AI chat widget" className="chat-widget">
    
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
        <div
          role="alert"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "8px",
            padding: "6px 12px",
          }}
        >
          <p style={{ color: "#dc2626", fontSize: "13px", margin: 0 }}>
            {error}
          </p>
          <button
            onClick={() => retryLastMessage()}
            disabled={isLoading}
            aria-label="Retry sending your last message"
            style={{
              flexShrink: 0,
              padding: "4px 10px",
              borderRadius: "6px",
              border: "1px solid #dc2626",
              backgroundColor: "#fff",
              color: "#dc2626",
              fontSize: "12px",
              cursor: isLoading ? "not-allowed" : "pointer",
            }}
          >
            Retry
          </button>
        </div>
      )}

      {showLeadPrompt && sessionToken ? (
        <LeadCaptureForm
          sessionToken={sessionToken}
          onSubmitted={() => setLeadSubmitted(true)}
          onCancel={() => setLeadSubmitted(true)}
        />
      ) : (
        <MessageInput onSend={sendMessage} disabled={isLoading} />
      )}
    </div>
  );
}