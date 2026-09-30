// src/api/chatClient.ts
// Typed Axios client for the MoinSystems AI chatbot backend.

import axios, { AxiosError } from "axios";
import type {
  SessionCreateRequest,
  SessionCreateResponse,
  ChatMessageRequest,
  ChatMessageResponse,
  LeadCaptureRequest,
  LeadCaptureResponse,
} from "../types/chat";

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string;

if (!BASE_URL) {
  // Fails loudly in dev if the .env file is missing, instead of silently
  // hitting a relative path that won't work.
  console.error(
    "VITE_API_BASE_URL is not set. Check frontend/.env exists and dev server was restarted."
  );
}

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 45000, // 15s — LLM responses can be slow
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------- Error handling helper ----------

export class ChatApiError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "ChatApiError";
    this.status = status;
  }
}

function handleError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const err = error as AxiosError<{ detail?: string }>;
    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    if (err.code === "ECONNABORTED") {
      throw new ChatApiError(
        "The request took too long. Please try again.",
        status
      );
    }
    if (status === 429) {
      throw new ChatApiError(
        "Too many requests — please wait a moment and try again.",
        status
      );
    }
    if (status && status >= 500) {
      throw new ChatApiError(
        "Something went wrong on our end. Please try again shortly.",
        status
      );
    }
    throw new ChatApiError(
      detail || "Something went wrong. Please try again.",
      status
    );
  }
  throw new ChatApiError("An unexpected error occurred.");
}

// ---------- Endpoint functions ----------

/**
 * Creates a new chat session. Call this once when the widget first opens,
 * before the visitor sends their first message.
 */
export async function createSession(
  payload: SessionCreateRequest
): Promise<SessionCreateResponse> {
  try {
    const { data } = await apiClient.post<SessionCreateResponse>(
      "/api/v1/sessions",
      payload
    );
    return data;
  } catch (error) {
    handleError(error);
  }
}

/**
 * Sends a chat message. Omit session_token on the very first message —
 * the backend will create a session and return its token, which you
 * must then reuse on every subsequent call.
 */
export async function sendChatMessage(
  payload: ChatMessageRequest
): Promise<ChatMessageResponse> {
  try {
    const { data } = await apiClient.post<ChatMessageResponse>(
      "/api/v1/chat/messages",
      payload
    );
    return data;
  } catch (error) {
    handleError(error);
  }
}

/**
 * Submits (partial or full) lead capture data tied to an existing session.
 * Check response.lead_state and response.missing_fields to know whether
 * to keep prompting the visitor for more info.
 */
export async function submitLeadCapture(
  payload: LeadCaptureRequest
): Promise<LeadCaptureResponse> {
  try {
    const { data } = await apiClient.post<LeadCaptureResponse>(
      "/api/v1/lead-capture",
      payload
    );
    return data;
  } catch (error) {
    handleError(error);
  }
}