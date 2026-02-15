import { useState, useEffect } from "react";
import { PhotoCapture } from "../components/PhotoCapture";
import { AdminMap } from "../components/AdminMap";
import { OfflineBanner } from "../components/offlineBanner";
import { listReports } from "../services/api";
import { Report } from "../types";

export const Home = () => {
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    listReports()
      .then(setReports)
      .catch(() => { /* offline or not logged in */ });
  }, []);

  const handleReportCreated = (report: Report) => {
    setReports((prev) => [report, ...prev]);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <OfflineBanner />

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Report an Issue</h1>
        <p className="mt-1 text-gray-500">Snap a photo of infrastructure problems in your area</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <PhotoCapture onReportCreated={handleReportCreated} />
        </div>
        <div className="lg:col-span-2">
          <div className="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <span>📍</span> Nearby Reports
                <span className="ml-auto text-sm font-normal text-gray-400">{reports.length} total</span>
              </h2>
            </div>
            <div className="h-[500px]">
              <AdminMap filters={{ category: "", status: "", date: "" }} externalReports={reports} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
