# STATUS.md — Hackathon Source of Truth

Update this every ~45 minutes. Keep it short.

---

## Pair A (Backend)

- [x] FastAPI app running
- [x] CORS configured
- [x] Session store (in-memory dict)
- [x] schemas.py (shared contract)
- [x] /session/start endpoint
- [x] /session/message endpoint
- [x] /session/{id}/evaluate endpoint (stub — Pair B fills evaluator logic)
- [x] Interviewer Agent (executive persona, MAX_TURNS=6)
- [x] Evaluator Agent scaffold (Pair B owns implementation)
- [x] /samples endpoint
- [ ] Speech-to-text integration (partner's task)

**Currently:** Base backend complete, ready for integration

**Blocked on:** Nothing — Pair B can connect now using the contract

**Last Commit:** (update this)

---

## Pair B (Frontend)

- [ ] Screen 1: Paste text landing
- [ ] Screen 2: Chat interface
- [ ] Screen 3: Final report page
- [ ] Connected to real backend

**Currently:** (Pair B fills this in)

**Blocked on:** (Pair B fills this in)

**Last Commit:** (update this)

---

## Integration Checklist

- [ ] Hour 0:30 — Contract locked (schemas.py + types.ts match)
- [ ] Hour 2:00 — Skeleton sync (frontend talks to hardcoded backend)
- [ ] Hour 4:00 — Real Claude sync (full end-to-end demo)
- [ ] Hour 5:00 — Demo lock (no more features)
