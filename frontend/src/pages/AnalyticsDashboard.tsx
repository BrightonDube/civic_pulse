import { useState, useEffect } from "react";
import {
  getKeyMetrics,
  getTrends,
  getCategoryDistribution,
  getSeverityTrends,
  getHeatZones,
  exportCSV,
  exportPDF,
} from "../services/api";
import { KeyMetrics, TrendPoint, SeverityTrend, HeatZone } from "../types";

export const AnalyticsDashboard = () => {
  const [metrics, setMetrics] = useState<KeyMetrics | null>(null);
  const [trendPeriod, setTrendPeriod] = useState<"daily" | "weekly" | "monthly">("daily");
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [categoryDist, setCategoryDist] = useState<Record<string, number>>({});
  const [severityTrends, setSeverityTrends] = useState<SeverityTrend[]>([]);
  const [heatZones, setHeatZones] = useState<HeatZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    category: "",
    status: "",
    date_from: "",
    date_to: "",
  });

  useEffect(() => {
    loadAnalytics();
  }, [trendPeriod, filters]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filters.category) params.category = filters.category;
      if (filters.status) params.status = filters.status;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;

      const [metricsData, trendsData, categoryData, severityData, heatData] = await Promise.all([
        getKeyMetrics(params),
        getTrends(trendPeriod, params),
        getCategoryDistribution(params),
        getSeverityTrends(trendPeriod, params),
        getHeatZones(params),
      ]);

      setMetrics(metricsData);
      setTrends(trendsData);
      setCategoryDist(categoryData);
      setSeverityTrends(severityData);
      setHeatZones(heatData);
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const params: Record<string, string> = {};
      if (filters.category) params.category = filters.category;
      if (filters.status) params.status = filters.status;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;

      const blob = await exportCSV(params);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `civicpulse_reports_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export CSV:", error);
      alert("Failed to export CSV");
    }
  };

  const handleExportPDF = async () => {
    try {
      const params: Record<string, string> = {};
      if (filters.category) params.category = filters.category;
      if (filters.status) params.status = filters.status;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;

      const blob = await exportPDF(params);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `civicpulse_analytics_${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export PDF:", error);
      alert("Failed to export PDF");
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading analytics...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span>📊</span> Analytics Dashboard
        </h1>
        <p className="mt-1 text-gray-500">Data-driven insights for resource allocation</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={filters.category}
              onChange={(e) => setFilters({ ...filters, category: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="Pothole">Pothole</option>
              <option value="Water Leak">Water Leak</option>
              <option value="Vandalism">Vandalism</option>
              <option value="Broken Streetlight">Broken Streetlight</option>
              <option value="Illegal Dumping">Illegal Dumping</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="Reported">Reported</option>
              <option value="In Progress">In Progress</option>
              <option value="Fixed">Fixed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">From Date</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">To Date</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        <div className="mt-4 flex gap-2">
          <button
            onClick={handleExportCSV}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
          >
            📥 Export CSV
          </button>
          <button
            onClick={handleExportPDF}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            📄 Export PDF
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Reports</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{metrics.total_reports}</p>
              </div>
              <div className="text-4xl">📝</div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Resolution Rate</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.resolution_rate.toFixed(1)}%
                </p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Resolution Time</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {metrics.average_resolution_time.toFixed(1)}h
                </p>
              </div>
              <div className="text-4xl">⏱️</div>
            </div>
          </div>
        </div>
      )}

      {/* Trend Period Selector */}
      <div className="mb-4">
        <div className="flex gap-2">
          <button
            onClick={() => setTrendPeriod("daily")}
            className={`px-4 py-2 rounded-md transition-colors ${
              trendPeriod === "daily"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Daily
          </button>
          <button
            onClick={() => setTrendPeriod("weekly")}
            className={`px-4 py-2 rounded-md transition-colors ${
              trendPeriod === "weekly"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Weekly
          </button>
          <button
            onClick={() => setTrendPeriod("monthly")}
            className={`px-4 py-2 rounded-md transition-colors ${
              trendPeriod === "monthly"
                ? "bg-blue-600 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            Monthly
          </button>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Report Trends Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Report Trends</h2>
          <div className="space-y-2">
            {trends.length > 0 ? (
              <div className="h-64 flex items-end gap-2">
                {trends.map((point, idx) => {
                  const maxCount = Math.max(...trends.map((t) => t.count), 1);
                  const height = (point.count / maxCount) * 100;
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <div
                        className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                        style={{ height: `${height}%` }}
                        title={`${point.period}: ${point.count} reports`}
                      />
                      <div className="text-xs text-gray-600 mt-2 truncate w-full text-center">
                        {point.period.split("T")[0]}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No trend data available
              </div>
            )}
          </div>
        </div>

        {/* Category Distribution Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Category Distribution</h2>
          <div className="space-y-3">
            {Object.entries(categoryDist).length > 0 ? (
              Object.entries(categoryDist)
                .sort(([, a], [, b]) => b - a)
                .map(([category, count]) => {
                  const total = Object.values(categoryDist).reduce((sum, c) => sum + c, 0);
                  const percentage = total > 0 ? (count / total) * 100 : 0;
                  return (
                    <div key={category}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700">{category}</span>
                        <span className="text-gray-600">
                          {count} ({percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No category data available
              </div>
            )}
          </div>
        </div>

        {/* Severity Trends Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Severity Trends</h2>
          <div className="space-y-2">
            {severityTrends.length > 0 ? (
              <div className="h-64 flex items-end gap-2">
                {severityTrends.map((point, idx) => {
                  const height = (point.average_severity / 10) * 100;
                  const color =
                    point.average_severity >= 8
                      ? "bg-red-500"
                      : point.average_severity >= 4
                      ? "bg-yellow-500"
                      : "bg-green-500";
                  return (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <div
                        className={`w-full ${color} rounded-t transition-all`}
                        style={{ height: `${height}%` }}
                        title={`${point.period}: ${point.average_severity.toFixed(1)} avg severity`}
                      />
                      <div className="text-xs text-gray-600 mt-2 truncate w-full text-center">
                        {point.period.split("T")[0]}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No severity data available
              </div>
            )}
          </div>
        </div>

        {/* Heat Zones Table */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Top Heat Zones</h2>
          <div className="overflow-auto max-h-64">
            {heatZones.length > 0 ? (
              <table className="min-w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Location
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      Reports
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {heatZones.slice(0, 10).map((zone, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-sm text-gray-900">
                        {zone.latitude.toFixed(4)}, {zone.longitude.toFixed(4)}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-900">{zone.report_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No heat zones identified
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
