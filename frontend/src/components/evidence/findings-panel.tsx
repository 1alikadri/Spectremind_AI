import type { FindingRow } from "@/types/api";

type FindingsPanelProps = {
  findings: FindingRow[];
  loading?: boolean;
};

export function FindingsPanel({ findings, loading = false }: FindingsPanelProps) {
  if (loading) {
    return <div className="text-sm text-zinc-400">Loading findings...</div>;
  }

  if (findings.length === 0) {
    return <div className="text-sm text-zinc-500">No findings loaded.</div>;
  }

  return (
    <div className="space-y-2">
      {findings.map((item, index) => (
        <div
          key={`${item.tool_run_id ?? "run"}-${item.port ?? "port"}-${index}`}
          className="rounded-xl border border-white/10 bg-black/20 p-3"
        >
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-zinc-100">
              {item.port ?? "?"}/{item.protocol ?? "?"}
            </span>
            <span className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-2 py-0.5 text-xs text-cyan-300">
              {item.state ?? "unknown"}
            </span>
            <span className="text-zinc-300">{item.service ?? "unknown service"}</span>
          </div>

          <div className="mt-2 text-xs text-zinc-400">
            Host: {item.host ?? "unknown"}
            {item.version ? ` · Version: ${item.version}` : ""}
            {item.os_hint ? ` · OS: ${item.os_hint}` : ""}
          </div>

          <div className="mt-1 text-[11px] text-zinc-500">
            Task: {item.task_id ?? "n/a"} · Tool Run: {item.tool_run_id ?? "n/a"}
          </div>
        </div>
      ))}
    </div>
  );
}