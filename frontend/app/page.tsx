"use client";

import { useState } from "react";
import Header from "@/components/Header";
import PipelineDiagram, { type StageKey } from "@/components/PipelineDiagram";
import ResultsView from "@/components/ResultsView";
import { runResearch, type ResearchResult } from "@/lib/api";

const STAGE_SEQUENCE: StageKey[] = ["supervisor", "researcher", "critic", "writer"];

export default function Home() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeStage, setActiveStage] = useState<StageKey | null>(null);
  const [result, setResult] = useState<ResearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setElapsed(0);

    let stageIndex = 0;
    setActiveStage(STAGE_SEQUENCE[0]);
    const stageTimer = setInterval(() => {
      stageIndex = (stageIndex + 1) % STAGE_SEQUENCE.length;
      setActiveStage(STAGE_SEQUENCE[stageIndex]);
    }, 1800);

    const elapsedTimer = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    try {
      const data = await runResearch(query.trim());
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      clearInterval(stageTimer);
      clearInterval(elapsedTimer);
      setActiveStage(null);
      setLoading(false);
    }
  }

  const hasRun = loading || result || error;

  return (
    <>
      <Header />
      <main className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
        <header className="mb-12">
          <p className="font-mono text-xs text-muted mb-3">a research workflow, not a chatbot</p>
          <h1 className="font-serif text-3xl sm:text-4xl leading-tight max-w-[18ch]">
            Four agents read the room before they write the report.
          </h1>
          <p className="text-ink-soft mt-4 max-w-[52ch] leading-relaxed">
            Ask a research question. A supervisor plans the approach, a researcher gathers
            findings, a critic decides when there&apos;s enough, and a writer drafts the
            final report.
          </p>
        </header>

        <PipelineDiagram activeStage={activeStage} />

        <form onSubmit={handleSubmit} className="mt-10">
          <label htmlFor="query" className="font-mono text-xs text-muted">
            your question
          </label>
          <div className="mt-2 flex flex-col sm:flex-row gap-3">
            <input
              id="query"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What is the future of AI research in the next 10 years?"
              maxLength={500}
              className="flex-1 border border-line bg-paper-raised px-4 py-3 text-sm outline-none focus:border-accent transition-colors"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-3 bg-ink text-paper text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed hover:bg-accent transition-colors"
            >
              {loading ? "Researching\u2026" : "Run research"}
            </button>
          </div>
        </form>

        {loading && (
          <div className="mt-6 flex items-center gap-3 text-sm text-muted">
            <span className="inline-block w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            <span>Working&hellip; {elapsed}s elapsed</span>
          </div>
        )}

        {!hasRun && (
          <p className="mt-8 text-sm text-muted border-l-2 border-line pl-4">
            Nothing here yet. Try a question with room to research — a trend, a
            comparison, a &quot;what&apos;s the current state of&quot; question.
          </p>
        )}

        {error && (
          <p className="mt-6 text-sm text-flag border border-flag/30 bg-flag/5 px-4 py-3">
            {error}
          </p>
        )}

        {result && <ResultsView result={result} />}
      </main>
    </>
  );
}