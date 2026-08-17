"use client";

import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import type { LocationStat } from "@/lib/types";

function colorFor(s: number | null): string {
  if (s == null) return "#5B6B7E";
  if (s >= 0.15) return "#3DD68C";
  if (s <= -0.15) return "#F4656B";
  return "#E7B84E";
}

const EMPTY = { stress: 0, closure: 0, opportunity: 0, neutral: 0 };

export default function MapView({ locations }: { locations: LocationStat[] }) {
  if (!locations.length) {
    return (
      <div className="card flex h-96 items-center justify-center font-mono text-xs text-mute">
        No geocoded sentiment yet - enrichment is running.
      </div>
    );
  }
  return (
    <div className="relative overflow-hidden rounded-[0.9rem] border border-line">
      <MapContainer
        center={[24.7, 54.6]}
        zoom={8}
        scrollWheelZoom
        style={{ height: 520, width: "100%", background: "#0A0E14" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          subdomains="abcd"
        />
        {locations.map((l) => {
          const radius = 8 + Math.min(18, Math.sqrt(l.docs) * 3);
          const mix = l.mix || EMPTY;
          const total = Math.max(1, mix.stress + mix.closure + mix.opportunity + mix.neutral);
          const col = colorFor(l.avgSentiment);
          return (
            <CircleMarker
              key={l.name}
              center={[l.lat, l.lng]}
              radius={radius}
              className="map-marker"
              pathOptions={{
                color: col,
                fillColor: col,
                fillOpacity: 0.6,
                weight: 1.5,
              }}
            >
              <Tooltip direction="top" offset={[0, -4]}>
                <span className="font-semibold capitalize">{l.name}</span>
              </Tooltip>
              <Popup>
                <div className="min-w-[190px] font-mono text-[11px]">
                  <div className="mb-1.5 text-[13px] font-semibold capitalize">
                    {l.name}
                  </div>
                  <div className="flex justify-between text-mute">
                    <span>Docs</span>
                    <strong className="text-text1">{l.docs}</strong>
                  </div>
                  <div className="flex justify-between text-mute">
                    <span>Avg sentiment</span>
                    <strong className={col === "#5B6B7E" ? "text-text1" : ""} style={{ color: col }}>
                      {l.avgSentiment == null ? "n/a" : l.avgSentiment.toFixed(2)}
                    </strong>
                  </div>
                  <div className="mt-1.5 flex justify-between text-mute">
                    <span>Stress / Closure</span>
                    <strong className="text-text1">
                      {mix.stress} / {mix.closure}
                    </strong>
                  </div>
                  <div className="flex justify-between text-mute">
                    <span>Opportunity</span>
                    <strong className="text-text1">{mix.opportunity}</strong>
                  </div>
                  <div className="flex justify-between text-mute">
                    <span>Negative share</span>
                    <strong className="text-text1">
                      {Math.round((100 * (mix.stress + mix.closure)) / total)}%
                    </strong>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      <div className="pointer-events-none absolute left-3 top-3 rounded-lg border border-line bg-ink/75 px-3 py-2 font-mono text-[10px] tracking-wide text-mute backdrop-blur-sm">
        <span className="mr-3 inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-pos" /> positive
        </span>
        <span className="mr-3 inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-gold" /> mixed
        </span>
        <span className="inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-neg" /> negative
        </span>
      </div>
    </div>
  );
}
