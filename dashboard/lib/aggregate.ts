// Dashboard data layer: pulls the small BASR tables from Supabase and
// aggregates them into the view payloads the UI renders. Volumes are small
// (hundreds to low thousands of rows), so fetching whole tables and joining
// in TypeScript is both simple and fast - no PostgREST join gymnastics.
//
// Everything here is pure + testable (scripts/smoke.mjs runs the same
// functions against the live database).

import { getClient } from "./supabase";
import type {
  AlertItem,
  AlertsData,
  BriefItem,
  BriefsData,
  Classification,
  DayPoint,
  DocEntity,
  DocTopic,
  EntityRow,
  FeedItem,
  LocationStat,
  MapData,
  OverviewData,
  RawDoc,
  ReportItem,
  ReportsData,
  SignalMix,
  TopicRow,
  TopicStat,
  TopicsData,
  TrendsData,
  FeedData,
} from "./types";

const DAY_MS = 24 * 60 * 60 * 1000;

function isoDay(ts: string | null): string {
  if (!ts) return "";
  return ts.slice(0, 10);
}

function daysAgo(n: number): string {
  return isoDay(new Date(Date.now() - n * DAY_MS).toISOString());
}

function clamp(v: number | null | undefined): number | null {
  if (v == null || Number.isNaN(v)) return null;
  return Math.max(-1, Math.min(1, Number(v)));
}

function emptyMix(): SignalMix {
  return { stress: 0, closure: 0, opportunity: 0, neutral: 0 };
}

function addToMix(mix: SignalMix, signal: string | null) {
  if (signal === "stress") mix.stress += 1;
  else if (signal === "closure") mix.closure += 1;
  else if (signal === "opportunity") mix.opportunity += 1;
  else mix.neutral += 1;
}

function avg(nums: number[]): number | null {
  if (!nums.length) return null;
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}

async function fetchAll<T>(
  table: string,
  select: string
): Promise<T[]> {
  const client = getClient();
  const { data, error } = await client.from(table).select(select);
  if (error) throw error;
  return (data || []) as T[];
}

async function fetchBase() {
  const [rawDocs, classifications, topics, docTopics, entities, docEntities] =
    await Promise.all([
      fetchAll<RawDoc>("raw_docs", "id,source,title,published_at"),
      fetchAll<Classification>(
        "classifications",
        "raw_doc_id,sentiment_score,sentiment_label,signal_type,sector,emotion,sarcasm,model_version,confidence"
      ),
      fetchAll<TopicRow>("topics", "id,key,label_en,label_ar"),
      fetchAll<DocTopic>("doc_topics", "doc_id,topic_id,score"),
      fetchAll<EntityRow>("entities", "id,name,type,normalized,lat,lng"),
      fetchAll<DocEntity>("doc_entities", "doc_id,entity_id,role"),
    ]);
  return { rawDocs, classifications, topics, docTopics, entities, docEntities };
}

function buildSeries(
  rawDocs: RawDoc[],
  classifications: Classification[],
  days: number,
  docTopicKeys: Map<number, string[]>
): DayPoint[] {
  const byDoc = new Map<number, Classification>();
  for (const c of classifications) byDoc.set(c.raw_doc_id, c);

  const start = daysAgo(days - 1);
  const buckets = new Map<string, DayPoint>();
  for (let i = days - 1; i >= 0; i--) {
    const d = daysAgo(i);
    buckets.set(d, {
      date: d,
      volume: 0,
      avgSentiment: null,
      stress: 0,
      stressByTopic: {},
    });
  }

  for (const doc of rawDocs) {
    const day = isoDay(doc.published_at);
    if (!day || day < start || !buckets.has(day)) continue;
    const c = byDoc.get(doc.id);
    if (!c) continue;
    const bucket = buckets.get(day)!;
    bucket.volume += 1;
    if (c.signal_type === "stress") {
      bucket.stress += 1;
      for (const key of docTopicKeys.get(doc.id) || []) {
        bucket.stressByTopic[key] = (bucket.stressByTopic[key] || 0) + 1;
      }
    }
  }

  // One pass for sentiment average per day.
  const sentPerDay = new Map<string, number[]>();
  for (const doc of rawDocs) {
    const day = isoDay(doc.published_at);
    if (!day || !buckets.has(day)) continue;
    const c = byDoc.get(doc.id);
    const s = clamp(c?.sentiment_score);
    if (s == null) continue;
    const arr = sentPerDay.get(day) || [];
    arr.push(s);
    sentPerDay.set(day, arr);
  }
  Array.from(sentPerDay.entries()).forEach(([day, arr]) => {
    buckets.get(day)!.avgSentiment = Number(avg(arr)!.toFixed(3));
  });

  return Array.from(buckets.values());
}

// ---------------------------------------------------------------------------
// Views
// ---------------------------------------------------------------------------

export async function buildOverview(): Promise<OverviewData> {
  const { rawDocs, classifications, topics, docTopics, entities, docEntities } =
    await fetchBase();

  const mix = emptyMix();
  let sentimentSum = 0;
  let sentimentN = 0;
  for (const c of classifications) {
    addToMix(mix, c.signal_type);
    const s = clamp(c.sentiment_score);
    if (s != null) {
      sentimentSum += s;
      sentimentN += 1;
    }
  }

  const classified = classifications.length;
  const total = rawDocs.length;
  const avgSentiment = sentimentN
    ? Number((sentimentSum / sentimentN).toFixed(3))
    : null;

  // Top topics by doc count.
  const topicById = new Map(topics.map((t) => [t.id, t]));
  const docTopicCount = new Map<number, number>();
  const docTopicSent = new Map<number, number[]>();
  const docTopicKeys = new Map<number, string[]>();
  for (const dt of docTopics) {
    const t = topicById.get(dt.topic_id);
    if (!t) continue;
    docTopicCount.set(t.id, (docTopicCount.get(t.id) || 0) + 1);
    const doc = rawDocs.find((r) => r.id === dt.doc_id);
    if (doc) {
      const keys = docTopicKeys.get(doc.id) || [];
      if (!keys.includes(t.key)) keys.push(t.key);
      docTopicKeys.set(doc.id, keys);
    }
  }
  const byClass = new Map(classifications.map((c) => [c.raw_doc_id, c]));
  for (const dt of docTopics) {
    const c = byClass.get(dt.doc_id);
    const s = clamp(c?.sentiment_score);
    if (s == null) continue;
    const arr = docTopicSent.get(dt.topic_id) || [];
    arr.push(s);
    docTopicSent.set(dt.topic_id, arr);
  }

  const topTopics = [...docTopicCount.entries()]
    .map(([topicId, docs]) => {
      const t = topicById.get(topicId)!;
      const s = docTopicSent.get(topicId) || [];
      return {
        key: t.key,
        labelEn: t.label_en,
        docs,
        avgSentiment: s.length ? Number(avg(s)!.toFixed(3)) : null,
      };
    })
    .sort((a, b) => b.docs - a.docs)
    .slice(0, 8);

  // Recent stress headlines for the overview strip.
  const recent = buildFeedItems(rawDocs, classifications, docTopics, topicById,
    entities, docEntities, 6, "stress");

  return {
    kpis: [
      { label: "Total docs", value: String(total), sub: "across all sources" },
      { label: "Classified", value: String(classified), sub: `${total ? Math.round((100 * classified) / total) : 0}% of corpus` },
      { label: "Stress signals", value: String(mix.stress), sub: `${mix.stress ? Math.round((100 * mix.stress) / Math.max(1, mix.stress + mix.closure + mix.opportunity)) : 0}% of non-neutral` },
      { label: "Avg sentiment", value: avgSentiment == null ? "n/a" : avgSentiment.toFixed(2), sub: "scaled -1.0 .. 1.0" },
    ],
    mix,
    topTopics,
    series: buildSeries(rawDocs, classifications, 30, docTopicKeys),
    recentStress: recent,
  };
}

export async function buildMap(): Promise<MapData> {
  const { rawDocs, classifications, topics, docTopics, entities, docEntities } =
    await fetchBase();

  const locById = new Map(
    entities.filter((e) => e.type === "location" && e.lat != null && e.lng != null)
      .map((e) => [e.id, e])
  );
  const byClass = new Map(classifications.map((c) => [c.raw_doc_id, c]));

  const perLocation = new Map<number, { scores: number[]; mix: SignalMix }>();
  for (const de of docEntities) {
    const loc = locById.get(de.entity_id);
    if (!loc) continue;
    const c = byClass.get(de.doc_id);
    if (!c) continue;
    let acc = perLocation.get(loc.id);
    if (!acc) {
      acc = { scores: [], mix: emptyMix() };
      perLocation.set(loc.id, acc);
    }
    const s = clamp(c.sentiment_score);
    if (s != null) acc.scores.push(s);
    addToMix(acc.mix, c.signal_type);
  }

  const docTopicKeys = new Map<number, string[]>();
  const topicById = new Map(topics.map((t) => [t.id, t]));
  for (const dt of docTopics) {
    const t = topicById.get(dt.topic_id);
    if (!t) continue;
    const keys = docTopicKeys.get(dt.doc_id) || [];
    if (!keys.includes(t.key)) keys.push(t.key);
    docTopicKeys.set(dt.doc_id, keys);
  }

  const locations: LocationStat[] = [...perLocation.entries()]
    .map(([id, acc]) => {
      const loc = locById.get(id)!;
      const docs = acc.scores.length;
      return {
        name: loc.name,
        lat: loc.lat!,
        lng: loc.lng!,
        docs,
        avgSentiment: docs ? Number(avg(acc.scores)!.toFixed(3)) : null,
        mix: acc.mix,
      };
    })
    .sort((a, b) => b.docs - a.docs)
    .slice(0, 60);

  return {
    locations,
    series: buildSeries(rawDocs, classifications, 30, docTopicKeys),
  };
}

export async function buildTrends(): Promise<TrendsData> {
  const { rawDocs, classifications, topics, docTopics } = await fetchBase();
  const topicById = new Map(topics.map((t) => [t.id, t]));
  const docTopicKeys = new Map<number, string[]>();
  const topicDocCount = new Map<string, number>();
  for (const dt of docTopics) {
    const t = topicById.get(dt.topic_id);
    if (!t) continue;
    const keys = docTopicKeys.get(dt.doc_id) || [];
    if (!keys.includes(t.key)) keys.push(t.key);
    docTopicKeys.set(dt.doc_id, keys);
    topicDocCount.set(t.key, (topicDocCount.get(t.key) || 0) + 1);
  }
  const series = buildSeries(rawDocs, classifications, 30, docTopicKeys);
  const topTopicKeys = [...topicDocCount.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([k]) => k);
  return { series, topTopicKeys };
}

export async function buildTopics(): Promise<TopicsData> {
  const { rawDocs, classifications, topics, docTopics } = await fetchBase();
  const topicById = new Map(topics.map((t) => [t.id, t]));
  const byClass = new Map(classifications.map((c) => [c.raw_doc_id, c]));

  const stats = new Map<number, { docs: number; scores: number[]; mix: SignalMix; latest: string | null }>();
  for (const dt of docTopics) {
    const t = topicById.get(dt.topic_id);
    if (!t) continue;
    let acc = stats.get(t.id);
    if (!acc) {
      acc = { docs: 0, scores: [], mix: emptyMix(), latest: null };
      stats.set(t.id, acc);
    }
    acc.docs += 1;
    const c = byClass.get(dt.doc_id);
    const s = clamp(c?.sentiment_score);
    if (s != null) acc.scores.push(s);
    addToMix(acc.mix, c?.signal_type ?? null);
    const doc = rawDocs.find((r) => r.id === dt.doc_id);
    const d = doc?.published_at || "";
    if (!acc.latest || d > acc.latest) acc.latest = d;
  }

  const result: TopicStat[] = [...stats.entries()]
    .map(([id, acc]) => {
      const t = topicById.get(id)!;
      return {
        key: t.key,
        labelEn: t.label_en,
        docs: acc.docs,
        avgSentiment: acc.scores.length ? Number(avg(acc.scores)!.toFixed(3)) : null,
        mix: acc.mix,
        latest: acc.latest,
      };
    })
    .sort((a, b) => b.docs - a.docs);
  return { topics: result };
}

export async function buildBriefs(): Promise<BriefsData> {
  const client = getClient();
  const { data, error } = await client
    .from("briefs")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(30);
  if (error) throw new Error(error.message || "briefs query failed");
  const briefs = ((data || []) as BriefRow[]).map((b) => ({
    id: b.id,
    alertId: b.alert_id,
    title: b.title,
    summary: b.summary,
    severity: b.severity,
    status: b.status,
    recommendedResponse: (b.recommended_response || []) as BriefItem["recommendedResponse"],
    evidence: (b.evidence || []) as BriefItem["evidence"],
    modelVersion: b.model_version,
    createdAt: b.created_at,
  }));
  return {
    briefs,
    published: briefs.filter((b) => b.status === "published").length,
    critical: briefs.filter((b) => b.severity === "critical").length,
  };
}

interface BriefRow {
  id: number;
  alert_id: number | null;
  title: string;
  summary: string;
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  recommended_response: unknown;
  evidence: unknown;
  model_version: string;
  created_at: string | null;
}

export async function buildReports(): Promise<ReportsData> {
  const client = getClient();
  const { data, error } = await client
    .from("reports")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(20);
  if (error) throw new Error(error.message || "reports query failed");
  const reports = ((data || []) as ReportRow[]).map((r) => {
    const body = (r.body || {}) as {
      narrative?: string;
      headlines?: string[];
      stats?: ReportItem["stats"];
    };
    return {
      id: r.id,
      kind: r.kind,
      title: r.title,
      periodStart: r.period_start,
      periodEnd: r.period_end,
      narrative: body.narrative || "",
      headlines: body.headlines || [],
      stats: body.stats || {},
      deliveryStatus: r.delivery_status,
      channel: r.channel,
      createdAt: r.created_at,
    };
  });
  return { reports };
}

interface ReportRow {
  id: number;
  kind: "daily" | "weekly" | "org";
  title: string;
  period_start: string | null;
  period_end: string | null;
  body: unknown;
  delivery_status: string;
  channel: string | null;
  created_at: string | null;
}

export async function buildFeed(limit = 30): Promise<FeedData> {
  const { rawDocs, classifications, topics, docTopics, entities, docEntities } =
    await fetchBase();
  const topicById = new Map(topics.map((t) => [t.id, t]));
  return {
    items: buildFeedItems(rawDocs, classifications, docTopics, topicById,
      entities, docEntities, limit, null),
    totalClassified: classifications.length,
  };
}

export async function buildAlerts(): Promise<AlertsData> {
  const client = getClient();
  const { data, error } = await client
    .from("alerts")
    .select("id,title,severity,status,evidence,created_at,time_series_id")
    .order("created_at", { ascending: false })
    .limit(40);
  if (error) throw new Error(error.message || "alerts query failed");
  const rows = (data || []) as {
    id: number;
    title: string;
    severity: "low" | "medium" | "high" | "critical";
    status: string;
    evidence: { id: number; title: string; source: string; url?: string }[];
    created_at: string | null;
    time_series_id: number | null;
  }[];

  // Map bucket starts for evidence context (the anomaly scan dates).
  const tsIds = [...new Set(rows.map((r) => r.time_series_id).filter(Boolean))];
  const tsBy = new Map<number, string>();
  if (tsIds.length) {
    const { data: ts } = await client
      .from("time_series")
      .select("id,bucket_start")
      .in("id", tsIds);
    if (!ts) throw new Error("time_series lookup failed");
    for (const t of ts as { id: number; bucket_start: string }[]) {
      tsBy.set(t.id, t.bucket_start);
    }
  }

  const alerts: AlertItem[] = rows.map((r) => ({
    id: r.id,
    title: r.title,
    severity: r.severity,
    status: r.status,
    bucketStart: r.time_series_id != null ? tsBy.get(r.time_series_id) || null : null,
    evidence: (r.evidence || []).slice(0, 3),
    createdAt: r.created_at,
  }));
  return {
    alerts,
    open: alerts.filter((a) => a.status === "open").length,
    critical: alerts.filter((a) => a.severity === "critical").length,
  };
}

// Shared feed builder (internal).
function buildFeedItems(
  rawDocs: RawDoc[],
  classifications: Classification[],
  docTopics: DocTopic[],
  topicById: Map<number, TopicRow>,
  entities: EntityRow[],
  docEntities: DocEntity[],
  limit: number,
  onlySignal: string | null
): FeedItem[] {
  const byClass = new Map(classifications.map((c) => [c.raw_doc_id, c]));
  const topicsByDoc = new Map<number, string[]>();
  for (const dt of docTopics) {
    const t = topicById.get(dt.topic_id);
    if (!t) continue;
    const arr = topicsByDoc.get(dt.doc_id) || [];
    if (!arr.includes(t.label_en)) arr.push(t.label_en);
    topicsByDoc.set(dt.doc_id, arr);
  }
  const locById = new Map(entities.map((e) => [e.id, e]));
  const locsByDoc = new Map<number, string[]>();
  for (const de of docEntities) {
    const loc = locById.get(de.entity_id);
    if (!loc) continue;
    const arr = locsByDoc.get(de.doc_id) || [];
    if (!arr.includes(loc.name)) arr.push(loc.name);
    locsByDoc.set(de.doc_id, arr);
  }

  const items: FeedItem[] = [];
  for (const doc of rawDocs) {
    const c = byClass.get(doc.id);
    if (!c) continue;
    if (onlySignal && c.signal_type !== onlySignal) continue;
    items.push({
      id: doc.id,
      title: doc.title || "Untitled",
      source: doc.source,
      published_at: doc.published_at,
      sentiment_label: c.sentiment_label,
      signal_type: c.signal_type,
      sector: c.sector,
      emotion: c.emotion,
      sarcasm: c.sarcasm,
      confidence: c.confidence,
      model_version: c.model_version,
      topics: topicsByDoc.get(doc.id) || [],
      locations: locsByDoc.get(doc.id) || [],
    });
  }
  items.sort((a, b) => (b.published_at || "").localeCompare(a.published_at || ""));
  return items.slice(0, limit);
}

// ---------------------------------------------------------------------------
// Feedback
// ---------------------------------------------------------------------------
export async function buildFeedback() {
  const client = getClient();
  const { data, error } = await client
    .from("feedback")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(100);
  if (error) throw error;
  return { items: data || [], total: data?.length || 0 };
}
