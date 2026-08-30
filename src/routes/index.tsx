import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Decision Debate Agent" },
      {
        name: "description",
        content: "Three perspectives argue your decision. You make the call.",
      },
      { property: "og:title", content: "Decision Debate Agent" },
      {
        property: "og:description",
        content: "Three perspectives argue your decision. You make the call.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

interface DebateResponse {
  optimist_view: string;
  skeptic_view: string;
  analyst_view: string;
  moderator_output: string;
  verification_retries: number;
  retrieved_context: string;
  safety_category?: "normal" | "crisis" | "medical" | "harmful";
}

interface Perspective {
  key: keyof Pick<DebateResponse, "optimist_view" | "skeptic_view" | "analyst_view">;
  label: string;
  accent: "optimist" | "skeptic" | "analyst";
}

const PERSPECTIVES: Perspective[] = [
  { key: "optimist_view", label: "Optimist", accent: "optimist" },
  { key: "skeptic_view", label: "Skeptic", accent: "skeptic" },
  { key: "analyst_view", label: "Analyst", accent: "analyst" },
];

const ACCENT_STYLES = {
  optimist: {
    dot: "bg-optimist",
    glow: "shadow-[0_18px_44px_-28px_rgba(52,197,132,0.5)]",
  },
  skeptic: {
    dot: "bg-skeptic",
    glow: "shadow-[0_18px_44px_-28px_rgba(242,163,60,0.5)]",
  },
  analyst: {
    dot: "bg-analyst",
    glow: "shadow-[0_18px_44px_-28px_rgba(91,163,224,0.5)]",
  },
};

function PerspectiveCard({
  perspective,
  content,
  index,
}: {
  perspective: Perspective;
  content: string;
  index: number;
}) {
  const styles = ACCENT_STYLES[perspective.accent];

  return (
    <article
      className={`animate-rise rounded-3xl bg-card p-6 ring-1 ring-black/5 ${styles.glow}`}
      style={{ animationDelay: `${0.05 + index * 0.1}s` }}
    >
      <div className="mb-4 flex items-center gap-3">
        <span className="grid size-9 place-items-center rounded-full bg-secondary">
          <span className={`size-3 rounded-full ${styles.dot}`} />
        </span>
        <h3 className="font-serif text-xl font-medium">{perspective.label}</h3>
      </div>
      <ReactMarkdown
        components={{
          ul: ({ children }) => (
            <ul className="space-y-2.5 text-sm leading-relaxed text-ink-soft">{children}</ul>
          ),
          li: ({ children }) => (
            <li className="flex gap-2.5">
              <span className={`mt-1.5 size-1.5 shrink-0 rounded-full ${styles.dot}`} />
              <span>{children}</span>
            </li>
          ),
          p: ({ children }) => <p className="text-sm leading-relaxed text-ink-soft">{children}</p>,
        }}
      >
        {content}
      </ReactMarkdown>
    </article>
  );
}

function LoadingState() {
  return (
    <section className="mt-16 animate-rise" aria-live="polite" aria-busy="true">
      <div className="mb-6 flex items-center gap-4">
        <span className="h-px flex-1 bg-ink/10" />
        <span className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft">
          The briefs
        </span>
        <span className="h-px flex-1 bg-ink/10" />
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="animate-breathe rounded-3xl bg-card p-6 ring-1 ring-black/5 shadow-[0_18px_44px_-28px_rgba(52,197,132,0.5)]">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-full bg-optimist/15">
              <span className="size-3 rounded-full bg-optimist" />
            </span>
            <h3 className="font-serif text-xl font-medium text-ink/60">Optimist</h3>
          </div>
          <div className="space-y-3">
            <div className="h-3 w-3/4 rounded-full bg-ink/10" />
            <div className="h-3 w-full rounded-full bg-ink/10" />
            <div className="h-3 w-5/6 rounded-full bg-ink/10" />
          </div>
        </div>
        <div className="animate-breathe-delayed rounded-3xl bg-card p-6 ring-1 ring-black/5 shadow-[0_18px_44px_-28px_rgba(242,163,60,0.5)]">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-full bg-skeptic/15">
              <span className="size-3 rounded-full bg-skeptic" />
            </span>
            <h3 className="font-serif text-xl font-medium text-ink/60">Skeptic</h3>
          </div>
          <div className="space-y-3">
            <div className="h-3 w-3/4 rounded-full bg-ink/10" />
            <div className="h-3 w-full rounded-full bg-ink/10" />
            <div className="h-3 w-5/6 rounded-full bg-ink/10" />
          </div>
        </div>
        <div className="animate-breathe-delayed-2 rounded-3xl bg-card p-6 ring-1 ring-black/5 shadow-[0_18px_44px_-28px_rgba(91,163,224,0.5)]">
          <div className="mb-4 flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-full bg-analyst/15">
              <span className="size-3 rounded-full bg-analyst" />
            </span>
            <h3 className="font-serif text-xl font-medium text-ink/60">Analyst</h3>
          </div>
          <div className="space-y-3">
            <div className="h-3 w-3/4 rounded-full bg-ink/10" />
            <div className="h-3 w-full rounded-full bg-ink/10" />
            <div className="h-3 w-5/6 rounded-full bg-ink/10" />
          </div>
        </div>
      </div>
    </section>
  );
}

function SafetyMessageCard({ content, context }: { content: string; context?: string }) {
  return (
    <article
      className="animate-rise rounded-[28px] bg-card p-8 ring-1 ring-black/5 shadow-[0_24px_60px_-30px_rgba(59,55,48,0.18)] sm:p-10"
      style={{ animationDelay: "0.15s" }}
    >
      <ReactMarkdown
        components={{
          h1: ({ children }) => (
            <h3 className="font-serif text-2xl font-medium leading-tight text-ink sm:text-3xl">
              {children}
            </h3>
          ),
          h2: ({ children }) => (
            <h3 className="font-serif text-2xl font-medium leading-tight text-ink sm:text-3xl">
              {children}
            </h3>
          ),
          h3: ({ children }) => (
            <h3 className="font-serif text-2xl font-medium leading-tight text-ink sm:text-3xl">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="mt-4 max-w-[52ch] text-base leading-relaxed text-ink-soft">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="mt-4 space-y-2 text-base leading-relaxed text-ink-soft">{children}</ul>
          ),
          li: ({ children }) => (
            <li className="flex gap-2">
              <span className="mt-2 size-1.5 shrink-0 rounded-full bg-plum/60" />
              <span>{children}</span>
            </li>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
      {context && (
        <p className="mt-6 border-t border-ink/10 pt-4 text-xs leading-relaxed text-ink-soft/70">
          Context retrieved: {context}
        </p>
      )}
    </article>
  );
}

function Index() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<DebateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:5000/debate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
      });

      if (!response.ok) {
        throw new Error("The debate server returned " + response.status + ". Please try again.");
      }

      const data = (await response.json()) as DebateResponse;
      setResult(data);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Something went wrong while running the debate.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const retryLabel =
    result && result.verification_retries > 0
      ? "Revised " +
        (result.verification_retries === 1 ? "once" : result.verification_retries + " times") +
        " after review"
      : null;

  return (
    <div className="min-h-screen bg-cream font-sans text-ink antialiased">
      <div className="mx-auto max-w-[1080px] px-6 py-10 sm:py-16">
        {/* Hero */}
        <header className="mx-auto max-w-[40ch] text-center">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-plum ring-1 ring-plum/10">
            A quiet room for hard calls
          </p>
          <h1
            className="font-serif text-[2.75rem] font-medium leading-[1.05] text-balance sm:text-6xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Decision Debate Agent
          </h1>
          <p className="mt-5 text-base leading-relaxed text-pretty text-ink-soft">
            Three perspectives argue your decision. You make the call.
          </p>
        </header>

        {/* Input stage */}
        <section className="mx-auto mt-12 max-w-[640px]">
          <form
            onSubmit={handleSubmit}
            className="rounded-[28px] bg-card p-3 ring-1 ring-black/5 shadow-[0_24px_60px_-30px_rgba(59,55,48,0.35)]"
          >
            <label htmlFor="decision" className="sr-only">
              Your decision
            </label>
            <Textarea
              id="decision"
              rows={4}
              placeholder="Should I leave my stable job to join a small startup as their second hire?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full resize-none border-0 bg-transparent px-4 py-3 text-base leading-relaxed text-ink placeholder:text-ink-soft/60 shadow-none outline-none ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:placeholder:text-ink-soft/40"
            />
            <div className="mt-2 flex items-center justify-between gap-3 px-2 pb-1">
              <span className="text-xs font-medium text-ink-soft/70">Optional context welcome</span>
              <Button
                type="submit"
                disabled={loading || !query.trim()}
                className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-cream transition-transform duration-300 hover:-translate-y-0.5 disabled:opacity-60 disabled:hover:translate-y-0"
              >
                {loading ? "Running..." : "Run the Debate"}
              </Button>
            </div>
          </form>
        </section>

        {/* Error state */}
        {error && (
          <div className="mx-auto mt-8 max-w-[640px] animate-rise">
            <Alert variant="destructive" className="rounded-2xl bg-destructive/15">
              <AlertCircle className="size-4 text-destructive" />
              <AlertTitle className="font-serif text-destructive">
                Could not run the debate
              </AlertTitle>
              <AlertDescription className="text-foreground/90">{error}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Loading state */}
        {loading && <LoadingState />}

        {/* Results */}
        {result && !loading && (
          <section className="mt-16 animate-rise">
            {(!result.safety_category || result.safety_category === "normal") ? (
              <>
                <div className="mb-6 flex items-center gap-4">
                  <span className="h-px flex-1 bg-ink/10" />
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-ink-soft">
                    The briefs
                  </span>
                  <span className="h-px flex-1 bg-ink/10" />
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                  {PERSPECTIVES.map((perspective, index) => (
                    <PerspectiveCard
                      key={perspective.key}
                      perspective={perspective}
                      content={result[perspective.key]}
                      index={index}
                    />
                  ))}
                </div>

                {/* Recommendation */}
                <article
                  className="mt-8 animate-rise rounded-[28px] bg-plum p-8 text-cream shadow-[0_30px_70px_-32px_rgba(107,74,158,0.7)] sm:p-10"
                  style={{ animationDelay: "0.35s" }}
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cream/70">
                      Moderator&apos;s read
                    </p>
                    {retryLabel && (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-cream/90">
                        {retryLabel}
                      </span>
                    )}
                  </div>
                  <ReactMarkdown
                    components={{
                      h1: ({ children }) => (
                        <h3 className="mt-3 font-serif text-2xl font-medium leading-tight sm:text-3xl">
                          {children}
                        </h3>
                      ),
                      h2: ({ children }) => (
                        <h3 className="mt-3 font-serif text-2xl font-medium leading-tight sm:text-3xl">
                          {children}
                        </h3>
                      ),
                      h3: ({ children }) => (
                        <h3 className="mt-3 font-serif text-2xl font-medium leading-tight sm:text-3xl">
                          {children}
                        </h3>
                      ),
                      p: ({ children }) => (
                        <p className="mt-4 max-w-[52ch] text-sm leading-relaxed text-cream/85">
                          {children}
                        </p>
                      ),
                      ul: ({ children }) => (
                        <ul className="mt-4 space-y-2 text-sm leading-relaxed text-cream/85">
                          {children}
                        </ul>
                      ),
                      li: ({ children }) => (
                        <li className="flex gap-2">
                          <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-cream/70" />
                          <span>{children}</span>
                        </li>
                      ),
                    }}
                  >
                    {result.moderator_output}
                  </ReactMarkdown>
                  {result.retrieved_context && (
                    <p className="mt-6 border-t border-cream/10 pt-4 text-xs leading-relaxed text-cream/50">
                      Context retrieved: {result.retrieved_context}
                    </p>
                  )}
                </article>
              </>
            ) : (
              <SafetyMessageCard
                content={result.moderator_output}
                context={result.retrieved_context}
              />
            )}
          </section>
        )}

        {/* Footer */}
        <footer className="mt-14 text-center">
          <p className="font-serif text-lg text-ink/80">
            This is a recommendation, not a decision.
          </p>
          <p className="mt-1 text-sm text-ink-soft">The choice stays with you.</p>
        </footer>
      </div>
    </div>
  );
}
