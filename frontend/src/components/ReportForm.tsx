import { useState } from "react";
import { createReport } from "../services/api";

export const ReportForm = () => {
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!category) {
      setMessage("Category is required");
      return;
    }

    setSubmitting(true);
    setMessage(null);

    // For text-only reports, we still need a photo per the API
    // This form is a simplified fallback
    const formData = new FormData();
    formData.append("user_override_category", category);
    if (description) formData.append("description", description);

    try {
      await createReport(formData);
      setCategory("");
      setDescription("");
      setMessage("Report submitted!");
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-md mx-auto bg-white rounded-2xl shadow-md border border-gray-100 p-6"
    >
      <h2 className="text-xl font-bold text-gray-900 mb-4">Submit a Report</h2>

      {message && (
        <div className={`flex items-center gap-2 px-4 py-3 rounded-xl mb-4 text-sm ${
          message.includes("failed") ? "bg-red-50 border border-red-200 text-red-700" : "bg-blue-50 border border-blue-200 text-blue-700"
        }`}>
          {message}
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Category *</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="block w-full px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
        >
          <option value="">Select category</option>
          <option value="Pothole">🕳️ Pothole</option>
          <option value="Water Leak">💧 Water Leak</option>
          <option value="Vandalism">🎨 Vandalism</option>
          <option value="Broken Light">💡 Broken Light</option>
          <option value="Other">📋 Other</option>
        </select>
      </div>

      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="block w-full px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none"
          rows={3}
        />
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2.5 px-4 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
      >
        {submitting ? "Submitting..." : "Submit"}
      </button>
    </form>
  );
};
