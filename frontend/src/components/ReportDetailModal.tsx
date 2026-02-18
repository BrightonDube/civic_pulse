import { useState } from "react";
import { Report } from "../types";
import { useAuth } from "../context/AuthContext";
import { getImageUrl } from "../services/api";
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
    if (newStatus === current.status) return;
    try {
      const updated = await adminUpdateStatus(current.id, newStatus);
      setCurrent(updated);
      onUpdate?.(updated);
      setMessage("Status updated successfully");
      setTimeout(() => setMessage(null), 3000);
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto relative" onClick={(e) => e.stopPropagation()}>
        <button
          className="absolute top-4 right-4 z-10 w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 transition-colors"
          onClick={onClose}
        >
          ✕
        </button>

        {current.photo_url && (
          <img
            src={getImageUrl(current.photo_url)}
            alt="report"
            className="w-full h-56 object-cover rounded-t-2xl"
          />
        )}

        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <span
              className="inline-block w-4 h-4 rounded-full ring-2 ring-white shadow"
              style={{ backgroundColor: current.color }}
            />
            <h2 className="text-xl font-bold text-gray-900">{current.category}</h2>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
              current.status === "Fixed" ? "bg-green-100 text-green-800" :
              current.status === "In Progress" ? "bg-blue-100 text-blue-800" :
              "bg-orange-100 text-orange-800"
            }`}>
              {current.status}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm mb-4">
            <div className="bg-gray-50 rounded-xl px-4 py-3">
              <span className="text-gray-500 block text-xs">Severity</span>
              <span className="font-bold text-lg" style={{ color: current.color }}>{current.severity_score}/10</span>
            </div>
            <div className="bg-gray-50 rounded-xl px-4 py-3">
              <span className="text-gray-500 block text-xs">Upvotes</span>
              <span className="font-bold text-lg text-gray-900">👍 {current.upvote_count}</span>
            </div>
          </div>

          <div className="text-sm text-gray-500 space-y-1 mb-4">
            <p className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" /></svg>
              {current.latitude.toFixed(5)}, {current.longitude.toFixed(5)}
            </p>
            <p className="text-xs text-gray-400">
              Created {new Date(current.created_at).toLocaleString()}
            </p>
          </div>

          {message && (
            <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-2.5 rounded-xl text-sm mb-4">
              {message}
            </div>
          )}

          <button
            onClick={handleUpvote}
            className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-2.5 rounded-xl font-semibold hover:from-green-600 hover:to-emerald-700 transition-all shadow-md hover:shadow-lg"
          >
            👍 Upvote
          </button>

          {isAdmin && (
            <div className="mt-6 pt-6 border-t border-gray-100">
              <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-4">Admin Actions</h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Status</label>
                  <div className="flex gap-2">
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                    >
                      <option value="Reported">Reported</option>
                      <option value="In Progress">In Progress</option>
                      <option value="Fixed">Fixed</option>
                    </select>
                    <button onClick={handleStatusUpdate} className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors">
                      Update
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Category Override</label>
                  <div className="flex gap-2">
                    <input
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button onClick={handleCategoryOverride} className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors">
                      Override
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Severity (1-10)</label>
                  <div className="flex gap-2">
                    <input
                      type="number"
                      min={1}
                      max={10}
                      value={newSeverity}
                      onChange={(e) => setNewSeverity(Number(e.target.value))}
                      className="w-20 px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <button onClick={handleSeverityAdjust} className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors">
                      Adjust
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1.5">Internal Note</label>
                  <div className="flex gap-2">
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      rows={2}
                    />
                    <button onClick={handleAddNote} className="self-end px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors">
                      Add
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
