"use client";

import { useState } from "react";
import type { ResearchResult } from "@/lib/api";

export default function ResultsView({ result }: { result: ResearchResult }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    if (!result.final_report) return;
    await navigator.clipboard.writeText(result.final_report);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="mt-10 space-y-10">
      {result.plan && (
        <section>
          <h2 className="font-mono text-xs text-muted mb-2">supervisor plan</h2>
          <p className="whitespace-pre-line text-sm text-ink-soft leading-relaxed border-l-2 border-line pl-4">
            {result.plan}
          </p>
        </section>
      )}

      {result.final_report && (
        <section className="paper-card p-6 sm:p-8">
          <div className="flex items-start justify-between gap-4 mb-3">
            <h2 className="font-mono text-xs text-muted">
              final report &middot; {result.iteration_count} iteration
              {result.iteration_count === 1 ? "" : "s"}
            </h2>
            <button
              onClick={handleCopy}
              className="font-mono text-xs text-muted hover:text-accent transition-colors shrink-0"
            >
              {copied ? "copied" : "copy"}
            </button>
          </div>
          <div className="font-serif text-[1.05rem] leading-relaxed whitespace-pre-line max-w-[70ch]">
            {result.final_report}
          </div>
        </section>
      )}

      {result.findings.length > 0 && (
        <section>
          <h2 className="font-mono text-xs text-muted mb-3">
            research findings &middot; {result.findings.length}
          </h2>
          <ul className="space-y-3">
            {result.findings.map((finding, i) => (
              <li key={i} className="border border-line p-4 text-sm text-ink-soft leading-relaxed">
                <p>{finding.content}</p>
                {finding.source && (
                  <p className="font-mono text-xs text-muted mt-2">{finding.source}</p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}