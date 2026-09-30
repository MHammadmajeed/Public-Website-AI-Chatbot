// src/types/chat.ts
// TypeScript types mirroring the backend Pydantic schemas in app/schemas/
// Keep these in sync manually — if you change a schema on the backend,
// update the matching type here.

// ---------- Sessions (app/schemas/sessions.py) ----------

export interface SessionCreateRequest {
  source_page?: string | null;
}

export interface SessionCreateResponse {
  session_token: string;
}

// ---------- Chat (app/schemas/chat.py) ----------

export interface ChatMessageRequest {
  message: string; // 1–2000 chars
  session_token?: string | null; // omit on first message
  source_page?: string | null;
}

export type ChatIntent =
  | "company_overview"
  | "pricing"
  | "contact_request"
  | "technology"
  | "services"
  | "general";

export interface ChatMessageResponse {
  session_token: string;
  message: string;
  intent: ChatIntent;
}

// ---------- Leads (app/schemas/leads.py) ----------

export interface LeadCaptureRequest {
  session_token: string; // max 64 chars
  full_name?: string | null; // max 80
  email?: string | null; // max 254
  contact_number?: string | null; // max 20
  company_name?: string | null; // max 120
  project_summary?: string | null; // max 1000
  service_interest?: string | null; // max 200
  timeline?: string | null; // max 100
  budget_range?: string | null; // max 100
  source_page?: string | null; // max 300
}

export interface LeadCaptureResponse {
  lead_state: string;
  missing_fields: string[];
  message: string;
  lead_id?: string | null; // set once all required fields are collected and saved
}

// ---------- Frontend-only UI types ----------
// These don't exist on the backend — they're for the widget's own state management.

export interface ChatMessage {
  id: string; // client-generated (uuid) for React keys
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface ChatWidgetState {
  sessionToken: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
}