export default function Header() {
  return (
    <header className="border-b border-line">
      <div className="max-w-3xl mx-auto px-6 py-5 flex items-baseline justify-between">
        <span className="font-serif text-lg">Multi-Agent Researcher</span>
        <span className="font-mono text-xs text-muted">supervisor · researcher · critic · writer</span>
      </div>
    </header>
  );
}