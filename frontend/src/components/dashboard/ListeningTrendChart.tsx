import { useState, useMemo } from "react";
import type { DailyTrendResponse } from "@/api/analytics";

interface Props {
  data?: DailyTrendResponse;
  isLoading: boolean;
}

type Metric = "plays" | "minutes";

const W = 800;
const H = 200;
const PADDING_X = 8;
const PADDING_Y = 16;

interface Coord {
  x: number;
  y: number;
  value: number;
  date: string;
}

interface ChartGeometry {
  pathD: string;
  areaD: string;
  peak: Coord | null;
  axisLabels: string[];
}

const formatLabel = (dateStr: string) =>
  new Date(dateStr)
    .toLocaleDateString("en-US", { month: "short", day: "numeric" })
    .toUpperCase();

const LoadingState = () => (
  <div className="flex-1 animate-pulse bg-white/[0.02] rounded-2xl" />
);

const EmptyState = () => (
  <div className="flex-1 flex items-center justify-center">
    <p className="text-on-surface-variant text-sm">
      No listening activity in this period yet.
    </p>
  </div>
);

const ChartSvg = ({
  pathD,
  areaD,
  peak,
  axisLabels,
}: ChartGeometry) => (
  <div className="flex-1 w-full relative pb-5">
    <svg
      className="w-full h-full"
      viewBox={`0 0 ${W} ${H}`}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#53e076" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#53e076" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaD} fill="url(#trendGradient)" />
      <path
        d={pathD}
        fill="none"
        stroke="#53e076"
        strokeWidth="3"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
      {peak && (
        <>
          <circle cx={peak.x} cy={peak.y} r="8" fill="#53e076" opacity="0.25">
            <animate
              attributeName="r"
              values="6;12;6"
              dur="2s"
              repeatCount="indefinite"
            />
          </circle>
          <circle cx={peak.x} cy={peak.y} r="4" fill="#53e076" />
        </>
      )}
    </svg>
    <div className="absolute bottom-0 left-0 w-full flex justify-between px-1">
      {axisLabels.map((label) => (
        <span
          key={label}
          className="text-[9px] text-outline font-bold tracking-widest"
        >
          {label}
        </span>
      ))}
    </div>
  </div>
);

export const ListeningTrendChart = ({ data, isLoading }: Props) => {
  const [metric, setMetric] = useState<Metric>("plays");

  const geometry = useMemo<ChartGeometry>(() => {
    if (!data || data.points.length === 0) {
      return { pathD: "", areaD: "", peak: null, axisLabels: [] };
    }

    const values = data.points.map((p) => p[metric]);
    const maxVal = Math.max(...values, 1);
    const n = data.points.length;

    const coords: Coord[] = data.points.map((p, i) => {
      const x = PADDING_X + (i * (W - PADDING_X * 2)) / Math.max(n - 1, 1);
      const ratio = p[metric] / maxVal;
      const y = H - PADDING_Y - ratio * (H - PADDING_Y * 2);
      return { x, y, value: p[metric], date: p.date };
    });

    let d = `M ${coords[0].x},${coords[0].y}`;
    for (let i = 1; i < coords.length; i++) {
      const prev = coords[i - 1];
      const curr = coords[i];
      const midX = (prev.x + curr.x) / 2;
      d += ` Q ${midX},${prev.y} ${midX},${(prev.y + curr.y) / 2}`;
      d += ` T ${curr.x},${curr.y}`;
    }

    const lastCoord = coords.at(-1)!;
    const area = `${d} L ${lastCoord.x},${H} L ${coords[0].x},${H} Z`;

    const peakCoord = coords.reduce(
      (acc, c) => (c.value > acc.value ? c : acc),
      coords[0],
    );

    // 4 evenly-spaced labels — fits cleanly even at 320px wide.
    const labels: string[] = [];
    const step = Math.max(1, Math.floor((n - 1) / 3));
    for (let i = 0; i < n; i += step) {
      labels.push(formatLabel(data.points[i].date));
    }
    if (labels.length < 4 && n > 0) {
      labels.push(formatLabel(data.points[n - 1].date));
    }

    return {
      pathD: d,
      areaD: area,
      peak: peakCoord,
      axisLabels: labels.slice(0, 4),
    };
  }, [data, metric]);

  // Pick the render branch explicitly rather than nesting ternaries inline.
  const renderBody = () => {
    if (isLoading || !data) return <LoadingState />;
    if (data.points.every((p) => p[metric] === 0)) return <EmptyState />;
    return <ChartSvg {...geometry} />;
  };

  return (
    <div className="lg:col-span-2 glass-card p-6 sm:p-8 rounded-3xl h-[360px] sm:h-[400px] flex flex-col">
      <div className="flex justify-between items-center mb-6 sm:mb-8 gap-4 flex-wrap">
        <div>
          <h3 className="text-xl font-bold text-white">Listening Trends</h3>
          <p className="text-[11px] text-on-surface-variant mt-0.5">
            {data ? `Last ${data.days} days` : ""}
          </p>
        </div>
        <div className="flex gap-1 bg-white/5 rounded-full p-1">
          <button
            type="button"
            onClick={() => setMetric("plays")}
            className={`px-3 py-1 rounded-full text-[11px] font-bold transition-colors ${
              metric === "plays"
                ? "bg-primary text-on-primary"
                : "text-on-surface-variant hover:text-white"
            }`}
          >
            Plays
          </button>
          <button
            type="button"
            onClick={() => setMetric("minutes")}
            className={`px-3 py-1 rounded-full text-[11px] font-bold transition-colors ${
              metric === "minutes"
                ? "bg-primary text-on-primary"
                : "text-on-surface-variant hover:text-white"
            }`}
          >
            Minutes
          </button>
        </div>
      </div>
      {renderBody()}
    </div>
  );
};
