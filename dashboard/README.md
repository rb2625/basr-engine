# BASR Dashboard

Public sentiment intelligence dashboard for the UAE. Built with Next.js 14 (App Router), Tailwind CSS, Recharts, and Leaflet.

## Views

- **Overview** - KPIs, signal mix, top topics, 30-day volume/sentiment, recent stress headlines
- **Map** - entity sentiment map (Leaflet), locations sized by mentions and colored by average sentiment
- **Trends** - daily volume + sentiment, stress signals broken down by topic
- **Topics** - 14-topic taxonomy with doc counts, sentiment, signal mix
- **Feed** - latest classified docs with badges (sentiment, signal, sector, sarcasm, topics, locations)
- **Alerts** - anomaly alerts from the ensemble detector (rolling z-score + STL seasonality)
- **Briefs** - issue briefs with severity, evidence, recommended responses
- **Reports** - daily/weekly intelligence digests

## Run locally

```bash
cp .env.local.example .env.local   # fill in your Supabase URL + keys
npm install
npm run dev                         # http://localhost:3000
```

Server-side API routes read from `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` (never sent to the browser). Client-side pages optionally use `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` for auth features.

## Deployment

The project deploys automatically to Vercel on every push to `main`.

1. Import `rb2625/basr-engine` into Vercel
2. Set **Root Directory** to `dashboard`
3. Add environment variables:
   - `SUPABASE_URL` (server)
   - `SUPABASE_SERVICE_ROLE_KEY` (server)
   - `NEXT_PUBLIC_SUPABASE_URL` (client)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` (client, for auth)
4. Every `git push` triggers a new deployment
