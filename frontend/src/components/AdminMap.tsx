import { useState } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

import { useReports } from "../context/ReportContext";
import { ReportDetailModal } from "./ReportDetailmodal";
import { MarkerCluster } from "./MarkerCluster";

const getColorIcon = (severity: number) => {
  const color = severity > 7 ? "red" : severity > 3 ? "orange" : "green";

  return new L.Icon({
    iconUrl: `https://chart.googleapis.com/chart?chst=d_map_pin_icon&chld=report|${color}`,
    iconSize: [30, 42],
    iconAnchor: [15, 42],
  });
};

export const AdminMap = ({ filters }: { filters: any }) => {
  const { reports } = useReports();

  const [selectedReport, setSelectedReport] = useState<any>(null);

  const filteredReports = reports.filter((r) => {
    const matchesCategory =
      !filters.category || r.category === filters.category;

    const matchesStatus =
      !filters.status || r.status === filters.status;

    const matchesDate =
      !filters.date ||
      new Date(r.timestamp).toDateString() === filters.date;

    return matchesCategory && matchesStatus && matchesDate;
  });

  const markers = filteredReports.map((report) => ({
    id: report.id,
    lat: report.latitude,
    lng: report.longitude,
    icon: getColorIcon(report.severity),
    onClick: () => setSelectedReport(report),
  }));

  return (
    <>
      <MapContainer
        center={[0, 0]}
        zoom={2}
        style={{ height: "600px", width: "100%" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MarkerCluster markers={markers} />
      </MapContainer>

      {selectedReport && (
        <ReportDetailModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </>
  );
};
