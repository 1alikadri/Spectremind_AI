export type ApiEnvelope<T = Record<string, unknown>> = {
  status: string;
  summary: string;
  data: T;
  next_steps: string[];
};

export type StoredChatMessage = {
  id: number;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: {
    status?: string;
    summary?: string;
    next_steps?: string[];
    data?: Record<string, unknown>;
  };
  created_at: string;
};

export type ChatHistoryResponse = ApiEnvelope<{
  session_id: string;
  messages: StoredChatMessage[];
}>;

export type HealthResponse = {
  status: string;
  service: string;
};

export type SessionRow = {
  session_id: string;
  name?: string | null;
  created_at: string;
  status: string;
  finding_count?: number;
  tool_run_count?: number;
  has_memory?: number;
};

export type AskRequest = {
  text: string;
  approved?: boolean;
  session_id?: string;
  session_name?: string;
  latest?: boolean;
};

export type AskResponse = ApiEnvelope<{
  session_id?: string;
  [key: string]: unknown;
}>;

export type SessionsResponse = ApiEnvelope<{
  sessions: SessionRow[];
}>;

export type CreateSessionRequest = {
  name: string;
};

export type CreateSessionResponse = ApiEnvelope<{
  session_id: string;
  name?: string | null;
  created_at: string;
  status: string;
}>;

export type FindingRow = {
  task_id?: string | null;
  tool_run_id?: number | null;
  host?: string | null;
  port?: number | null;
  protocol?: string | null;
  state?: string | null;
  service?: string | null;
  version?: string | null;
  os_hint?: string | null;
  created_at?: string | null;
};

export type FindingsResponse = ApiEnvelope<{
  session_id: string;
  findings: FindingRow[];
}>;

export type ToolRunRow = {
  id: number;
  session_id: string;
  tool_name: string;
  command_preview: string;
  stdout_path?: string | null;
  stderr_path?: string | null;
  returncode: number;
  created_at: string;
};

export type ToolRunsResponse = ApiEnvelope<{
  session_id: string;
  tool_runs: ToolRunRow[];
}>;

export type ReportResponse = ApiEnvelope<{
  session_id: string;
  report_path: string;
  report: string | null;
}>;

export type MemoryItem = {
  id: number;
  memory_type: string;
  memory_key?: string | null;
  content: string;
  tags: string[];
  source_session_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type MemoryRecallResponse = ApiEnvelope<{
  query: string;
  memories: MemoryItem[];
}>;

export type MemorySaveRequest = {
  content: string;
  memory_type?: string;
  session_id?: string;
  session_name?: string;
  latest?: boolean;
};

export type MemorySaveResponse = ApiEnvelope<{
  memory_id: number;
  memory_type: string;
  content: string;
  source_session_id?: string | null;
}>;