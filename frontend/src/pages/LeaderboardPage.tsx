import { useEffect, useState } from "react";
import { getLeaderboard } from "../services/api";
import { LeaderboardEntry } from "../types";

export const LeaderboardPage = () => {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLeaderboard(10)
      .then(setEntries)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return (
      <div className="flex items-center justify-center h-64">
        <svg className="animate-spin w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  if (error)
    return (
      <div className="max-w-2xl mx-auto mt-8 p-4">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">Error: {error}</div>
      </div>
    );

  const rankMedal = (rank: number) => {
    if (rank === 1) return "🥇";
    if (rank === 2) return "🥈";
    if (rank === 3) return "🥉";
    return `#${rank}`;
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="text-center mb-8">
        <span className="text-5xl">🏆</span>
        <h1 className="mt-3 text-3xl font-bold text-gray-900">Leaderboard</h1>
        <p className="mt-1 text-gray-500">Top reporters by number of submissions</p>
      </div>

      {entries.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100 shadow-sm">
          <span className="text-5xl">📊</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No data yet</h3>
          <p className="mt-1 text-gray-500">Be the first to submit a report!</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
          <div className="divide-y divide-gray-100">
            {entries.map((entry) => (
              <div key={entry.user_id} className="flex items-center px-6 py-4 hover:bg-gray-50/50 transition-colors">
                <div className="w-12 text-center text-2xl">
                  {rankMedal(entry.rank)}
                </div>
                <div className="flex-1 ml-4">
                  <p className="font-medium text-gray-900">{entry.email}</p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-indigo-600">{entry.report_count}</span>
                  <p className="text-xs text-gray-400">reports</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
