import { useState } from "react";
import EXIF from "exif-js"; // npm install exif-js
import { useReports } from "../context/ReportContext";
import { Report } from "../types";

export const PhotoCapture = () => {
  const { addReport } = useReports();

  const [preview, setPreview] = useState<string | null>(null);
  const [gps, setGps] = useState<{ lat: number; lng: number } | null>(null);
  const [title, setTitle] = useState<string>("");
  const [category, setCategory] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Show preview
    const url = URL.createObjectURL(file);
    setPreview(url);

    // EXIF GPS extraction
    EXIF.getData(file as any, () => {
      const lat = EXIF.getTag(file as any, "GPSLatitude") as number[] | undefined;
      const lon = EXIF.getTag(file as any, "GPSLongitude") as number[] | undefined;
      const latRef = EXIF.getTag(file as any, "GPSLatitudeRef") || "N";
      const lonRef = EXIF.getTag(file as any, "GPSLongitudeRef") || "E";

      if (lat && lon) {
        const latitude =
          (lat[0] + lat[1] / 60 + lat[2] / 3600) * (latRef === "N" ? 1 : -1);
        const longitude =
          (lon[0] + lon[1] / 60 + lon[2] / 3600) * (lonRef === "E" ? 1 : -1);
        setGps({ lat: latitude, lng: longitude });
      } else {
        // Browser geolocation fallback
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition((pos) => {
            setGps({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          });
        } else {
          setError("Unable to get location.");
        }
      }
    });
  };

  const handleSubmit = () => {
    if (!preview || !gps || !title || !category) {
      setError("Please fill all fields and upload a photo.");
      return;
    }

    const newReport: Report = {
      id: Date.now().toString(),
      title,
      category,
      severity: 1, // default until AI sets it
      latitude: gps.lat,
      longitude: gps.lng,
      status: "Reported",
      timestamp: new Date().toISOString(),
      imageUrl: preview!, // required by Report type
    };

    addReport(newReport);

    // Reset form
    setPreview(null);
    setGps(null);
    setTitle("");
    setCategory("");
    setError(null);
  };

  return (
    <div className="photo-capture">
      {error && <div className="error">{error}</div>}

      <input
        type="text"
        placeholder="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <input
        type="text"
        placeholder="Category"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
      />

      <input type="file" accept="image/*" onChange={handleFileChange} />

      {preview && (
        <div className="preview">
          <img
            src={preview}
            alt="preview"
            style={{ maxWidth: "300px", marginTop: "10px" }}
          />
        </div>
      )}

      <button onClick={handleSubmit} style={{ marginTop: "10px" }}>
        Submit Report
      </button>
    </div>
  );
};
