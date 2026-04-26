# Person 1 Deliverable — Integration Guide

This package contains everything for the evaluator agent and the report screen.
It's designed to drop into the existing project structure with minimal friction.

```
stakeholder-sim-person1/
├── backend/
│   ├── agents/
│   │   └── evaluator.py        ← REPLACE existing file
│   ├── llm_client.py            ← REPLACE existing file (small additive change)
│   └── test_evaluator.py        ← NEW: standalone test harness
└── frontend/src/components/
    ├── ReportScreen.jsx         ← NEW
    ├── ReportScreen.css         ← NEW
    └── ReportScreen.example.jsx ← NEW: standalone preview (optional)
```

---

## 1. Backend installation (5 minutes)

### Files to drop in

Replace these two files in the existing project. Both are backward-compatible — Pair A's code keeps working without changes.

- `backend/agents/evaluator.py` → replaces existing
- `backend/llm_client.py` → replaces existing

### What changed in `evaluator.py`

| | Before | After |
|---|---|---|
| Bad JSON | Returned hardcoded `5/5/5` fallback (silent failure) | Retries once with stricter prompt; raises `HTTPException(502)` if both fail |
| Temperature | Provider default (~0.7, non-deterministic) | `0.0` for stable JSON |
| Fence stripping | Only handled \`\`\`json fences | Handles fences, preamble, postamble, mixed cases |
| Score validation | Trusted Claude blindly | Clamps to `[1, 10]`, coerces floats, defaults to 5 on garbage |
| Jargon list | Unbounded length | Capped at 5, filters out malformed entries |
| Logging | None | `log.warning` on retry, `log.error` on final failure |

### What changed in `llm_client.py`

Added an optional `temperature` parameter to `chat()`. Existing callers are unaffected — they pass nothing and get the previous default behavior. Only the evaluator passes `temperature=0.0`.

### Verify the backend works

From the `backend/` directory, with your `.env` file set up:

```bash
cd backend
python test_evaluator.py
```

You should see 6 unit tests pass instantly, followed by 2 integration tests that hit the real LLM and return valid scores. Each integration test takes ~5–10 seconds.

If you want to test only the unit tests (no API calls):

```bash
python test_evaluator.py --no-llm
```

---

## 2. Frontend installation (10 minutes)

### Files to drop in

```
frontend/src/components/ReportScreen.jsx
frontend/src/components/ReportScreen.css
frontend/src/components/ReportScreen.example.jsx   (optional, for preview)
```

No additional dependencies. Just React. Fonts (Fraunces + DM Sans) load from Google Fonts via CSS `@import`.

### Preview it standalone (recommended first step)

Before integrating, verify the component renders correctly:

```jsx
// In your App.jsx (temporarily):
import ReportScreenExample from './components/ReportScreen.example';
export default function App() {
  return <ReportScreenExample />;
}
```

Then `npm run dev` — you'll see a preview with toggle buttons for the high/mid/low/loading/error states.

### Wire it into the real flow

This is what your partner (Person 2) will do. Two examples below.

#### Minimal integration

```jsx
import { useState } from 'react';
import { ReportScreen, ReportLoading, ReportError } from './components/ReportScreen';
import './components/ReportScreen.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function ReportPage({ sessionId, onRestart }) {
  const [status, setStatus] = useState('loading'); // 'loading' | 'success' | 'error'
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReport();
  }, [sessionId]);

  const fetchReport = async () => {
    setStatus('loading');
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/session/${sessionId}/evaluate`, {
        method: 'POST',
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `HTTP ${res.status}`);
      }
      setReport(await res.json());
      setStatus('success');
    } catch (e) {
      setError(e.message);
      setStatus('error');
    }
  };

  if (status === 'loading') return <ReportLoading />;
  if (status === 'error')   return <ReportError message={error} onRetry={fetchReport} onRestart={onRestart} />;
  return <ReportScreen report={report} onRestart={onRestart} />;
}
```

That's it. The component handles its own animation, copy-to-clipboard, accessibility, and responsive layout.

---

## 3. Data contract (this is what the API must return)

The `/session/{session_id}/evaluate` endpoint must return JSON matching this shape:

```ts
interface JargonTerm {
  term: string;        // exact phrase from presenter's responses
  suggestion: string;  // plain-language rewrite
}

interface EvaluateResponse {
  clarity: number;        // integer 1-10
  tone: number;           // integer 1-10
  jargon_score: number;   // integer 1-10 (higher = LESS jargon = better)
  jargon_terms: JargonTerm[];  // up to 5
  summary: string;        // 2-3 sentences, addressed to presenter as "you"
  top_fix: string;        // single most impactful change, one sentence
}
```

This matches the existing `EvaluateResponse` Pydantic model in `backend/schemas.py` — no schema changes needed.

---

## 4. What the screen handles automatically

You don't need to worry about any of this — the component takes care of it:

- **Out-of-range scores** are clamped to `[1, 10]`
- **Empty `jargon_terms` array** → the entire jargon section is hidden
- **Missing `onRestart` prop** → the "Try again" button is hidden
- **`navigator.clipboard` unavailable** (older browsers, non-HTTPS) → falls back to `document.execCommand('copy')`
- **Reduced-motion preference** → all animations disabled
- **Mobile (<540px)** → score row stacks vertically, masthead wraps
- **Keyboard navigation** → all buttons have visible focus states (crimson outline)
- **Screen readers** → semantic `<article>`, `<section>`, `aria-label` on scores, `role="status"` on loading, `role="alert"` on error

---

## 5. Coordination with the rest of the team

### What to tell Pair A
The evaluator now raises `HTTPException(502)` if Claude returns malformed JSON twice in a row. They don't need to do anything — FastAPI surfaces the 502 with a clear error message in the `detail` field. The frontend's `<ReportError>` component will display it.

### What to tell Person 2 (your partner)
- Their report-page component just needs to call `POST /session/{id}/evaluate`, then pass the response into `<ReportScreen report={...} onRestart={...} />`.
- The component is self-contained: imports its own CSS, brings its own fonts, handles its own animation.
- They should preview the example file first — it shows all three states without needing the backend to be running.

### Demo recommendations
- **Pre-warm the LLM** before the judges arrive — the first evaluator call takes ~10s, subsequent ones are faster.
- **Show the editorial design intentionally** — pause on the report screen. The serif numbers and parchment background read as *intentional design* in a sea of Tailwind defaults.
- **Click "Copy report"** during the demo — the clipboard format is plain-text and readable. Paste it into Slack or a notes window to show judges it works.

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| 502 on every evaluation | Model returning prose instead of JSON | Check `EVALUATOR_MODEL` in `config.py` — needs to be a model that handles instruction-following well. Sonnet 4.5 or higher recommended. |
| Fonts look wrong | Google Fonts blocked / offline | The CSS falls back to `Iowan Old Style → Georgia → serif` and `system-ui`. The aesthetic still works, just less distinctive. |
| Animation jitters on mount | Slow device | Component honors `prefers-reduced-motion`. Users can disable system-wide. |
| Copy button does nothing | Non-HTTPS dev server + locked-down browser | Component falls back to `execCommand('copy')`. If that also fails (very rare), no error is thrown — silently fails. |
| Score shows "5" for everything | Bad data from backend | Check the backend logs for `Evaluator JSON decode failed` warnings. If retries are firing constantly, the prompt or model needs adjustment. |
