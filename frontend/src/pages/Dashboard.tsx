import { Calendar } from "lucide-react";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useOverview } from "@/hooks/useOverview";
import { useDailyTrend } from "@/hooks/useDailyTrend";
import { useGenreDistribution } from "@/hooks/useGenreDistribution";
import { useTodaySummary } from "@/hooks/useTodaySummary";
import { useHourlyVelocity } from "@/hooks/useHourlyVelocity";
import { StatRow } from "@/components/dashboard/StatRow";
import { ListeningTrendChart } from "@/components/dashboard/ListeningTrendChart";
import { GenreDonut } from "@/components/dashboard/GenreDonut";
import { TodaySummaryCard } from "@/components/dashboard/TodaySummaryCard";
import { TopTracksTable } from "@/components/dashboard/TopTracksTable";

const WINDOW_DAYS = 30;

const formatWindow = (days: number): string => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - (days - 1));
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  return `${start.toLocaleDateString("en-US", opts)} — ${end.toLocaleDateString(
    "en-US",
    opts,
  )}`;
};

const Dashboard = () => {
  const { data: user } = useCurrentUser();
  const { overviewData, isOverviewFetching } = useOverview(WINDOW_DAYS);
  const { dailyTrendData, isDailyTrendFetching } = useDailyTrend(WINDOW_DAYS);
  const { genreDistributionData, isGenreDistributionFetching } =
    useGenreDistribution(5);
  const { todaySummaryData, isTodaySummaryFetching } = useTodaySummary();
  const { hourlyVelocityData, isHourlyVelocityFetching } = useHourlyVelocity();

  const firstName = user?.display_name?.split(" ")[0] || "there";

  return (
    <div className="w-full space-y-6 sm:space-y-8">
      {/* Hero */}
      <section className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight">
            Hello, {firstName}
          </h1>
          <p className="text-on-surface-variant font-medium mt-1 text-sm sm:text-base">
            Your listening performance for the last {WINDOW_DAYS} days.
          </p>
        </div>
        <div className="glass-card flex items-center gap-3 px-4 py-2 rounded-xl self-start sm:self-auto">
          <Calendar size={14} className="text-primary" />
          <span className="text-xs font-bold text-white whitespace-nowrap">
            {formatWindow(WINDOW_DAYS)}
          </span>
        </div>
      </section>

      {/* Stat Row */}
      <StatRow data={overviewData} isLoading={isOverviewFetching} />

      {/* Trend + Genre */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
        <ListeningTrendChart
          data={dailyTrendData}
          isLoading={isDailyTrendFetching}
        />
        <GenreDonut
          data={genreDistributionData}
          isLoading={isGenreDistributionFetching}
        />
      </section>

      {/* Today's Activity + Top Tracks */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
        <TodaySummaryCard
          todayData={todaySummaryData}
          hourlyData={hourlyVelocityData}
          isLoading={isTodaySummaryFetching || isHourlyVelocityFetching}
        />
        <div className="lg:col-span-2">
          <TopTracksTable />
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
