import { useEffect } from "react";
import { useReports } from "../context/ReportContext";
import { listReports } from "../services/api";

export const useReportsPolling = (interval = 5000) => {
  const { addReport } = useReports();

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const reports = await listReports();
        reports.forEach((report) => addReport(report));
      } catch {
        // Silently fail when offline or unauthenticated
      }
    };

    fetchReports();
    const timer = setInterval(fetchReports, interval);
    return () => clearInterval(timer);
  }, []);
};
