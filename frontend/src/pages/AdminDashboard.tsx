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
    <div className="container mx-auto p-4">
      <OfflineBanner />
      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
      <Filters filters={filters} setFilters={setFilters} />
      <AdminMap filters={filters} externalReports={reports} />
    </div>
  );
};
