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

export function getImageUrl(photoUrl: string): string {
  if (!photoUrl) return "";
  if (photoUrl.startsWith("http")) return photoUrl;
  return `${API_BASE}${photoUrl}`;
}

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
    
    // Handle duplicate report (409 Conflict) with enhanced error message
    if (res.status === 409 && typeof body.detail === 'object') {
      const detail = body.detail;
      // Use the user-friendly message from the backend
      const message = detail.message || detail.user_friendly_message || "Duplicate report detected";
      throw new Error(message);
    }
    
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

// Analytics
export async function getKeyMetrics(params?: Record<string, string>): Promise<any> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<any>(`/api/analytics/metrics${query}`);
}

export async function getTrends(period: "daily" | "weekly" | "monthly", params?: Record<string, string>): Promise<any[]> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<any[]>(`/api/analytics/trends/${period}${query}`);
}

export async function getCategoryDistribution(params?: Record<string, string>): Promise<Record<string, number>> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<Record<string, number>>(`/api/analytics/category-distribution${query}`);
}

export async function getSeverityTrends(period: "daily" | "weekly" | "monthly", params?: Record<string, string>): Promise<any[]> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<any[]>(`/api/analytics/severity-trends/${period}${query}`);
}

export async function getHeatZones(params?: Record<string, string>): Promise<any[]> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<any[]>(`/api/analytics/heat-zones${query}`);
}

export async function exportCSV(params?: Record<string, string>): Promise<Blob> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  
  const res = await fetch(`${API_BASE}/api/analytics/export/csv${query}`, {
    method: "GET",
    headers,
  });
  
  if (!res.ok) {
    throw new Error("Failed to export CSV");
  }
  
  return res.blob();
}

export async function exportPDF(params?: Record<string, string>): Promise<Blob> {
  const query = params ? "?" + new URLSearchParams(params).toString() : "";
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  
  const res = await fetch(`${API_BASE}/api/analytics/export/pdf${query}`, {
    method: "GET",
    headers,
  });
  
  if (!res.ok) {
    throw new Error("Failed to export PDF");
  }
  
  return res.blob();
}

// Config
export async function getCategories(): Promise<string[]> {
  const res = await request<{ categories: string[] }>("/api/config/categories");
  return res.categories;
}

export async function getStatuses(): Promise<string[]> {
  const res = await request<{ statuses: string[] }>("/api/config/statuses");
  return res.statuses;
}


// Notification API
export async function getNotifications(): Promise<any[]> {
  return request<any[]>("/api/notifications/");
}

export async function getUnreadCount(): Promise<{ count: number }> {
  return request<{ count: number }>("/api/notifications/unread/count");
}

export async function markNotificationsRead(notificationIds: string[]): Promise<any> {
  return request<any>("/api/notifications/mark-read", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ notification_ids: notificationIds }),
  });
}

export async function markAllNotificationsRead(): Promise<any> {
  return request<any>("/api/notifications/mark-all-read", { method: "POST" });
}

export async function deleteNotification(notificationId: string): Promise<any> {
  return request<any>(`/api/notifications/${notificationId}`, { method: "DELETE" });
}


// User Management API (Admin)
export async function listUsers(params: Record<string, any> = {}): Promise<any> {
  const query = Object.keys(params).length ? "?" + new URLSearchParams(params).toString() : "";
  return request<any>(`/api/admin/users/${query}`);
}

export async function getUserStats(): Promise<any> {
  return request<any>("/api/admin/users/stats/summary");
}

export async function updateUserRole(userId: string, role: string): Promise<any> {
  return request<any>(`/api/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  });
}

export async function verifyUserEmail(userId: string): Promise<any> {
  return request<any>(`/api/admin/users/${userId}/verify`, { method: "PATCH" });
}

export async function deleteUser(userId: string): Promise<any> {
  return request<any>(`/api/admin/users/${userId}`, { method: "DELETE" });
}
