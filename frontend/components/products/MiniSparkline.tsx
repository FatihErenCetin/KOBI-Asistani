"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";

interface SparklinePoint {
  day: string;
  units: number;
}

export function MiniSparkline({ productId }: { productId: number }) {
  const [series, setSeries] = useState<SparklinePoint[]>([]);

  useEffect(() => {
    let alive = true;
    api
      .productSparkline(productId, 7)
      .then((s) => alive && setSeries(s))
      .catch(() => alive && setSeries([]));
    return () => {
      alive = false;
    };
  }, [productId]);

  if (series.length === 0) {
    return <span className="text-xs text-slate-300">—</span>;
  }

  const max = Math.max(1, ...series.map((p) => p.units));
  const w = 72;
  const h = 22;
  const stepX = w / Math.max(1, series.length - 1);
  const points = series
    .map(
      (p, i) =>
        `${(i * stepX).toFixed(1)},${(h - (p.units / max) * h).toFixed(1)}`,
    )
    .join(" ");

  return (
    <svg
      width={w}
      height={h}
      className="text-brand-500"
      aria-label="7g satis sparkline"
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
