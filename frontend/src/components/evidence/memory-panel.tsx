"use client";

import { useState } from "react";
import type { MemoryItem } from "@/types/api";

type MemoryPanelProps = {
  memories: MemoryItem[];
  loading?: boolean;
  onSave: (content: string) => Promise<void>;
  onRecall: (query: string) => Promise<void>;
};

export function MemoryPanel({ memories, loading = false, onSave, onRecall }: MemoryPanelProps) {
  const [saveText, setSaveText] = useState("");
  const [query, setQuery] = useState("");

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-3 text-sm text-zinc-300">
        Global long-term memory across engagements. Saved notes may still retain source-session context.
      </div>

      <div className="rounded-xl border border-white/10 bg-black/20 p-3">
        <div className="mb-2 text-sm font-medium text-zinc-100">Save to Global Memory</div>
        <textarea
          value={saveText}
          onChange={(e) => setSaveText(e.target.value)}
          rows={3}
          placeholder="Store an operator note or durable observation..."
          className="w-full resize-none rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none placeholder:text-zinc-500"
        />
        <button
          onClick={async () => {
            const value = saveText.trim();
            if (!value) return;
            await onSave(value);
            setSaveText("");
          }}
          className="mt-2 rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-300"
        >
          Save
        </button>
      </div>

      <div className="rounded-xl border border-white/10 bg-black/20 p-3">
        <div className="mb-2 text-sm font-medium text-zinc-100">Search Global Memory</div>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search global memory..."
            className="flex-1 rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm outline-none placeholder:text-zinc-500"
          />
          <button
            onClick={() => onRecall(query.trim())}
            className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-300"
          >
            Search
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {loading ? (
          <div className="text-sm text-zinc-400">Loading global memory...</div>
        ) : memories.length === 0 ? (
          <div className="text-sm text-zinc-500">No global memory items loaded.</div>
        ) : (
          memories.map((item) => (
            <div key={item.id} className="rounded-xl border border-white/10 bg-black/20 p-3">
              <div className="text-sm text-zinc-100">{item.content}</div>
              <div className="mt-2 text-[11px] text-zinc-500">
                Type: {item.memory_type} · ID: {item.id}
              </div>
              {item.tags?.length ? (
                <div className="mt-1 text-[11px] text-zinc-500">Tags: {item.tags.join(", ")}</div>
              ) : null}
            </div>
          ))
        )}
      </div>
    </div>
  );
}