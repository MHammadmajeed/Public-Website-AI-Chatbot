// src/hooks/useChatSession.ts
// Manages chat widget state: session token, message history, loading/error.

import { useState, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { sendChatMessage, ChatApiError } from "../api/chatClient";
import type { ChatMessage } from "../types/chat";

interface UseChatSessionOptions {
  sourcePage?: string;
}

export function useChatSession(options: UseChatSessionOptions = {}) {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastIntent, setLastIntent] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      setError(null);

      // Optimistically add the user's message to the UI immediately.
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await sendChatMessage({
          message: trimmed,
          session_token: sessionToken ?? undefined,
          source_page: options.sourcePage,
        });

        // First message: backend creates the session and returns its token.
        // Every message after this must reuse it.
        setSessionToken(response.session_token);
        setLastIntent(response.intent);

        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: "assistant",
          content: response.message,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const message =
          err instanceof ChatApiError
            ? err.message
            : "Something went wrong. Please try again.";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionToken, options.sourcePage]
  );

  const resetSession = useCallback(() => {
    setSessionToken(null);
    setMessages([]);
    setError(null);
    setLastIntent(null);
  }, []);

  return {
    sessionToken,
    messages,
    isLoading,
    error,
    lastIntent,
    sendMessage,
    resetSession,
  };
}