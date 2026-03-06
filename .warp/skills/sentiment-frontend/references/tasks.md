# Front-End Tasks — Sentiment Dashboard

## Current State
The Next.js 16 dashboard (`ui/`) has a single page (`src/app/page.tsx`) with:
- SSE connection to `GET /stream/sentiment` for live updates
- Initial summary fetch from `GET /sentiment/summary`
- Area chart (Recharts) showing score over time
- Live event feed with label icons
- Stat cards (total, positive %, neutral %, negative %)
- Tailwind v4 styling with dark mode support

## Tasks to Complete

### Source Filtering
- Add a source selector (YouTube / Reddit / Reviews) that filters the summary and live feed
- The `GET /sentiment/summary` endpoint already accepts a `source` query param but the UI doesn't use it
- Filter the SSE event feed client-side by source type

### Time-Window Controls
- Add time-range selectors (last 1h, 6h, 24h, 7d) for the chart and summary stats
- The backend `aggregates_windowed` table supports 1m, 5m, and 1h buckets but no API endpoint exposes them yet — coordinate with back-end to add `GET /sentiment/aggregates`

### Authentication Integration
- Add a login page/modal that calls `POST /auth/login` and stores the JWT
- Protect the dashboard behind authentication
- Show the logged-in user's email in the header
- Handle token expiration (60-minute default) with redirect to login

### Component Extraction
- Extract `StatCard` from `page.tsx` into its own component file under `src/components/`
- Extract the chart section into a `SentimentChart` component
- Extract the live feed into a `LiveEventFeed` component

### Error Handling & Reconnection
- Show a user-visible error banner when the initial `/sentiment/summary` fetch fails (currently only logs to console)
- Implement SSE auto-reconnect with exponential backoff when `eventSource.onerror` fires
- Add a loading skeleton while the initial summary is being fetched

### Multi-Page Routing
- Add a `/history` page for browsing past sentiment results with pagination
- Add an `/ingest` page for triggering YouTube or Reddit ingestion from the UI (requires new back-end endpoints)

### Build & Lint Cleanup
- Ensure `npm run build` produces zero warnings
- Ensure `npm run lint` (ESLint 9) passes cleanly
- Add TypeScript strict mode checks in `tsconfig.json`
