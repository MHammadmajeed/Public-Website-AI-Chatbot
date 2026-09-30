// src/hooks/useChatSession.ts
// Manages chat widget state: session token, message history, loading/error, retry.

import { useState, useCallback, useRef } from "react";
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
  const [leadSubmitted, setLeadSubmitted] = useState(false);

  // Tracks the text of the message currently in flight or last failed,
  // so "Retry" can resend it without the user retyping.
  const pendingTextRef = useRef<string | null>(null);

  const deliver = useCallback(
    async (trimmed: string) => {
      setError(null);
      setIsLoading(true);
      pendingTextRef.current = trimmed;

      try {
        const response = await sendChatMessage({
          message: trimmed,
          session_token: sessionToken ?? undefined,
          source_page: options.sourcePage,
        });

        setSessionToken(response.session_token);
        setLastIntent(response.intent);

        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: "assistant",
          content: response.message,
          timestamp: Date.now(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        pendingTextRef.current = null; // succeeded, nothing to retry
      } catch (err) {
        const message =
          err instanceof ChatApiError
            ? err.message
            : "Something went wrong. Please try again.";
        setError(message);
        // pendingTextRef stays set so retry() can use it
      } finally {
        setIsLoading(false);
      }
    },
    [sessionToken, options.sourcePage]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed) return;

      // Optimistically add the user's message to the UI immediately.
      const userMessage: ChatMessage = {
        id: uuidv4(),
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, userMessage]);

      await deliver(trimmed);
    },
    [deliver]
  );

  const retryLastMessage = useCallback(async () => {
    if (!pendingTextRef.current) return;
    // Don't add a new bubble — just retry delivering the same text.
    await deliver(pendingTextRef.current);
  }, [deliver]);

  const resetSession = useCallback(() => {
    setSessionToken(null);
    setMessages([]);
    setError(null);
    setLastIntent(null);
    setLeadSubmitted(false);
    pendingTextRef.current = null;
  }, []);

  const showLeadPrompt =
    !leadSubmitted &&
    (lastIntent === "pricing" || lastIntent === "contact_request");

  return {
    sessionToken,
    messages,
    isLoading,
    error,
    lastIntent,
    showLeadPrompt,
    setLeadSubmitted,
    sendMessage,
    retryLastMessage,
    resetSession,
  };
}