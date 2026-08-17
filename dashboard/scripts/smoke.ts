// Data-layer smoke test: runs the exact aggregation functions the dashboard
// API uses, against the live Supabase database.
//
// Usage (from the dashboard dir, with the root .env exported):
//   set -a; . ../.env; set +a; npx tsx scripts/smoke.ts

import {
  buildAlerts,
  buildBriefs,
  buildFeed,
  buildMap,
  buildOverview,
  buildTopics,
  buildTrends,
} from "../lib/aggregate";

async function main() {
  const overview = await buildOverview();
  console.log("== overview ==");
  console.log("KPIs:", overview.kpis.map((k) => `${k.label}=${k.value}`).join(" | "));
  console.log("mix:", JSON.stringify(overview.mix));
  console.log("topTopics:", overview.topTopics.map((t) => `${t.labelEn}:${t.docs}`).join(", "));
  console.log("series days:", overview.series.length, "| stress today:", overview.series[overview.series.length - 1]?.stress);
  console.log("recentStress:", overview.recentStress.length, "headlines");
  if (overview.recentStress[0]) {
    console.log("  first:", overview.recentStress[0].title.slice(0, 70));
  }

  const map = await buildMap();
  console.log("\n== map ==");
  console.log("locations:", map.locations.length);
  map.locations.slice(0, 5).forEach((l) =>
    console.log(`  ${l.name} (${l.lat.toFixed(3)},${l.lng.toFixed(3)}) docs=${l.docs} avg=${l.avgSentiment}`)
  );

  const trends = await buildTrends();
  console.log("\n== trends ==");
  console.log("series:", trends.series.length, "days | top topics:", trends.topTopicKeys.join(", "));

  const topics = await buildTopics();
  console.log("\n== topics ==");
  topics.topics.slice(0, 8).forEach((t) =>
    console.log(`  ${t.labelEn}: docs=${t.docs} avg=${t.avgSentiment} mix=${JSON.stringify(t.mix)}`)
  );

  const feed = await buildFeed(10);
  console.log("\n== feed ==");
  console.log("totalClassified:", feed.totalClassified, "| items:", feed.items.length);
  feed.items.slice(0, 3).forEach((f) =>
    console.log(`  [${f.signal_type}/${f.sentiment_label}] ${f.title.slice(0, 60)}`)
  );

  const alerts = await buildAlerts();
  console.log("\n== alerts ==");
  console.log("alerts:", alerts.alerts.length, "| open:", alerts.open, "| critical:", alerts.critical);

  const briefs = await buildBriefs();
  console.log("\n== briefs ==");
  console.log("briefs:", briefs.briefs.length, "| published:", briefs.published, "| critical:", briefs.critical);
  if (briefs.briefs[0]) {
    console.log("  first:", briefs.briefs[0].title.slice(0, 70), "|", briefs.briefs[0].severity);
  }
  console.log("\nSMOKE OK");
}

main().catch((err) => {
  console.error("SMOKE FAILED:", err);
  process.exit(1);
});
