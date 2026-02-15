import { useState } from "react";
import { Report } from "../types";
import { useAuth } from "../context/AuthContext";
import {
  upvoteReport,
  adminUpdateStatus,
  adminOverrideCategory,
  adminAdjustSeverity,
  adminAddNote,
} from "../services/api";

interface Props {
  report: Report;
  onClose: () => void;
  onUpdate?: (report: Report) => void;
}

export const ReportDetailModal = ({ report, onClose, onUpdate }: Props) => {
  const { isAdmin } = useAuth();
  const [current, setCurrent] = useState(report);
  const [newStatus, setNewStatus] = useState(current.status);
  const [newCategory, setNewCategory] = useState(current.category);
  const [newSeverity, setNewSeverity] = useState(current.severity_score);
  const [note, setNote] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const handleUpvote = async () => {
    try {
      const updated = await upvoteReport(current.id);
      setCurrent(updated);
      onUpdate?.(updated);
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Upvote failed");
    }
  };

  const handleStatusUpdate = async () => {
    try {
      const updated = await adminUpdateStatus(current.id, newStatus);
      setCurrent(updated);
      onUpdate?.(updated);
      setMessage("Status updated");
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Update failed");
    }
  };

  const handleCategoryOverride = async () => {
    try {
      const updated = await adminOverrideCategory(current.id, newCategory);
      setCurrent(updated);
      onUpdate?.(updated);
      setMessage("Category updated");
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Update failed");
    }
  };

  const handleSeverityAdjust = async () => {
    try {
      const updated = await adminAdjustSeverity(current.id, newSeverity);
      setCurrent(updated);
      onUpdate?.(updated);
      setMessage("Severity adjusted");
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Update failed");
    }
  };

  const handleAddNote = async () => {
    if (!note.trim()) return;
    try {
      await adminAddNote(current.id, note);
      setNote("");
      setMessage("Note added");
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Failed");
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>✕</button>

        {current.photo_url && (
          <img
            src={current.photo_url}
            alt="report"
            style={{ width: "100%", borderRadius: "8px", marginBottom: "1rem" }}
          />
        )}

        <p><b>Category:</b> {current.category}</p>
        <p>
          <b>Severity:</b>{" "}
          <span style={{ color: current.color }}>{current.severity_score}</span>
        </p>
        <p><b>Status:</b> {current.status}</p>
        <p><b>Location:</b> {current.latitude.toFixed(5)}, {current.longitude.toFixed(5)}</p>
        <p><b>Upvotes:</b> {current.upvote_count}</p>
        <p className="text-xs text-gray-400 mt-1">
          Created: {new Date(current.created_at).toLocaleString()}
        </p>

        {message && (
          <div className="bg-blue-100 text-blue-700 px-3 py-2 rounded mt-2 text-sm">
            {message}
          </div>
        )}

        <div className="mt-3">
          <button
            onClick={handleUpvote}
            className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 mr-2"
          >
            👍 Upvote
          </button>
        </div>

        {isAdmin && (
          <div className="mt-4 border-t pt-4">
            <h3 className="font-semibold mb-2">Admin Actions</h3>

            <div className="mb-3">
              <label className="text-sm text-gray-600">Status</label>
              <div className="flex gap-2">
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="border rounded p-1 flex-1"
                >
                  <option value="Reported">Reported</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Fixed">Fixed</option>
                </select>
                <button onClick={handleStatusUpdate} className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                  Update
                </button>
              </div>
            </div>

            <div className="mb-3">
              <label className="text-sm text-gray-600">Category Override</label>
              <div className="flex gap-2">
                <input
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="border rounded p-1 flex-1"
                />
                <button onClick={handleCategoryOverride} className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                  Override
                </button>
              </div>
            </div>

            <div className="mb-3">
              <label className="text-sm text-gray-600">Severity (1-10)</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={newSeverity}
                  onChange={(e) => setNewSeverity(Number(e.target.value))}
                  className="border rounded p-1 w-20"
                />
                <button onClick={handleSeverityAdjust} className="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                  Adjust
                </button>
              </div>
            </div>

            <div className="mb-2">
              <label className="text-sm text-gray-600">Internal Note</label>
              <div className="flex gap-2">
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="border rounded p-1 flex-1"
                  rows={2}
                />
                <button onClick={handleAddNote} className="bg-blue-600 text-white px-2 py-1 rounded text-sm self-end">
                  Add
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
