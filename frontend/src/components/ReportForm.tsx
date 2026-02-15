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
      className="max-w-md mx-auto p-4 border rounded-md shadow-md"
    >
      <h2 className="text-xl font-bold mb-4">Submit a Report</h2>

      {message && (
        <div className="bg-blue-100 text-blue-700 px-4 py-2 rounded mb-3">
          {message}
        </div>
      )}

      <label className="block mb-2">
        Category*
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full border p-2 rounded"
        >
          <option value="">Select category</option>
          <option value="Pothole">Pothole</option>
          <option value="Water Leak">Water Leak</option>
          <option value="Vandalism">Vandalism</option>
          <option value="Broken Light">Broken Light</option>
          <option value="Other">Other</option>
        </select>
      </label>

      <label className="block mb-2">
        Description
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full border p-2 rounded"
        />
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Submitting..." : "Submit"}
      </button>
    </form>
  );
};
