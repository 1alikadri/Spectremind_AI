type ReportPanelProps = {
  report: string | null;
  loading?: boolean;
};

type ParsedSection = {
  title: string;
  lines: string[];
};

function stripBackticks(value: string) {
  return value.replace(/`/g, "");
}

function parseReport(report: string) {
  const lines = report.split("\n");
  const sections: ParsedSection[] = [];
  let title = "Report";
  let current: ParsedSection | null = null;

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;

    if (line.startsWith("# ")) {
      title = line.slice(2).trim();
      continue;
    }

    if (line.startsWith("## ")) {
      if (current) sections.push(current);
      current = {
        title: line.slice(3).trim(),
        lines: [],
      };
      continue;
    }

    if (!current) {
      current = {
        title: "Overview",
        lines: [],
      };
    }

    current.lines.push(line);
  }

  if (current) sections.push(current);

  return { title, sections };
}

function renderLine(line: string, index: number) {
  if (line.startsWith("- ")) {
    const content = line.slice(2).trim();

    if (content.includes(":")) {
      const [label, ...rest] = content.split(":");
      const value = stripBackticks(rest.join(":").trim());

      return (
        <div
          key={index}
          className="flex flex-col gap-1 rounded-xl border border-white/10 bg-black/20 px-3 py-2 sm:flex-row sm:items-start sm:justify-between"
        >
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">{label}</div>
          <div className="text-sm text-zinc-200 sm:max-w-[70%] sm:text-right">{value || "—"}</div>
        </div>
      );
    }

    return (
      <li key={index} className="ml-5 list-disc text-sm text-zinc-300">
        {stripBackticks(content)}
      </li>
    );
  }

  return (
    <p key={index} className="text-sm leading-7 text-zinc-300">
      {stripBackticks(line)}
    </p>
  );
}

export function ReportPanel({ report, loading = false }: ReportPanelProps) {
  if (loading) {
    return <div className="text-sm text-zinc-400">Loading report...</div>;
  }

  if (!report) {
    return <div className="text-sm text-zinc-500">No report loaded.</div>;
  }

  const { title, sections } = parseReport(report);

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-4">
        <div className="text-[11px] uppercase tracking-[0.22em] text-cyan-300">Structured Report</div>
        <h3 className="mt-2 text-lg font-semibold text-zinc-100">{title}</h3>
      </div>

      {sections.map((section) => (
        <section
          key={section.title}
          className="rounded-2xl border border-white/10 bg-black/20 p-4 shadow-[0_0_20px_rgba(0,0,0,0.15)]"
        >
          <h4 className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-zinc-200">
            {section.title}
          </h4>

          <div className="space-y-3">
            {section.lines.map((line, index) => renderLine(line, index))}
          </div>
        </section>
      ))}
    </div>
  );
}