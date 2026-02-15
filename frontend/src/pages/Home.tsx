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
    setReports((prev) => [...prev, report]);
  };

  return (
    <div className="container mx-auto p-4">
      <OfflineBanner />
      <h1 className="text-2xl font-bold mb-4">Report an Issue</h1>
      <PhotoCapture onReportCreated={handleReportCreated} />
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Nearby Reports</h2>
        <AdminMap filters={{ category: "", status: "", date: "" }} externalReports={reports} />
      </div>
    </div>
  );
};
