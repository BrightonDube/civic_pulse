import { useState, useEffect } from "react";
import { AdminMap } from "../components/AdminMap";
import { Filters } from "../components/Filters";
import { OfflineBanner } from "../components/offlineBanner";
import { listReports } from "../services/api";
import { Report } from "../types";

export const AdminDashboard = () => {
  const [filters, setFilters] = useState({
    category: "",
    status: "",
    date: "",
  });
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    const params: Record<string, string> = {};
    if (filters.category) params.category = filters.category;
    if (filters.status) params.report_status = filters.status;
    listReports(params)
      .then(setReports)
      .catch(() => {});
  }, [filters.category, filters.status]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <OfflineBanner />
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span>🛡️</span> Admin Dashboard
        </h1>
        <p className="mt-1 text-gray-500">{reports.length} reports found</p>
      </div>
      <Filters filters={filters} setFilters={setFilters} />
      <div className="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
        <div className="h-[600px]">
          <AdminMap filters={filters} externalReports={reports} />
        </div>
      </div>
    </div>
  );
};
