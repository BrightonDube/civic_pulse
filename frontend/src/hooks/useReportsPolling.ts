import { useEffect } from "react";
import { useReports } from "../context/ReportContext";
import axios from "axios";

export const useReportsPolling = (interval = 5000) => {
  const { addReport } = useReports();

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await axios.get("/api/reports"); // Backend endpoint
        res.data.forEach((report: any) => addReport(report));
      } catch (err) {
        console.error("Failed to fetch reports", err);
      }
    };

    fetchReports();
    const timer = setInterval(fetchReports, interval);
    return () => clearInterval(timer);
  }, []);
};
