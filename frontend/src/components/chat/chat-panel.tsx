"use client";

import { useState } from "react";

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

type ChatPanelProps = {
  messages: ChatMessage[];
  onSend: (payload: { text: string; approved: boolean }) => Promise<void>;
  sending?: boolean;
};

function renderKeyData(data: Record<string, unknown>) {
  const interestingKeys = [
    "session_id",
    "message",
    "tool_card",
    "plan",
    "parsed_result",
    "watcher_result",
    "report_path",
    "session",
    "memory",
    "session_state",
    "artifacts",
    "findings",
    "tool_runs",
    "report",
    "memories",
  ];

  const filtered = Object.fromEntries(
    Object.entries(data).filter(([key]) => interestingKeys.includes(key))
  );

  if (Object.keys(filtered).length === 0) return null;

  return (
    <details className="mt-2 rounded-xl border border-white/10 bg-black/25">
      <summary className="cursor-pointer list-none px-3 py-2 text-xs font-medium uppercase tracking-[0.2em] text-zinc-400">
        view details
      </summary>
      <pre className="overflow-auto border-t border-white/10 p-3 text-[11px] text-zinc-300">
        {JSON.stringify(filtered, null, 2)}
      </pre>
    </details>
  );
}

export function ChatPanel({ messages, onSend, sending = false }: ChatPanelProps) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/5 p-4 shadow-2xl backdrop-blur-xl">
      <ChatComposer messages={messages} onSend={onSend} sending={sending} />
    </div>
  );
}

function ChatComposer({
  messages,
  onSend,
  sending,
}: {
  messages: ChatMessage[];
  onSend: (payload: { text: string; approved: boolean }) => Promise<void>;
  sending: boolean;
}) {
    const [text, setText] = useState("");
    const [approved, setApproved] = useState(false);

  return (
    <>
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Command Surface</h2>
        <p className="text-sm text-zinc-400">Chat with SpectreMind and dispatch scoped actions.</p>

        {sending ? (
          <div className="mt-3 rounded-xl border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-300">
            Request in progress. Waiting for SpectreMind to respond...
          </div>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {[
          "show sessions",
          "show session",
          "show findings",
          "show tool runs",
          "show report",
        ].map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => setText(prompt)}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-300 transition hover:border-cyan-500/30 hover:bg-cyan-500/10 hover:text-cyan-300"
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="mb-4 flex-1 space-y-3 overflow-auto rounded-xl border border-white/10 bg-black/20 p-3">
        {messages.length === 0 ? (
          <div className="text-sm text-zinc-500">No messages yet.</div>
        ) : (
          messages.map((message) => {
            if (message.kind === "user") {
              return (
                <div
                  key={message.id}
                  className="ml-8 rounded-xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-sm text-cyan-50"
                >
                  <div className="mb-1 text-[10px] uppercase tracking-wider text-zinc-400">user</div>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
              );
            }

            const statusClass =
              message.status === "completed" || message.status === "handled"
                ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                : message.status === "error" || message.status === "blocked"
                ? "border-red-500/20 bg-red-500/10 text-red-300"
                : "border-white/10 bg-white/5 text-zinc-300";

            return (
              <div
                key={message.id}
                className="mr-8 rounded-2xl border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.03))] p-4 text-sm text-zinc-100 shadow-[0_0_30px_rgba(0,0,0,0.2)]"
              >
                <div className="mb-2 flex items-center justify-between gap-3">
                  <div className="text-[10px] uppercase tracking-wider text-zinc-400">assistant</div>
                  <div className={`rounded-md border px-2 py-0.5 text-[10px] uppercase ${statusClass}`}>
                    {message.status}
                  </div>
                </div>

                <div className="whitespace-pre-wrap text-sm font-semibold leading-6 text-zinc-100">
                  {message.summary}
                </div>

                {message.nextSteps.length > 0 ? (
                  <div className="mt-3">
                    <div className="mb-1 text-[11px] uppercase tracking-wide text-zinc-500">next steps</div>
                    <ul className="space-y-1 text-xs text-zinc-300">
                      {message.nextSteps.map((step, index) => (
                        <li key={`${message.id}-step-${index}`}>• {step}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {Object.keys(message.data ?? {}).length > 0 ? (
                  <div className="mt-3 text-[11px] uppercase tracking-[0.2em] text-zinc-500">
                    structured output
                  </div>
                ) : null}

                {renderKeyData(message.data)}
              </div>
            );
          })
        )}
      </div>

      <form
        className="space-y-3"
        onSubmit={async (e) => {
          e.preventDefault();
          const payload = text.trim();
          if (!payload || sending) return;
          await onSend({ text: payload, approved });
          setText("");
        }}
      >
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          placeholder="Enter a request like: show sessions, show findings, scan 127.0.0.1"
          className="w-full resize-none rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm outline-none placeholder:text-zinc-500"
        />

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-zinc-300">
            <input
              type="checkbox"
              checked={approved}
              onChange={(e) => setApproved(e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-black/30"
            />
            Explicit approval
          </label>

          <button
            type="submit"
            disabled={sending}
            className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-4 py-2 text-sm font-medium text-cyan-300 disabled:opacity-50"
          >
            {sending ? "Sending..." : "Execute"}
          </button>
        </div>
      </form>
    </>
  );
}

