"use client";

import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from "react-leaflet";
import type { LocationStat } from "@/lib/types";

function colorFor(s: number | null): string {
  if (s == null) return "#a1a1aa";
  if (s >= 0.15) return "#10b981";
  if (s <= -0.15) return "#ef4444";
  return "#f59e0b";
}

const EMPTY = { stress: 0, closure: 0, opportunity: 0, neutral: 0 };

export default function MapView({ locations }: { locations: LocationStat[] }) {
  if (!locations.length) {
    return (
      <div className="flex h-96 items-center justify-center rounded-xl border border-zinc-200 bg-white text-sm text-zinc-400">
        No geocoded sentiment yet - enrichment is running.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 shadow-sm">
      <MapContainer
        center={[24.7, 54.6]}
        zoom={8}
        scrollWheelZoom
        style={{ height: 520, width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {locations.map((l) => {
          const radius = 7 + Math.min(18, Math.sqrt(l.docs) * 3);
          const mix = l.mix || EMPTY;
          const total = Math.max(1, mix.stress + mix.closure + mix.opportunity + mix.neutral);
          return (
            <CircleMarker
              key={l.name}
              center={[l.lat, l.lng]}
              radius={radius}
              pathOptions={{
                color: colorFor(l.avgSentiment),
                fillColor: colorFor(l.avgSentiment),
                fillOpacity: 0.55,
                weight: 1.5,
              }}
            >
              <Tooltip direction="top" offset={[0, -4]}>
                <strong>{l.name}</strong>
              </Tooltip>
              <Popup>
                <div className="text-sm">
                  <div className="mb-1 font-semibold capitalize">{l.name}</div>
                  <div>
                    Docs: <strong>{l.docs}</strong>
                  </div>
                  <div>
                    Avg sentiment:{" "}
                    <strong>{l.avgSentiment == null ? "n/a" : l.avgSentiment.toFixed(2)}</strong>
                  </div>
                  <div className="mt-1 flex gap-3 text-xs">
                    <span className="text-red-600">Stress {mix.stress}</span>
                    <span className="text-violet-600">Closure {mix.closure}</span>
                    <span className="text-emerald-600">Opp {mix.opportunity}</span>
                    <span className="text-zinc-500">{Math.round((100 * (mix.stress + mix.closure)) / total)}% neg</span>
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
