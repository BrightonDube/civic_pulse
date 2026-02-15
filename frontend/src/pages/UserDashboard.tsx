import { useEffect, useState } from "react";
import { getMyReports } from "../services/api";
import { Report } from "../types";
import { OfflineBanner } from "../components/offlineBanner";

export const UserDashboard = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyReports()
      .then(setReports)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading)
    return <p className="text-center mt-8 text-gray-500">Loading reports...</p>;
  if (error)
    return <p className="text-center mt-8 text-red-500">Error: {error}</p>;

  return (
    <div className="container mx-auto p-4">
      <OfflineBanner />
      <h1 className="text-2xl font-bold mb-4">My Reports</h1>

      {reports.length === 0 ? (
        <p className="text-gray-500">You haven't submitted any reports yet.</p>
      ) : (
        <div className="grid gap-4">
          {reports.map((r) => (
            <div
              key={r.id}
              className="border rounded-lg p-4 shadow-sm flex gap-4"
            >
              {r.photo_url && (
                <img
                  src={r.photo_url}
                  alt="report"
                  className="w-24 h-24 object-cover rounded"
                />
              )}
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="inline-block w-3 h-3 rounded-full"
                    style={{ backgroundColor: r.color }}
                  />
                  <span className="font-semibold">{r.category}</span>
                  <span className="text-sm text-gray-500">
                    Severity: {r.severity_score}
                  </span>
                </div>
                <p className="text-sm text-gray-600">
                  Status: <span className="font-medium">{r.status}</span>
                </p>
                <p className="text-sm text-gray-600">
                  Upvotes: {r.upvote_count}
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(r.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
