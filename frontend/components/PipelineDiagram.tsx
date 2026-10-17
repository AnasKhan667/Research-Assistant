"use client";

const STAGES = [
  { key: "supervisor", label: "Supervisor", note: "drafts the plan" },
  { key: "researcher", label: "Researcher", note: "gathers findings" },
  { key: "critic", label: "Critic", note: "judges sufficiency" },
  { key: "writer", label: "Writer", note: "drafts the report" },
] as const;

export type StageKey = (typeof STAGES)[number]["key"];

export default function PipelineDiagram({ activeStage }: { activeStage: StageKey | null }) {
  return (
    <div className="flex items-stretch">
      {STAGES.map((stage, i) => {
        const isActive = activeStage === stage.key;
        return (
          <div key={stage.key} className="flex items-center flex-1">
            <div className="flex-1">
              <div
                className={`border px-4 py-3 transition-colors ${
                  isActive
                    ? "border-accent bg-accent-soft node-active"
                    : "border-line bg-paper-raised"
                }`}
              >
                <p className="font-mono text-xs text-muted">{String(i + 1).padStart(2, "0")}</p>
                <p className="font-serif text-lg leading-tight mt-1">{stage.label}</p>
                <p className="text-xs text-ink-soft mt-1">{stage.note}</p>
              </div>
            </div>
            {i < STAGES.length - 1 && (
              <div className="w-6 sm:w-10 h-px bg-line shrink-0" aria-hidden />
            )}
          </div>
        );
      })}
    </div>
  );
}