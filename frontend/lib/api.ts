const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface Finding {
  content: string;
  source: string | null;
}

export interface ResearchResult {
  query: string;
  plan: string | null;
  final_report: string | null;
  iteration_count: number;
  findings: Finding[];
  sources: string[];
}

export async function runResearch(query: string): Promise<ResearchResult> {
  const res = await fetch(`${API_BASE_URL}/api/research`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}
