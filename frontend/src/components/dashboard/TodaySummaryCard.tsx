import { TrendingUp } from "lucide-react";
import type {
  TodaySummaryResponse,
  HourlyVelocityResponse,
} from "@/api/analytics";

interface Props {
  todayData?: TodaySummaryResponse;
  hourlyData?: HourlyVelocityResponse;
  isLoading: boolean;
}

// Find the peak hour window (densest 2-hour stretch) for the "Peak Activity" line.
const findPeakWindow = (
  hours: HourlyVelocityResponse["hours"],
): { startHour: number; ratio: number } | null => {
  if (!hours || hours.length === 0) return null;

  let bestStart = 0;
  let bestSum = 0;
  for (let i = 0; i < hours.length; i++) {
    const next = hours[(i + 1) % hours.length];
    const sum = hours[i].count + next.count;
    if (sum > bestSum) {
      bestSum = sum;
      bestStart = i;
    }
  }
  if (bestSum === 0) return null;

  const totalPlays = hours.reduce((acc, h) => acc + h.count, 0);
  const ratio = totalPlays > 0 ? bestSum / totalPlays : 0;
  return { startHour: bestStart, ratio };
};

const formatHourRange = (startHour: number): string => {
  const fmt = (h: number) => {
    const period = h >= 12 ? "PM" : "AM";
    const display = h % 12 === 0 ? 12 : h % 12;
    return `${display}:00 ${period}`;
  };
  return `${fmt(startHour)} — ${fmt((startHour + 2) % 24)}`;
};

export const TodaySummaryCard = ({
  todayData,
  hourlyData,
  isLoading,
}: Props) => {
  const peak = findPeakWindow(hourlyData?.hours ?? []);
  const maxHourCount = Math.max(...(hourlyData?.hours.map((h) => h.count) ?? [1]), 1);

  return (
    <div className="glass-card rounded-3xl p-6 flex flex-col gap-6">
      <h3 className="font-bold text-white text-lg flex items-center gap-2">
        <TrendingUp className="text-primary" size={18} /> Today's Activity
      </h3>

      {isLoading ? (
        <div className="space-y-4">
          <div className="h-16 bg-white/[0.02] animate-pulse rounded-xl" />
          <div className="h-12 bg-white/[0.02] animate-pulse rounded-xl" />
          <div className="h-20 bg-white/[0.02] animate-pulse rounded-xl" />
        </div>
      ) : (
        <>
          {/* Total Tracks */}
          <div>
            <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant mb-1">
              Tracks Today
            </p>
            <p className="text-4xl font-bold text-primary leading-none">
              {todayData?.total_tracks ?? 0}
            </p>
          </div>

          {/* Listening Time */}
          <div>
            <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant mb-1">
              Listening Time
            </p>
            <p className="text-2xl font-bold text-white leading-none">
              {todayData?.listening_time ?? "0h 0m"}
            </p>
          </div>

          {/* Peak Activity */}
          {peak && (
            <div>
              <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant mb-1">
                Peak Activity
              </p>
              <p className="text-sm font-semibold text-white">
                {formatHourRange(peak.startHour)}
              </p>
              <div className="mt-2 h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full shadow-[0_0_8px_rgba(83,224,118,0.5)] transition-all"
                  style={{ width: `${Math.round(peak.ratio * 100)}%` }}
                />
              </div>
            </div>
          )}

          {/* Hourly Velocity (24-hour bars) */}
          {hourlyData && hourlyData.hours.length > 0 && (
            <div className="pt-4 border-t border-white/5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant">
                  Hourly Velocity
                </p>
                <span className="text-[9px] text-outline">Last 24h</span>
              </div>
              <div className="flex items-end justify-between h-16 gap-[2px]">
                {hourlyData.hours.map((h) => {
                  const heightPct = (h.count / maxHourCount) * 100;
                  const opacityClass =
                    h.count === 0
                      ? "bg-white/[0.04]"
                      : h.count === maxHourCount
                        ? "bg-primary shadow-[0_0_8px_rgba(83,224,118,0.4)]"
                        : "bg-primary/60";
                  return (
                    <div
                      key={h.hour}
                      className={`flex-1 rounded-t transition-all ${opacityClass}`}
                      style={{
                        height: `${Math.max(heightPct, h.count > 0 ? 8 : 4)}%`,
                      }}
                      title={`${h.hour}:00 — ${h.count} plays`}
                    />
                  );
                })}
              </div>
              <div className="flex justify-between mt-1 text-[8px] text-outline font-bold">
                <span>00</span>
                <span>06</span>
                <span>12</span>
                <span>18</span>
                <span>23</span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
