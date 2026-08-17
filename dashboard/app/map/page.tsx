"use client";

import dynamic from "next/dynamic";
import Reveal from "@/components/Reveal";
import Section from "@/components/Section";
import { useApi } from "@/components/useApi";
import type { MapData } from "@/lib/types";

const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="card flex h-[520px] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="skeleton h-4 w-40 rounded" />
        <div className="skeleton h-4 w-56 rounded" />
      </div>
    </div>
  ),
});

export default function MapPage() {
  const { data, error, loading } = useApi<MapData>("map");
  return (
    <div className="space-y-6">
      <div className="mb-7">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-gold">
          Geospatial / coverage
        </div>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-text1 sm:text-3xl">
          Entity sentiment map
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-mute">
          Average sentiment and signal mix per UAE location, sized by mention
          volume. Coordinates come from the BASR gazetteer - curated, not a
          third-party API.
        </p>
      </div>

      <Reveal>
        {loading ? (
          <div className="card flex h-[520px] items-center justify-center">
            <div className="skeleton h-4 w-56 rounded" />
          </div>
        ) : error ? (
          <div className="card border-neg/30 p-6 text-sm text-neg">{error}</div>
        ) : (
          <MapView locations={data?.locations || []} />
        )}
      </Reveal>

      <Reveal delay={120}>
        <Section kicker="Method" title="How locations are scored">
          <p className="text-sm leading-relaxed text-mute">
            Every raw doc is tagged with up to three entities by the zero-token
            gazetteer layer. Each location aggregates the sentiment of the docs
            that mention it; the marker color is the average sentiment and the
            size is mention volume. Negative share is the fraction of docs with
            a stress or closure signal.
          </p>
        </Section>
      </Reveal>
    </div>
  );
}
