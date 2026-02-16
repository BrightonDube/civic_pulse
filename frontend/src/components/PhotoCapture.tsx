import { useState, useRef } from "react";
import { createReport } from "../services/api";
import { Report } from "../types";
import { parseExifCoords } from "../utils/exif";

interface Props {
  onReportCreated?: (report: Report) => void;
}

export const PhotoCapture = ({ onReportCreated }: Props) => {
  const [preview, setPreview] = useState<string | null>(null);
  const [gps, setGps] = useState<{ lat: number; lng: number } | null>(null);
  const [category, setCategory] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const fileRef = useRef<File | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    fileRef.current = file;
    setPreview(URL.createObjectURL(file));
    setSuccess(false);
    setError(null);

    // Try EXIF GPS extraction
    const coords = await parseExifCoords(file);
    if (coords) {
      setGps(coords);
    } else if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setGps({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        () => setError("Unable to get location. Please enable GPS.")
      );
    } else {
      setError("Unable to get location.");
    }
  };

  const handleSubmit = async () => {
    if (!fileRef.current) {
      setError("Please upload a photo.");
      return;
    }
    setSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.append("photo", fileRef.current);
    if (gps) {
      formData.append("latitude", gps.lat.toString());
      formData.append("longitude", gps.lng.toString());
    }
    if (category) {
      formData.append("user_override_category", category);
    }

    try {
      const report = await createReport(formData);
      setSuccess(true);
      setPreview(null);
      setGps(null);
      setCategory("");
      fileRef.current = null;
      onReportCreated?.(report);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-md border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <span>📸</span> Capture Photo
      </h3>

      {error && (
        <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-4 text-sm">
          <svg className="w-5 h-5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}
      {success && (
        <div className="flex items-center gap-2 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-xl mb-4 text-sm">
          <svg className="w-5 h-5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
          Report submitted successfully!
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Upload photo</label>
        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-xl cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-colors">
          <div className="flex flex-col items-center justify-center pt-5 pb-6">
            <svg className="w-8 h-8 mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <p className="text-sm text-gray-500">
              <span className="text-blue-600 font-medium">Click to upload</span> or take a photo
            </p>
          </div>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileChange}
            className="hidden"
          />
        </label>
      </div>

      {preview && (
        <div className="mb-4">
          <img src={preview} alt="preview" className="w-full h-48 object-cover rounded-xl" />
        </div>
      )}

      {gps && (
        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 rounded-lg px-3 py-2 mb-4">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z" clipRule="evenodd" />
          </svg>
          {gps.lat.toFixed(5)}, {gps.lng.toFixed(5)}
        </div>
      )}

      <div className="mb-5">
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Category (optional)</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="block w-full px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow bg-white"
        >
          <option value="">🤖 Let AI decide</option>
          <option value="Pothole">🕳️ Pothole</option>
          <option value="Water Leak">💧 Water Leak</option>
          <option value="Vandalism">🎨 Vandalism</option>
          <option value="Broken Light">💡 Broken Light</option>
          <option value="Road Damage">🛣️ Road Damage</option>
          <option value="Other">📋 Other</option>
        </select>
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting || !fileRef.current}
        className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2.5 px-4 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
      >
        {submitting ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Submitting…
          </span>
        ) : "Submit Report"}
      </button>
    </div>
  );
};
