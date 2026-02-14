import { Report } from "../types";

const API_URL = "http://localhost:8000/reports"; // FastAPI later

export async function uploadReport(
  report: Report,
  retries = 3
): Promise<boolean> {
  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    });

    if (!res.ok) throw new Error("Upload failed");

    return true;
  } catch (err) {
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 2000));
      return uploadReport(report, retries - 1);
    }

    return false;
  }
}
