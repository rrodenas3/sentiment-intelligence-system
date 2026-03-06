---
name: sentiment-frontend
description: >
  Build and extend the Next.js sentiment dashboard (ui/ directory). Use this skill when working on
  front-end tasks for the real-time sentiment intelligence system, including: adding source filtering,
  time-window controls, authentication UI, component extraction, SSE error handling and reconnection,
  multi-page routing, or build/lint fixes. Triggers on any dashboard, UI, React, Next.js, chart,
  SSE client, or front-end related work in the sentiment project.
---

# Sentiment Front-End Skill

## Context

The dashboard is a Next.js 16 app in `ui/` using React 19, Recharts, Tailwind v4, and Framer Motion.
It connects to the FastAPI backend at `NEXT_PUBLIC_API_BASE_URL` (default `http://127.0.0.1:8000`).

Key files:
- `ui/src/app/page.tsx` - Single-page dashboard (all current UI lives here)
- `ui/src/lib/utils.ts` - `cn()` utility (clsx + tailwind-merge)
- `ui/package.json` - Scripts: `dev`, `build`, `start`, `lint`

## API Contracts

The UI consumes these backend endpoints:
- `GET /sentiment/summary` - Returns `{ count, by_label: { positive, neutral, negative }, recent: [...] }`
- `GET /stream/sentiment` - SSE stream of `{ event_id, label, score, confidence, model_version, scored_at_utc }`
- `POST /analyze/text` - `{ text }` -> `{ label, score, confidence, model_version }`
- `POST /auth/login` - `{ email, password }` -> `{ access_token, token_type }`

## Task Reference

Read [references/tasks.md](references/tasks.md) for the complete task list before starting work.

## Workflow

1. Read `references/tasks.md` to identify the relevant task
2. Work from the `ui/` directory of the agentcode repo
3. Run `npm run dev` to start the dev server
4. After changes, verify with `npm run build` and `npm run lint`
5. Maintain dark mode support in all new components (use `dark:` Tailwind variants)
6. Keep TypeScript types aligned with the backend Pydantic schemas in `src/mswia/schemas.py`