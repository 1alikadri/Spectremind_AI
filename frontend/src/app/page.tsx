"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { SessionSidebar } from "@/components/sessions/session-sidebar";
import { ChatPanel } from "@/components/chat/chat-panel";
import { EvidenceTabs } from "@/components/evidence/evidence-tabs";
import { api } from "@/lib/api";
import type {
  AskResponse,
  FindingRow,
  MemoryItem,
  SessionRow,
  ToolRunRow,
} from "@/types/api";

type UserMessage = {
  kind: "user";
  id: string;
  content: string;
};

type AssistantMessage = {
  kind: "assistant";
  id: string;
  summary: string;
  status: string;
  nextSteps: string[];
  data: Record<string, unknown>;
};

type ChatMessage = UserMessage | AssistantMessage;

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<"online" | "offline" | "checking">("checking");
  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionRow | null>(null);
  const [chatBySession, setChatBySession] = useState<Record<string, ChatMessage[]>>({});
  const activeSessionId = selectedSession?.session_id ?? "";
  const messages = activeSessionId ? (chatBySession[activeSessionId] ?? []) : [];
  const [findings, setFindings] = useState<FindingRow[]>([]);
  const [toolRuns, setToolRuns] = useState<ToolRunRow[]>([]);
  const [report, setReport] = useState<string | null>(null);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const chatLoadVersion = useRef(0);

  const [loadingFindings, setLoadingFindings] = useState(false);
  const [loadingToolRuns, setLoadingToolRuns] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [loadingMemory, setLoadingMemory] = useState(false);
  const [sending, setSending] = useState(false);

  async function loadChatForSession(session: SessionRow | null) {
    const sessionId = session?.session_id;
    if (!sessionId) {
      return;
    }

    const requestVersion = ++chatLoadVersion.current;

    try {
      const res = await api.getChatHistory({
        sessionId,
        limit: 100,
      });

      // Ignore stale responses if the user switched sessions quickly
      if (requestVersion !== chatLoadVersion.current) {
        return;
      }

      const mapped = (res.data.messages ?? []).map((item) => {
        if (item.role === "user") {
          return {
            kind: "user" as const,
            id: String(item.id),
            content: item.content,
          };
        }

        return {
          kind: "assistant" as const,
          id: String(item.id),
          summary: item.metadata?.summary ?? item.content,
          status: item.metadata?.status ?? "handled",
          nextSteps: item.metadata?.next_steps ?? [],
          data: item.metadata?.data ?? {},
        };
      });

      setChatBySession((prev) => ({
        ...prev,
        [sessionId]: mapped,
      }));
    } catch {
      if (requestVersion !== chatLoadVersion.current) {
        return;
      }

      setChatBySession((prev) => ({
        ...prev,
        [sessionId]: [],
      }));
    }
  }

  async function refreshSessions(): Promise<SessionRow[]> {
    const res = await api.getSessions();
    const rows = res.data.sessions ?? [];
    setSessions(rows);

    if (!selectedSession && rows.length > 0) {
      setSelectedSession(rows[0]);
    }

    return rows;
  }

  async function loadEvidenceForSession(session: SessionRow | null) {
    if (!session?.session_id) {
      setFindings([]);
      setToolRuns([]);
      setReport(null);
      return;
    }

    setLoadingFindings(true);
    setLoadingToolRuns(true);
    setLoadingReport(true);

    try {
      const [findingsRes, toolRunsRes, reportRes] = await Promise.all([
        api.getFindings({ sessionId: session.session_id }),
        api.getToolRuns({ sessionId: session.session_id }),
        api.getReport({ sessionId: session.session_id }),
      ]);

      setFindings(findingsRes.data.findings ?? []);
      setToolRuns(toolRunsRes.data.tool_runs ?? []);
      setReport(reportRes.data.report ?? null);
    } catch {
      setFindings([]);
      setToolRuns([]);
      setReport(null);
    } finally {
      setLoadingFindings(false);
      setLoadingToolRuns(false);
      setLoadingReport(false);
    }
  }

  useEffect(() => {
    api
      .getHealth()
      .then(() => setApiStatus("online"))
      .catch(() => setApiStatus("offline"));

    refreshSessions().catch(() => setApiStatus("offline"));
  }, []);

  useEffect(() => {
    loadEvidenceForSession(selectedSession).catch(() => {});
    loadChatForSession(selectedSession).catch(() => {});
  }, [selectedSession?.session_id]);

  useEffect(() => {
    handleRecallMemory("").catch(() => {});
  }, []);

  const selectedSessionName = useMemo(
    () => selectedSession?.name || selectedSession?.session_id || "No session selected",
    [selectedSession]
  );

  async function handleCreateSession(name: string) {
    const created = await api.createSession({ name });
    const rows = await refreshSessions();
    const match = rows.find((row) => row.session_id === created.data.session_id);
    if (match) {
      setSelectedSession(match);
      await loadEvidenceForSession(match);
    }
  }

  async function handleSend(payload: { text: string; approved: boolean }) {
    if (sending) return;

    const targetSession = selectedSession;
    const sessionId = targetSession?.session_id;
    if (!sessionId) return;

    const userMessage: UserMessage = {
      kind: "user",
      id: makeId(),
      content: payload.text,
    };

    // Optimistic local append only for the session being sent to
    setChatBySession((prev) => ({
      ...prev,
      [sessionId]: [...(prev[sessionId] ?? []), userMessage],
    }));

    setSending(true);

    try {
      const res: AskResponse = await api.ask({
        text: payload.text,
        approved: payload.approved,
        session_id: sessionId,
        session_name: "",
        latest: false,
      });

      const assistantMessage: AssistantMessage = {
        kind: "assistant",
        id: makeId(),
        summary: res.summary,
        status: res.status,
        nextSteps: res.next_steps ?? [],
        data: (res.data ?? {}) as Record<string, unknown>,
      };

      // Append response into the same session bucket the request belonged to
      setChatBySession((prev) => ({
        ...prev,
        [sessionId]: [...(prev[sessionId] ?? []), assistantMessage],
      }));

      const responseSessionId =
        typeof res.data?.session_id === "string" ? res.data.session_id : sessionId;

      const rows = await refreshSessions();

      const resolvedSession =
        rows.find((s) => s.session_id === responseSessionId) ??
        rows.find((s) => s.session_id === sessionId) ??
        null;

      // Refresh evidence for the request's session
      if (resolvedSession?.session_id) {
        await loadEvidenceForSession(resolvedSession);
        await loadChatForSession(resolvedSession); // canonical server truth
      }

      // Only change visible selection if the user is still on the same session
      setSelectedSession((current) => {
        if (!current) return resolvedSession;
        if (current.session_id === sessionId) {
          return resolvedSession;
        }
        return current;
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Request failed.";

      const assistantMessage: AssistantMessage = {
        kind: "assistant",
        id: makeId(),
        summary: `Request failed: ${message}`,
        status: "error",
        nextSteps: [],
        data: {},
      };

      setChatBySession((prev) => ({
        ...prev,
        [sessionId]: [...(prev[sessionId] ?? []), assistantMessage],
      }));
    } finally {
      setSending(false);
    }
  }

  async function handleSaveMemory(content: string) {
    if (!selectedSession?.session_id) return;

    await api.saveMemory({
      content,
      session_id: selectedSession.session_id,
      memory_type: "note",
    });

    await handleRecallMemory("");
  }

async function handleRecallMemory(query: string) {
  setLoadingMemory(true);
  try {
    const res = await api.recallMemory(query, 8);
    setMemories(res.data.memories ?? []);
  } finally {
    setLoadingMemory(false);
  }
}

  return (
    <AppShell
      apiStatus={apiStatus}
      sidebar={
        <SessionSidebar
          sessions={sessions}
          selectedSessionId={selectedSession?.session_id ?? ""}
          onSelectSession={setSelectedSession}
          onCreateSession={handleCreateSession}
          disabled={sending}
        />
      }
      chat={<ChatPanel messages={messages} onSend={handleSend} sending={sending} />}
      context={
        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.22em] text-zinc-500">
                  active engagement
                </div>
                <h2 className="mt-1 text-lg font-semibold text-zinc-100">{selectedSessionName}</h2>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-right">
                <div className="text-[10px] uppercase tracking-wide text-zinc-500">session id</div>
                <div className="max-w-[180px] truncate text-xs text-zinc-300">
                  {selectedSession?.session_id ?? "none"}
                </div>
              </div>
            </div>
          </div>

          <EvidenceTabs
            findings={findings}
            toolRuns={toolRuns}
            report={report}
            memories={memories}
            loadingFindings={loadingFindings}
            loadingToolRuns={loadingToolRuns}
            loadingReport={loadingReport}
            loadingMemory={loadingMemory}
            onSaveMemory={handleSaveMemory}
            onRecallMemory={handleRecallMemory}
          />
        </div>
      }
    />
  );
}