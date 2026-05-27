import { useMemo } from "react";
import type { GenreDistributionResponse } from "@/api/analytics";

interface Props {
  data?: GenreDistributionResponse;
  isLoading: boolean;
}

// Accent colors for slices, ordered by priority. Other = neutral.
const SLICE_COLORS = ["#53e076", "#ff767b", "#c8c6c6", "#72fe8f", "#1db954"];
const OTHER_COLOR = "#3d4a3d";

const CIRCUMFERENCE = 2 * Math.PI * 40; // r=40 in viewBox

export const GenreDonut = ({ data, isLoading }: Props) => {
  const segments = useMemo(() => {
    if (!data || data.slices.length === 0) return [];

    let offset = 0;
    return data.slices.map((slice, i) => {
      const length = (slice.weight / 100) * CIRCUMFERENCE;
      const seg = {
        name: slice.name,
        weight: slice.weight,
        color: slice.name === "Other" ? OTHER_COLOR : SLICE_COLORS[i % SLICE_COLORS.length],
        dashArray: `${length} ${CIRCUMFERENCE}`,
        dashOffset: -offset,
      };
      offset += length;
      return seg;
    });
  }, [data]);

  return (
    <div className="glass-card p-8 rounded-3xl h-[400px] flex flex-col">
      <div>
        <h3 className="text-xl font-bold text-white">Genre Distribution</h3>
        <p className="text-[11px] text-on-surface-variant mt-0.5">
          {data ? `From your top ${data.based_on_artists} artists` : ""}
        </p>
      </div>

      {isLoading || !data ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-40 h-40 rounded-full bg-white/[0.02] animate-pulse" />
        </div>
      ) : data.slices.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-on-surface-variant text-sm text-center">
            Not enough listening data yet to compute genres.
          </p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col justify-around">
          <div className="relative w-44 h-44 mx-auto">
            <svg
              className="w-full h-full -rotate-90"
              viewBox="0 0 100 100"
            >
              {/* Background ring */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="transparent"
                stroke="#ffffff"
                strokeOpacity="0.05"
                strokeWidth="12"
              />
              {segments.map((seg) => (
                <circle
                  key={seg.name}
                  cx="50"
                  cy="50"
                  r="40"
                  fill="transparent"
                  stroke={seg.color}
                  strokeWidth="12"
                  strokeDasharray={seg.dashArray}
                  strokeDashoffset={seg.dashOffset}
                />
              ))}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {data.total_genres}
              </span>
              <span className="text-[10px] text-outline uppercase font-bold tracking-widest">
                Genres
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 mt-6">
            {segments.map((seg) => (
              <div key={seg.name} className="flex items-center gap-2 min-w-0">
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: seg.color }}
                />
                <span className="text-xs text-on-surface truncate">
                  {seg.name}{" "}
                  <span className="text-outline">({seg.weight}%)</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
