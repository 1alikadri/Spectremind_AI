import type {
  AskRequest,
  AskResponse,
  CreateSessionRequest,
  CreateSessionResponse,
  FindingsResponse,
  HealthResponse,
  MemoryRecallResponse,
  MemorySaveRequest,
  MemorySaveResponse,
  ReportResponse,
  SessionsResponse,
  ToolRunsResponse,
} from "@/types/api";

import type { ChatHistoryResponse } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.summary ?? body?.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }

  return res.json() as Promise<T>;
}

export const api = {

  getChatHistory(params: { latest?: boolean; sessionId?: string; sessionName?: string; limit?: number }): Promise<ChatHistoryResponse> {
  const qs = new URLSearchParams();
  if (params.latest) qs.set("latest", "true");
  if (params.sessionId) qs.set("session_id", params.sessionId);
  if (params.sessionName) qs.set("session_name", params.sessionName);
  if (params.limit) qs.set("limit", String(params.limit));
  return apiFetch<ChatHistoryResponse>(`/chat/history?${qs.toString()}`);
},

  getHealth(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>("/health");
  },

  getSessions(): Promise<SessionsResponse> {
    return apiFetch<SessionsResponse>("/sessions");
  },

  createSession(payload: CreateSessionRequest): Promise<CreateSessionResponse> {
    return apiFetch<CreateSessionResponse>("/sessions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  ask(payload: AskRequest): Promise<AskResponse> {
    return apiFetch<AskResponse>("/chat/ask", {
      method: "POST",
      body: JSON.stringify({
        text: payload.text,
        approved: payload.approved ?? false,
        session_id: payload.session_id ?? "",
        session_name: payload.session_name ?? "",
        latest: payload.latest ?? false,
      }),
    });
  },

  getFindings(params: { latest?: boolean; sessionId?: string; sessionName?: string }): Promise<FindingsResponse> {
    const qs = new URLSearchParams();
    if (params.latest) qs.set("latest", "true");
    if (params.sessionId) qs.set("session_id", params.sessionId);
    if (params.sessionName) qs.set("session_name", params.sessionName);
    return apiFetch<FindingsResponse>(`/findings?${qs.toString()}`);
  },

  getToolRuns(params: { latest?: boolean; sessionId?: string; sessionName?: string }): Promise<ToolRunsResponse> {
    const qs = new URLSearchParams();
    if (params.latest) qs.set("latest", "true");
    if (params.sessionId) qs.set("session_id", params.sessionId);
    if (params.sessionName) qs.set("session_name", params.sessionName);
    return apiFetch<ToolRunsResponse>(`/tool-runs?${qs.toString()}`);
  },

  getReport(params: { latest?: boolean; sessionId?: string; sessionName?: string }): Promise<ReportResponse> {
    const qs = new URLSearchParams();
    if (params.latest) qs.set("latest", "true");
    if (params.sessionId) qs.set("session_id", params.sessionId);
    if (params.sessionName) qs.set("session_name", params.sessionName);
    return apiFetch<ReportResponse>(`/reports?${qs.toString()}`);
  },

  saveMemory(payload: MemorySaveRequest): Promise<MemorySaveResponse> {
    return apiFetch<MemorySaveResponse>("/memory/save", {
      method: "POST",
      body: JSON.stringify({
        content: payload.content,
        memory_type: payload.memory_type ?? "note",
        session_id: payload.session_id ?? "",
        session_name: payload.session_name ?? "",
        latest: payload.latest ?? false,
      }),
    });
  },

  recallMemory(query: string, limit = 8): Promise<MemoryRecallResponse> {
    return apiFetch<MemoryRecallResponse>("/memory/recall", {
      method: "POST",
      body: JSON.stringify({
        query,
        memory_type: null,
        limit,
      }),
    });
  },
};