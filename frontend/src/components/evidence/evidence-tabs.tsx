"use client";

import { useState } from "react";
import type { FindingRow, MemoryItem, ToolRunRow } from "@/types/api";
import { FindingsPanel } from "@/components/evidence/findings-panel";
import { ToolRunsPanel } from "@/components/evidence/tool-runs-panel";
import { ReportPanel } from "@/components/evidence/report-panel";
import { MemoryPanel } from "@/components/evidence/memory-panel";

type EvidenceTab = "findings" | "toolRuns" | "report" | "memory";

type EvidenceTabsProps = {
  findings: FindingRow[];
  toolRuns: ToolRunRow[];
  report: string | null;
  memories: MemoryItem[];
  loadingFindings?: boolean;
  loadingToolRuns?: boolean;
  loadingReport?: boolean;
  loadingMemory?: boolean;
  onSaveMemory: (content: string) => Promise<void>;
  onRecallMemory: (query: string) => Promise<void>;
};

export function EvidenceTabs({
  findings,
  toolRuns,
  report,
  memories,
  loadingFindings = false,
  loadingToolRuns = false,
  loadingReport = false,
  loadingMemory = false,
  onSaveMemory,
  onRecallMemory,
}: EvidenceTabsProps) {
  const [activeTab, setActiveTab] = useState<EvidenceTab>("findings");

  const tabs: Array<{ key: EvidenceTab; label: string; loading: boolean }> = [
    { key: "findings", label: `Findings (${findings.length})`, loading: loadingFindings },
    { key: "toolRuns", label: `Tool Runs (${toolRuns.length})`, loading: loadingToolRuns },
    { key: "report", label: "Report", loading: loadingReport },
    { key: "memory", label: `Global Memory (${memories.length})`, loading: loadingMemory },
  ];

  return (
    <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/5 p-4 shadow-2xl backdrop-blur-xl">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">Evidence</h2>
        <p className="text-sm text-zinc-400">Session evidence and global operator memory.</p>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {tabs.map((tab) => {
          const active = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-xl border px-3 py-2 text-sm transition ${
                active
                  ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-300"
                  : "border-white/10 bg-black/20 text-zinc-300 hover:border-white/20"
              }`}
            >
              {tab.label}
              {tab.loading ? <span className="ml-2 text-[10px] text-zinc-400">…</span> : null}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-auto">
        {activeTab === "findings" && <FindingsPanel findings={findings} loading={loadingFindings} />}
        {activeTab === "toolRuns" && <ToolRunsPanel toolRuns={toolRuns} loading={loadingToolRuns} />}
        {activeTab === "report" && <ReportPanel report={report} loading={loadingReport} />}
        {activeTab === "memory" && (
          <MemoryPanel
            memories={memories}
            loading={loadingMemory}
            onSave={onSaveMemory}
            onRecall={onRecallMemory}
          />
        )}
      </div>
    </div>
  );
}