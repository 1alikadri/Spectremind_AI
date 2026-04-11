import type { ReactNode } from "react";
import Image from "next/image";

type AppShellProps = {
  sidebar: ReactNode;
  chat: ReactNode;
  context: ReactNode;
  apiStatus: "online" | "offline" | "checking";
};

export function AppShell({ sidebar, chat, context, apiStatus }: AppShellProps) {
  const statusClass =
    apiStatus === "online"
      ? "text-emerald-400 border-emerald-500/30 bg-emerald-500/10"
      : apiStatus === "offline"
      ? "text-red-400 border-red-500/30 bg-red-500/10"
      : "text-zinc-300 border-zinc-500/30 bg-zinc-500/10";

  return (
    <main className="min-h-screen bg-[#07090d] text-zinc-100">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.12),transparent_30%)] pointer-events-none" />
      <div className="absolute inset-0 opacity-[0.08] bg-[linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)] bg-[size:28px_28px] pointer-events-none" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <header className="border-b border-white/10 bg-black/30 backdrop-blur-xl">
          <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between px-6 py-4">
            <div className="flex items-center gap-4">
              <div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-2xl border border-cyan-500/20 bg-cyan-500/10 shadow-[0_0_30px_rgba(34,211,238,0.08)]">
                <Image
                  src="/brand/logo-mark.png"
                  alt="SpectreMind logo"
                  width={44}
                  height={44}
                  className="h-10 w-10 object-contain"
                  priority
                />
              </div>

              <div>
                <h1 className="text-xl font-semibold tracking-wide text-zinc-100">SpectreMind</h1>
                <p className="text-xs uppercase tracking-[0.24em] text-zinc-500">
                  Local Operator Console
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-zinc-400 md:block">
                Scope locked · Local-only mode
              </div>
              <div className={`rounded-full border px-3 py-1 text-xs font-medium ${statusClass}`}>
                API: {apiStatus}
              </div>
            </div>
          </div>
        </header>

        <div className="mx-auto grid w-full max-w-[1600px] flex-1 grid-cols-12 gap-4 p-4">
          <section className="col-span-12 lg:col-span-3">{sidebar}</section>
          <section className="col-span-12 lg:col-span-5">{chat}</section>
          <section className="col-span-12 lg:col-span-4">{context}</section>
        </div>
      </div>
    </main>
  );
}