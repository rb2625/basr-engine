"use client";

import dynamic from "next/dynamic";
import { useApi } from "@/components/useApi";
import type { MapData } from "@/lib/types";

const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[520px] items-center justify-center rounded-xl border border-zinc-200 bg-white text-sm text-zinc-400">
      Loading map...
    </div>
  ),
});

export default function MapPage() {
  const { data, error, loading } = useApi<MapData>("map");
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold">Entity sentiment map</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Average sentiment and signal mix per UAE location, sized by mention volume.
          Color: green = positive, amber = mixed, red = negative.
        </p>
      </div>
      {loading ? (
        <div className="flex h-[520px] items-center justify-center rounded-xl border border-zinc-200 bg-white text-sm text-zinc-400">
          Loading intelligence...
        </div>
      ) : error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          {error}
        </div>
      ) : (
        <MapView locations={data?.locations || []} />
      )}
      <p className="text-xs text-zinc-400">
        Locations come from the BASR gazetteer; coordinates are curated, not from a
        third-party API. Tiles by OpenStreetMap.
      </p>
    </div>
  );
}
