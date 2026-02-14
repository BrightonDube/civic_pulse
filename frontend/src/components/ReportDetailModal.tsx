import { Report } from "../types";

interface Props {
  report: Report;
  onClose: () => void;
}

export const ReportDetailModal = ({ report, onClose }: Props) => {
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>

        <h2>{report.title}</h2>

        <img
          src={report.imageUrl}
          alt="report"
          style={{ width: "100%", borderRadius: "8px" }}
        />

        <p>
          <b>Category:</b> {report.category}
        </p>
        <p>
          <b>Severity:</b> {report.severity}
        </p>
        <p>
          <b>Status:</b> {report.status}
        </p>
        <p>
          <b>Location:</b> {report.latitude}, {report.longitude}
        </p>
      </div>
    </div>
  );
};
