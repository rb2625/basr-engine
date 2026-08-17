# BASR dashboard (Phase 3)

Public dashboard for BASR 2.0 - UAE Economic Sentiment Intelligence.
Next.js 14 (App Router) + Tailwind + Leaflet + Recharts, server-rendered data
through a single API route backed by Supabase.

## Views

- **Overview** - KPIs, signal mix, top topics, 30-day volume/sentiment,
  recent stress headlines
- **Map** - entity sentiment map (Leaflet), locations sized by mentions and
  colored by average sentiment
- **Trends** - daily volume + sentiment, stress signals broken down by topic
- **Topics** - the 14-topic taxonomy with doc counts, sentiment, signal mix
- **Feed** - latest classified docs with badges (sentiment, signal, sector,
  sarcasm, topics, locations)
- **Early warning** - anomaly alerts from the Phase 4 ensemble (rolling
  z-score + STL seasonality) with severity and evidence

## Run locally

```bash
cp .env.local.example .env.local   # fill in your Supabase URL + service key
npm install
npm run dev                        # http://localhost:3000
```

The service-role key is server-side only: pages never see it, they read
through `/api/data` (route handlers). Set the same two vars in the Vercel
project environment for deployment.

## Verify the data layer against the live database

```bash
set -a; . ../.env; set +a; npx tsx scripts/smoke.ts
```

This runs the exact aggregation functions the API uses and prints a summary
of every view - it should print `SMOKE OK`.

## Deployment

Push to GitHub, import the repo into Vercel, set the **Root Directory** to
`dashboard`, and add `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` to the
project environment. `vercel.json` pins the framework + build command.
