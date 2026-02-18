import { useState, useEffect } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

import { listReports } from "../services/api";
import { Report } from "../types";
import { ReportDetailModal } from "./ReportDetailModal";
import { MarkerCluster } from "./MarkerCluster";

const getColorIcon = (severity: number) => {
  const color = severity > 7 ? "red" : severity > 3 ? "orange" : "green";
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });
};

interface Props {
  filters: { category: string; status: string; date: string };
  externalReports?: Report[];
}

export const AdminMap = ({ filters, externalReports }: Props) => {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);

  useEffect(() => {
    if (externalReports) {
      setReports(externalReports);
      return;
    }
    const params: Record<string, string> = {};
    if (filters.category) params.category = filters.category;
    if (filters.status) params.report_status = filters.status;
    listReports(params)
      .then(setReports)
      .catch(() => {});
  }, [filters, externalReports]);

  const filteredReports = reports.filter((r) => {
    if (r.archived) return false;
    const matchesCategory = !filters.category || r.category === filters.category;
    const matchesStatus = !filters.status || r.status === filters.status;
    const matchesDate =
      !filters.date ||
      new Date(r.created_at).toDateString() ===
        new Date(filters.date).toDateString();
    return matchesCategory && matchesStatus && matchesDate;
  });

  const markers = filteredReports.map((report) => ({
    id: report.id,
    lat: report.latitude,
    lng: report.longitude,
    icon: getColorIcon(report.severity_score),
    onClick: () => setSelectedReport(report),
  }));

  return (
    <>
      <div className="relative z-0">
        <MapContainer
          center={[0, 0]}
          zoom={2}
          style={{ height: "500px", width: "100%" }}
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <MarkerCluster markers={markers} />
        </MapContainer>
      </div>

      {selectedReport && (
        <ReportDetailModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          onUpdate={(updatedReport) => {
            setReports((prev) =>
              prev.map((r) => (r.id === updatedReport.id ? updatedReport : r))
            );
            setSelectedReport(updatedReport);
          }}
        />
      )}
    </>
  );
};
