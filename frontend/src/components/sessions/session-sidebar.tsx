"use client";

import { useMemo, useState } from "react";
import type { SessionRow } from "@/types/api";

type SessionSidebarProps = {
  sessions: SessionRow[];
  selectedSessionId: string;
  onSelectSession: (session: SessionRow) => void;
  onCreateSession: (name: string) => Promise<void>;
  disabled?: boolean;
};

export function SessionSidebar({
  sessions,
  selectedSessionId,
  onSelectSession,
  onCreateSession,
  disabled = false,
}: SessionSidebarProps) {
  const [name, setName] = useState("");
  const sorted = useMemo(() => [...sessions], [sessions]);

  return (
    <div className="h-full rounded-2xl border border-white/10 bg-white/5 p-4 shadow-2xl backdrop-blur-xl">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Sessions</h2>
        <p className="text-sm text-zinc-400">Recent engagements and working context.</p>
        {disabled ? (
          <div className="mt-2 rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            Request in progress. Session switching is temporarily locked.
          </div>
        ) : null}
      </div>

      <form
        className="mb-4 flex gap-2"
        onSubmit={async (e) => {
          e.preventDefault();
          const trimmed = name.trim();
          if (!trimmed || disabled) return;
          await onCreateSession(trimmed);
          setName("");
        }}
      >
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="New session name"
          disabled={disabled}
          className="flex-1 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none placeholder:text-zinc-500 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled}
          className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-sm font-medium text-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Create
        </button>
      </form>

      <div className="space-y-2">
        {sorted.length === 0 ? (
          <div className="rounded-xl border border-dashed border-white/10 p-4 text-sm text-zinc-400">
            No sessions yet.
          </div>
        ) : (
          sorted.map((session) => {
            const active = session.session_id === selectedSessionId;
            return (
              <button
                key={session.session_id}
                onClick={() => {
                  if (disabled) return;
                  onSelectSession(session);
                }}
                disabled={disabled}
                className={`w-full rounded-xl border p-3 text-left transition ${
                  active
                    ? "border-cyan-500/40 bg-cyan-500/10"
                    : "border-white/10 bg-black/20 hover:border-white/20 hover:bg-white/5"
                } disabled:cursor-not-allowed disabled:opacity-50`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="truncate text-sm font-semibold text-zinc-100">
                    {session.name || "Unnamed session"}
                  </div>
                  <div className="rounded-md border border-white/10 bg-black/30 px-2 py-0.5 text-[10px] uppercase tracking-wide text-zinc-400">
                    {session.status}
                  </div>
                </div>

                <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
                  <span className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-2 py-0.5 text-cyan-300">
                    Findings {session.finding_count ?? 0}
                  </span>
                  <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-zinc-400">
                    Runs {session.tool_run_count ?? 0}
                  </span>
                  {session.has_memory ? (
                    <span className="rounded-md border border-emerald-500/20 bg-emerald-500/10 px-2 py-0.5 text-emerald-300">
                      Memory
                    </span>
                  ) : null}
                </div>

                <div className="mt-2 truncate text-[11px] text-zinc-500">
                  {session.session_id}
                </div>
              </button>
            );
          })
        )}
      </div>

      <div className="mt-6 border-t border-white/10 pt-4">
        <div className="text-[10px] uppercase tracking-[0.22em] text-zinc-600">
          SpectreMind
        </div>
        <div className="mt-1 text-xs text-zinc-500">
          Local intelligence. Operator controlled.
        </div>
      </div>
    </div>
  );
}