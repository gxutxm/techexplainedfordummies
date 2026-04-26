/**
 * ReportScreen.jsx — Stakeholder Sim Communication Evaluation
 * ============================================================
 * Owned by: Pair B / Person 1
 *
 * Renders the evaluator's structured feedback as a printed-magazine-style
 * review. Three exports:
 *
 *   <ReportScreen report={...} onRestart={...} />   - main success state
 *   <ReportLoading />                               - while /evaluate is in flight
 *   <ReportError message={...} onRetry={...} />    - if /evaluate fails
 *
 * The `report` prop must match the EvaluateResponse shape from the backend:
 *   {
 *     clarity:      number (1-10),
 *     tone:         number (1-10),
 *     jargon_score: number (1-10),
 *     jargon_terms: [{ term: string, suggestion: string }],
 *     summary:      string,
 *     top_fix:      string,
 *   }
 *
 * Drop into any React app:
 *   import { ReportScreen } from './components/ReportScreen';
 *   import './components/ReportScreen.css';
 */

import { useEffect, useState } from 'react';
import './ReportScreen.css';

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Snap any numeric input to an integer in [1, 10]. Defensive against bad data. */
const clampScore = (v) => {
  const n = Math.round(Number(v));
  if (Number.isNaN(n)) return 5;
  return Math.max(1, Math.min(10, n));
};

/** Color tier for a score. Used as a CSS class suffix. */
const scoreTier = (v) => {
  const n = clampScore(v);
  if (n >= 8) return 'high';
  if (n >= 5) return 'mid';
  return 'low';
};

/** A score's average for the headline. Plain mean of three dimensions. */
const overallScore = (report) => {
  const sum = clampScore(report.clarity) + clampScore(report.tone) + clampScore(report.jargon_score);
  return Math.round((sum / 3) * 10) / 10; // one decimal
};

/** Word verdict for the overall score — adds character without being patronizing. */
const overallVerdict = (n) => {
  if (n >= 8.5) return 'Exceptional';
  if (n >= 7) return 'Strong';
  if (n >= 5.5) return 'Mixed';
  if (n >= 4) return 'Underwhelming';
  return 'Needs work';
};

/** Format the report for the clipboard — plain text, copy-paste ready for Slack/email. */
const formatForClipboard = (report) => {
  const overall = overallScore(report);
  const lines = [
    'STAKEHOLDER SIM — COMMUNICATION EVALUATION',
    '═'.repeat(45),
    '',
    `Overall:  ${overall} / 10  (${overallVerdict(overall)})`,
    `Clarity:  ${clampScore(report.clarity)} / 10`,
    `Tone:     ${clampScore(report.tone)} / 10`,
    `Jargon:   ${clampScore(report.jargon_score)} / 10  (higher = less jargon)`,
    '',
    '── Summary ──',
    report.summary,
    '',
    '── Biggest fix ──',
    report.top_fix,
  ];

  if (report.jargon_terms && report.jargon_terms.length > 0) {
    lines.push('', '── Jargon flagged ──');
    report.jargon_terms.forEach((j, i) => {
      lines.push(`${i + 1}. "${j.term}" → ${j.suggestion}`);
    });
  }

  return lines.join('\n');
};

// ─── Atomic Components ───────────────────────────────────────────────────────

/** A single big serif score with a 10-block indicator below. */
function Score({ label, value }) {
  const n = clampScore(value);
  const tier = scoreTier(value);

  return (
    <div className="rs-score" data-tier={tier}>
      <div className="rs-score-label">{label}</div>
      <div className="rs-score-value" aria-label={`${label} score: ${n} out of 10`}>
        {n}
      </div>
      <div className="rs-score-indicator" aria-hidden="true">
        {Array.from({ length: 10 }, (_, i) => (
          <span
            key={i}
            className={`rs-score-block ${i < n ? 'rs-score-block--filled' : ''}`}
            style={{ '--block-delay': `${i * 30}ms` }}
          />
        ))}
      </div>
    </div>
  );
}

/** Hairline rule with a centered glyph. Pure decoration. */
function Rule() {
  return (
    <div className="rs-rule" aria-hidden="true">
      <span className="rs-rule-line" />
      <span className="rs-rule-mark">§</span>
      <span className="rs-rule-line" />
    </div>
  );
}

// ─── Main Report ─────────────────────────────────────────────────────────────

export function ReportScreen({ report, onRestart }) {
  const [copied, setCopied] = useState(false);

  // Reset the "Copied!" flash after 2s
  useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 2000);
    return () => clearTimeout(t);
  }, [copied]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formatForClipboard(report));
      setCopied(true);
    } catch (err) {
      // Fallback for older browsers / non-https contexts
      const ta = document.createElement('textarea');
      ta.value = formatForClipboard(report);
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand('copy');
        setCopied(true);
      } catch {
        // last resort: do nothing — at least don't crash
      }
      document.body.removeChild(ta);
    }
  };

  if (!report) return null;

  const overall = overallScore(report);
  const hasJargon = report.jargon_terms && report.jargon_terms.length > 0;

  return (
    <article className="rs-report" aria-labelledby="rs-title">
      {/* Masthead — feels like a real publication */}
      <header className="rs-masthead">
        <div className="rs-masthead-left">
          <span className="rs-eyebrow">Stakeholder Sim</span>
        </div>
        <div className="rs-masthead-right">
          <span className="rs-eyebrow">Communication Review</span>
          <span className="rs-eyebrow rs-eyebrow--muted">
            № {Math.floor(Math.random() * 900) + 100}
          </span>
        </div>
      </header>

      {/* Title and overall verdict */}
      <section className="rs-hero">
        <h1 id="rs-title" className="rs-title">
          The Verdict.
        </h1>
        <div className="rs-overall">
          <span className="rs-overall-value">{overall}</span>
          <span className="rs-overall-divider">/</span>
          <span className="rs-overall-max">10</span>
          <span className="rs-overall-verdict" data-tier={scoreTier(overall)}>
            {overallVerdict(overall)}
          </span>
        </div>
      </section>

      <Rule />

      {/* The three dimension scores */}
      <section className="rs-scores" aria-label="Score breakdown">
        <Score label="Clarity" value={report.clarity} />
        <Score label="Tone" value={report.tone} />
        <Score label="Jargon" value={report.jargon_score} />
      </section>

      <Rule />

      {/* Summary — the editorial body copy */}
      <section className="rs-section rs-summary">
        <h2 className="rs-section-heading">Summary</h2>
        <p className="rs-prose">{report.summary}</p>
      </section>

      <Rule />

      {/* Top fix — the most important takeaway, called out */}
      <section className="rs-section rs-topfix" aria-labelledby="rs-topfix-heading">
        <h2 id="rs-topfix-heading" className="rs-section-heading rs-section-heading--accent">
          The Biggest Fix
        </h2>
        <p className="rs-prose rs-prose--accent">{report.top_fix}</p>
      </section>

      {/* Jargon — only render if Claude flagged any */}
      {hasJargon && (
        <>
          <Rule />
          <section className="rs-section rs-jargon">
            <h2 className="rs-section-heading">Jargon Flagged</h2>
            <ol className="rs-jargon-list">
              {report.jargon_terms.map((j, i) => (
                <li key={i} className="rs-jargon-item">
                  <div className="rs-jargon-term">"{j.term}"</div>
                  <div className="rs-jargon-suggestion">
                    <span className="rs-jargon-arrow" aria-hidden="true">→</span>
                    {j.suggestion}
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </>
      )}

      <Rule />

      {/* Actions */}
      <footer className="rs-actions">
        <button
          type="button"
          className="rs-button rs-button--primary"
          onClick={handleCopy}
          aria-live="polite"
        >
          {copied ? 'Copied to clipboard' : 'Copy report'}
        </button>
        {onRestart && (
          <button
            type="button"
            className="rs-button rs-button--ghost"
            onClick={onRestart}
          >
            Try again
          </button>
        )}
      </footer>

      <div className="rs-colophon" aria-hidden="true">
        — End of report —
      </div>
    </article>
  );
}

// ─── Loading State ───────────────────────────────────────────────────────────

export function ReportLoading() {
  return (
    <div className="rs-report rs-loading" role="status" aria-live="polite">
      <header className="rs-masthead">
        <div className="rs-masthead-left">
          <span className="rs-eyebrow">Stakeholder Sim</span>
        </div>
        <div className="rs-masthead-right">
          <span className="rs-eyebrow">Communication Review</span>
        </div>
      </header>

      <div className="rs-loading-body">
        <div className="rs-loading-mark">§</div>
        <h2 className="rs-loading-title">
          Reading the transcript<span className="rs-loading-dots">
            <span>.</span><span>.</span><span>.</span>
          </span>
        </h2>
        <p className="rs-loading-sub">
          The communication coach is reviewing your responses. This usually takes
          5–10 seconds.
        </p>
      </div>
    </div>
  );
}

// ─── Error State ─────────────────────────────────────────────────────────────

export function ReportError({ message, onRetry, onRestart }) {
  return (
    <div className="rs-report rs-error" role="alert">
      <header className="rs-masthead">
        <div className="rs-masthead-left">
          <span className="rs-eyebrow">Stakeholder Sim</span>
        </div>
        <div className="rs-masthead-right">
          <span className="rs-eyebrow rs-eyebrow--muted">Error</span>
        </div>
      </header>

      <div className="rs-error-body">
        <h2 className="rs-error-title">Something went wrong.</h2>
        <p className="rs-prose">
          {message || 'The evaluator could not generate a report. This is usually transient — try again.'}
        </p>

        <div className="rs-actions">
          {onRetry && (
            <button
              type="button"
              className="rs-button rs-button--primary"
              onClick={onRetry}
            >
              Try again
            </button>
          )}
          {onRestart && (
            <button
              type="button"
              className="rs-button rs-button--ghost"
              onClick={onRestart}
            >
              Start over
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportScreen;
