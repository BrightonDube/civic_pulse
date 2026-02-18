import { useEffect, useState } from "react";
import { getMyReports, getImageUrl } from "../services/api";
import { Report } from "../types";
import { OfflineBanner } from "../components/offlineBanner";

const statusColors: Record<string, string> = {
  Reported: "bg-orange-100 text-orange-800",
  "In Progress": "bg-blue-100 text-blue-800",
  Fixed: "bg-green-100 text-green-800",
};

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

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <OfflineBanner />
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">My Reports</h1>
        <p className="mt-1 text-gray-500">{reports.length} report{reports.length !== 1 ? "s" : ""} submitted</p>
      </div>

      {reports.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100 shadow-sm">
          <span className="text-5xl">📋</span>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No reports yet</h3>
          <p className="mt-1 text-gray-500">Start by snapping a photo of an infrastructure issue.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((r) => (
            <div
              key={r.id}
              className="bg-white border border-gray-100 rounded-2xl shadow-sm hover:shadow-md transition-shadow p-5 flex gap-5"
            >
              {r.photo_url && (
                <img
                  src={getImageUrl(r.photo_url)}
                  alt="report"
                  className="w-28 h-28 object-cover rounded-xl shrink-0"
                />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <span
                    className="inline-block w-3 h-3 rounded-full ring-2 ring-white shadow-sm"
                    style={{ backgroundColor: r.color }}
                  />
                  <span className="font-semibold text-gray-900">{r.category}</span>
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${statusColors[r.status] || "bg-gray-100 text-gray-800"}`}>
                    {r.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Severity: <span className="font-medium text-gray-700">{r.severity_score}/10</span></span>
                  <span>👍 {r.upvote_count}</span>
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(r.created_at).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
