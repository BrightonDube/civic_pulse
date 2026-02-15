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
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded mb-3">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-2 rounded mb-3">
          Report submitted successfully!
        </div>
      )}

      <div className="mb-3">
        <label className="block text-gray-700 mb-1">Photo *</label>
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileChange}
          className="block w-full"
        />
      </div>

      {preview && (
        <div className="mb-3">
          <img src={preview} alt="preview" className="max-w-xs rounded" />
        </div>
      )}

      {gps && (
        <p className="text-sm text-gray-500 mb-3">
          📍 Location: {gps.lat.toFixed(5)}, {gps.lng.toFixed(5)}
        </p>
      )}

      <div className="mb-3">
        <label className="block text-gray-700 mb-1">
          Category Override (optional)
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="block w-full border border-gray-300 rounded-md p-2"
        >
          <option value="">Let AI decide</option>
          <option value="Pothole">Pothole</option>
          <option value="Water Leak">Water Leak</option>
          <option value="Vandalism">Vandalism</option>
          <option value="Broken Light">Broken Light</option>
          <option value="Road Damage">Road Damage</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting || !fileRef.current}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? "Submitting..." : "Submit Report"}
      </button>
    </div>
  );
};
