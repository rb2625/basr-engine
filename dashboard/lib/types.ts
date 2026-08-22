// Shared shapes between the API route and the UI.

export type SignalType = "stress" | "closure" | "opportunity" | "neutral";
export type SentimentLabel = "positive" | "negative" | "neutral" | "mixed";

export interface RawDoc {
  id: number;
  source: string;
  title: string | null;
  published_at: string | null;
  text?: string;
}

export interface Classification {
  raw_doc_id: number;
  sentiment_score: number | null;
  sentiment_label: SentimentLabel | null;
  signal_type: SignalType | null;
  sector: string | null;
  emotion: string | null;
  sarcasm: boolean | null;
  model_version: string | null;
  confidence: number | null;
}

export interface TopicRow {
  id: number;
  key: string;
  label_en: string;
  label_ar: string | null;
}

export interface DocTopic {
  doc_id: number;
  topic_id: number;
  score: number | null;
}

export interface EntityRow {
  id: number;
  name: string;
  type: string;
  normalized: string;
  lat: number | null;
  lng: number | null;
}

export interface DocEntity {
  doc_id: number;
  entity_id: number;
  role: string | null;
}

export interface Kpi {
  label: string;
  value: string;
  sub: string;
}

export interface SignalMix {
  stress: number;
  closure: number;
  opportunity: number;
  neutral: number;
}

export interface DayPoint {
  date: string; // YYYY-MM-DD
  volume: number;
  avgSentiment: number | null;
  stress: number;
  stressByTopic: Record<string, number>;
}

export interface TopicStat {
  key: string;
  labelEn: string;
  docs: number;
  avgSentiment: number | null;
  mix: SignalMix;
  latest: string | null;
}

export interface LocationStat {
  name: string;
  lat: number;
  lng: number;
  docs: number;
  avgSentiment: number | null;
  mix: SignalMix;
}

export interface FeedItem {
  id: number;
  title: string;
  source: string;
  published_at: string | null;
  sentiment_label: SentimentLabel | null;
  signal_type: SignalType | null;
  sector: string | null;
  emotion: string | null;
  sarcasm: boolean | null;
  confidence: number | null;
  model_version: string | null;
  topics: string[]; // label_en
  locations: string[];
}

export interface OverviewData {
  kpis: Kpi[];
  mix: SignalMix;
  topTopics: { key: string; labelEn: string; docs: number; avgSentiment: number | null }[];
  series: DayPoint[];
  recentAlerts: { id: number; title: string; severity: string; status: string; createdAt: string | null }[];
}

export interface MapData {
  locations: LocationStat[];
  series: DayPoint[];
}

export interface TrendsData {
  series: DayPoint[];
  topTopicKeys: string[];
}

export interface TopicsData {
  topics: TopicStat[];
}

export interface FeedData {
  items: FeedItem[];
  totalClassified: number;
}

export interface AlertItem {
  id: number;
  title: string;
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  bucketStart: string | null;
  evidence: { id: number; title: string; source: string; url?: string }[];
  createdAt: string | null;
}

export interface AlertsData {
  alerts: AlertItem[];
  open: number;
  critical: number;
}

export interface BriefItem {
  id: number;
  alertId: number | null;
  title: string;
  summary: string;
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  recommendedResponse: { action: string; owner: string; rationale: string }[];
  evidence: {
    title?: string;
    url?: string;
    source?: string;
    severity_justification?: string;
    severity_score?: number;
    trajectory?: { date: string; volume: number; flag: boolean }[];
  }[];
  modelVersion: string;
  createdAt: string | null;
}

export interface BriefsData {
  briefs: BriefItem[];
  published: number;
  critical: number;
}

export interface ReportItem {
  id: number;
  kind: "daily" | "weekly" | "org";
  title: string;
  periodStart: string | null;
  periodEnd: string | null;
  narrative: string;
  headlines: string[];
  stats: {
    current_volume?: number;
    prior_volume?: number;
    volume_delta_pct?: number | null;
    sentiment_avg?: number | null;
    open_alerts?: number;
    top_topics?: { topic: string; volume: number }[];
    top_emirates?: { emirate: string; volume: number }[];
    top_sectors?: { sector: string; volume: number }[];
  };
  deliveryStatus: string;
  channel: string | null;
  createdAt: string | null;
}

export interface ReportsData {
  reports: ReportItem[];
}
