import { useState } from "react";
import { useReports } from "../context/ReportContext";
import { Report } from "../types";

export const ReportForm = () => {
  const { addReport } = useReports();
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Simple validation
    if (!title || !category) {
      alert("Please fill in required fields!");
      return;
    }

    const newReport: Report = {
      id: crypto.randomUUID(), // unique ID
      title,
      category,
      description,
      severity: 1,
      latitude: 0,   // will be updated with GPS later
      longitude: 0,  // will be updated with GPS later
      status: "Reported",
      timestamp: new Date().toISOString(),
      imageUrl: "", // placeholder for uploaded image
    };

    addReport(newReport);

    // Reset form
    setTitle("");
    setCategory("");
    setDescription("");
    alert("Report submitted!");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-md mx-auto p-4 border rounded-md shadow-md"
    >
      <h2 className="text-xl font-bold mb-4">Submit a Report</h2>

      <label className="block mb-2">
        Title*
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full border p-2 rounded"
        />
      </label>

      <label className="block mb-2">
        Category*
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full border p-2 rounded"
        />
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
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Submit
      </button>
    </form>
  );
};
