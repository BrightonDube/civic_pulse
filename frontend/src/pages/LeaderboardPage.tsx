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
    return <p className="text-center mt-8 text-gray-500">Loading leaderboard...</p>;
  if (error)
    return <p className="text-center mt-8 text-red-500">Error: {error}</p>;

  return (
    <div className="container mx-auto p-4 max-w-lg">
      <h1 className="text-2xl font-bold mb-4">🏆 Leaderboard</h1>
      <p className="text-gray-600 mb-4">Top reporters by number of submissions</p>

      {entries.length === 0 ? (
        <p className="text-gray-500">No data yet.</p>
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-gray-200">
              <th className="text-left py-2 px-3">Rank</th>
              <th className="text-left py-2 px-3">User</th>
              <th className="text-right py-2 px-3">Reports</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.user_id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 px-3 font-bold text-blue-600">
                  #{entry.rank}
                </td>
                <td className="py-2 px-3">{entry.email}</td>
                <td className="py-2 px-3 text-right font-medium">
                  {entry.report_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
