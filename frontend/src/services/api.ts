import { Report, User, TokenResponse, LeaderboardEntry, AdminNote, AuditLogEntry } from "../types";

const getApiBase = (): string => {
  try {
    // Vite injects import.meta.env at build time
    return (globalThis as any).__VITE_API_URL__ || "http://localhost:8000";
  } catch {
    return "http://localhost:8000";
  }
};
const API_BASE = getApiBase();

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { ...authHeaders(), ...options.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

// Auth
export async function register(email: string, password: string, phone: string): Promise<User> {
  return request<User>("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, phone }),
  });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe(): Promise<User> {
  return request<User>("/api/auth/me");
}

// Reports
export async function createReport(formData: FormData): Promise<Report> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/api/reports/`, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }
  return res.json();
}

export async function listReports(params?: Record<string, string>): Promise<Report[]> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<Report[]>(`/api/reports/${query}`);
}

export async function getMyReports(): Promise<Report[]> {
  return request<Report[]>("/api/reports/my");
}

export async function getReport(id: string): Promise<Report> {
  return request<Report>(`/api/reports/${id}`);
}

export async function upvoteReport(id: string): Promise<Report> {
  return request<Report>(`/api/reports/${id}/upvote`, { method: "POST" });
}

// Admin
export async function adminUpdateStatus(reportId: string, status: string): Promise<Report> {
  return request<Report>(`/api/admin/reports/${reportId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
}

export async function adminOverrideCategory(reportId: string, category: string): Promise<Report> {
  return request<Report>(`/api/admin/reports/${reportId}/category`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category }),
  });
}

export async function adminAdjustSeverity(reportId: string, severity: number): Promise<Report> {
  return request<Report>(`/api/admin/reports/${reportId}/severity`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ severity }),
  });
}

export async function adminAddNote(reportId: string, note: string): Promise<AdminNote> {
  return request<AdminNote>(`/api/admin/reports/${reportId}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ note }),
  });
}

export async function adminArchiveReport(reportId: string): Promise<Report> {
  return request<Report>(`/api/admin/reports/${reportId}/archive`, { method: "POST" });
}

export async function adminGetAuditLog(reportId: string): Promise<AuditLogEntry[]> {
  return request<AuditLogEntry[]>(`/api/admin/reports/${reportId}/audit`);
}

export async function adminGetNotes(reportId: string): Promise<AdminNote[]> {
  return request<AdminNote[]>(`/api/admin/reports/${reportId}/notes`);
}

// Leaderboard
export async function getLeaderboard(limit = 10): Promise<LeaderboardEntry[]> {
  return request<LeaderboardEntry[]>(`/api/leaderboard/?limit=${limit}`);
}

// Upload report with retry (for offline sync)
export async function uploadReport(
  report: Report,
  retries = 3
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/reports/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(report),
    });
    if (!res.ok) throw new Error("Upload failed");
    return true;
  } catch {
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 2000));
      return uploadReport(report, retries - 1);
    }
    return false;
  }
}
