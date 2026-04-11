import type { ToolRunRow } from "@/types/api";

type ToolRunsPanelProps = {
  toolRuns: ToolRunRow[];
  loading?: boolean;
};

export function ToolRunsPanel({ toolRuns, loading = false }: ToolRunsPanelProps) {
  if (loading) {
    return <div className="text-sm text-zinc-400">Loading tool runs...</div>;
  }

  if (toolRuns.length === 0) {
    return <div className="text-sm text-zinc-500">No tool runs loaded.</div>;
  }

  return (
    <div className="space-y-2">
      {toolRuns.map((run) => (
        <div key={run.id} className="rounded-xl border border-white/10 bg-black/20 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold text-zinc-100">{run.tool_name}</div>
            <div
              className={`rounded-md border px-2 py-0.5 text-xs ${
                run.returncode === 0
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                  : "border-red-500/20 bg-red-500/10 text-red-300"
              }`}
            >
              rc={run.returncode}
            </div>
          </div>

          <div className="mt-2 break-all text-xs text-zinc-300">{run.command_preview}</div>
          <div className="mt-2 text-[11px] text-zinc-500">Run ID: {run.id}</div>
          <div className="mt-1 text-[11px] text-zinc-500">{run.created_at}</div>
        </div>
      ))}
    </div>
  );
}