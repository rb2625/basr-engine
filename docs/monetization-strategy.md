# BASR Monetization Strategy

## Core Principle
Open code, closed data. The code is Apache 2.0. The moat is the product experience, data quality, and brand.

## Why Open Source Works Here

1. **Running it yourself is harder than using it.** You need:
   - Your own Supabase project + schema setup
   - Your own Groq API key (free tier limited to 200k tokens/day)
   - Your own YouTube API key
   - Your own Telegram bot
   - Vercel deployment + cron setup
   - Training data (we have 546 hand-labeled items)
   - Entity database (40 UAE entities with lat/lng)

2. **The value is the accumulated intelligence.** A clone gets the code but not:
   - The trained n-gram model
   - The eval harness and labeled datasets
   - The curated entity database
   - The anomaly baselines
   - The production pipeline history

3. **Open source builds trust.** Companies like HashiCorp, Supabase, Vercel all have open source cores but profitable businesses.

## Revenue Streams (Phase 7b+)

### 1. Hosted SaaS (Primary)
- **Free tier**: 1 user, 100 docs/day, public dashboard only
- **Pro tier** ($49/month): 5 users, 1000 docs/day, private dashboards, email alerts, API access
- **Enterprise** ($499/month): Unlimited users, custom topics, SLA, dedicated support

### 2. API Access
- Researchers pay for bulk data access
- PR agencies pay for real-time feeds
- Universities pay for academic licenses

### 3. Custom Deployments
- Government entities pay for on-premise deployment
- Banks pay for private instances with their own data sources

### 4. Consulting
- Help orgs set up their own sentiment monitoring
- Custom topic/entity configuration
- Training and support

## What Competitors Charge
- Meltwater: $15,000+/year
- Brandwatch: $36,000+/year
- Talkwalker: Enterprise pricing
- DataEQ: Per-report pricing

BASR at $49/month is 97% cheaper than Meltwater.

## IP Protection (Already Done)
- Apache 2.0 license (patent protection)
- .env files out of git (verified)
- No hardcoded secrets (verified)
- Dashboard uses server-side API routes (service key never reaches browser)

## Next Steps
1. Get 100+ free users (Phase 7a)
2. Collect feedback on what features matter
3. Add Supabase Auth for login (Phase 7b)
4. Add org workspaces (Phase 7b)
5. Launch paid tiers (Phase 7b)
6. University outreach with user proof (Phase 7b)
