/**
 * ReportScreen.example.jsx — Standalone preview
 * ==============================================
 * Drop this into any Vite + React app to see the ReportScreen in all
 * three states without connecting to the backend.
 *
 * Quick usage:
 *   1. Copy this file alongside ReportScreen.jsx and ReportScreen.css
 *   2. In your App.jsx:    import ReportScreenExample from './components/ReportScreen.example';
 *                          export default function App() { return <ReportScreenExample />; }
 *   3. npm run dev
 *
 * Or use this as the integration template — copy the fetch logic into
 * your real flow and replace `MOCK_REPORTS.good` with the API response.
 */

import { useState } from 'react';
import { ReportScreen, ReportLoading, ReportError } from './ReportScreen';
import './ReportScreen.css';

// Three mock reports for sanity-checking high / mid / low score rendering.
const MOCK_REPORTS = {
  good: {
    clarity: 9,
    tone: 8,
    jargon_score: 7,
    summary:
      "You did a strong job translating a dense technical concept into something the executive could engage with. Your use of the 'librarian with notes' analogy was particularly effective, and you stayed patient when asked to rephrase. A few moments still leaned on insider vocabulary.",
    top_fix:
      "When introducing a new technical term, define it in the same sentence — don't make the executive ask.",
    jargon_terms: [
      {
        term: 'vector embeddings',
        suggestion:
          "Compressed numerical representations of meaning that let computers compare ideas quickly.",
      },
      {
        term: 'p99 latency',
        suggestion:
          "How slow the system is for the worst 1% of requests — the bad-day number.",
      },
    ],
  },

  mixed: {
    clarity: 6,
    tone: 7,
    jargon_score: 4,
    summary:
      "You showed real depth on the technical mechanics, but the executive needed simpler scaffolding to follow you. Several answers started with implementation details before the 'why' — and a handful of acronyms went undefined.",
    top_fix:
      "Lead every answer with the business outcome before any technical detail.",
    jargon_terms: [
      { term: 'RAG pipeline', suggestion: 'A system that looks information up before answering — like a researcher who consults notes.' },
      { term: 'gradient-boosted ensemble', suggestion: 'A team of small decision-making models that vote on the answer.' },
      { term: 'Champion/Challenger framework', suggestion: 'A system where a new model competes against the current one before replacing it.' },
      { term: 'p99', suggestion: 'The slowest 1% of cases — the worst-but-still-realistic situation.' },
    ],
  },

  poor: {
    clarity: 3,
    tone: 5,
    jargon_score: 2,
    summary:
      "Your responses repeatedly assumed technical fluency the executive doesn't have. Most answers stayed at the level of 'how it works' rather than 'why it matters,' and key terms went unexplained even after the executive asked clarifying questions.",
    top_fix:
      "Pretend the listener has never opened a textbook on this subject — start every answer there.",
    jargon_terms: [
      { term: 'self-attention', suggestion: 'A way for the model to weigh which earlier words matter most when interpreting a new one.' },
      { term: 'long-range dependencies', suggestion: 'Connections between words that are far apart in a sentence or document.' },
      { term: 'Vaswani et al.', suggestion: '(Skip this — it\'s a research citation that means nothing to an executive.)' },
      { term: 'F1 score', suggestion: 'A single number combining how often the model is right and how often it catches what it should.' },
      { term: 'baseline LSTM', suggestion: 'An older type of model used as the comparison point.' },
    ],
  },
};

export default function ReportScreenExample() {
  const [view, setView] = useState('good');

  const renderView = () => {
    switch (view) {
      case 'loading':
        return <ReportLoading />;
      case 'error':
        return (
          <ReportError
            message="The evaluator returned malformed JSON twice. Please try again in a moment."
            onRetry={() => setView('loading')}
            onRestart={() => setView('good')}
          />
        );
      case 'good':
      case 'mixed':
      case 'poor':
        return (
          <ReportScreen
            report={MOCK_REPORTS[view]}
            onRestart={() => setView('good')}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#e8e0cc', padding: '2rem 1rem' }}>
      <div
        style={{
          maxWidth: 720,
          margin: '0 auto 2rem',
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        <strong style={{ alignSelf: 'center', marginRight: 8, color: '#4a463e' }}>
          Preview:
        </strong>
        {['good', 'mixed', 'poor', 'loading', 'error'].map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            style={{
              padding: '6px 14px',
              borderRadius: 999,
              border: '1px solid #1a1a1f',
              background: view === v ? '#1a1a1f' : 'transparent',
              color: view === v ? '#f4ede0' : '#1a1a1f',
              fontSize: 13,
              fontWeight: 500,
              cursor: 'pointer',
              textTransform: 'capitalize',
            }}
          >
            {v}
          </button>
        ))}
      </div>

      {renderView()}
    </div>
  );
}
