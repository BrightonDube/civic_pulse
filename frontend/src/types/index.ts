export interface Report {
  id: string;
  user_id: string;
  photo_url: string;
  latitude: number;
  longitude: number;
  category: string;
  severity_score: number;
  color: string;
  status: string;
  upvote_count: number;
  ai_generated: boolean;
  archived: boolean;
  created_at: string;
  updated_at: string;
  // Legacy fields for backward compat
  title?: string;
  description?: string;
  imageUrl?: string;
  severity?: number;
  timestamp?: string;
}

export interface User {
  id: string;
  email: string;
  phone: string;
  role: "user" | "admin";
  email_verified: boolean;
  report_count: number;
  leaderboard_opt_out: boolean;
}

export interface TokenResponse {
  access_token: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  email: string;
  report_count: number;
}

export interface AdminNote {
  id: string;
  report_id: string;
  admin_id: string;
  note: string;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  report_id: string;
  admin_id: string;
  action: string;
  details: string | null;
  created_at: string;
}

export interface KeyMetrics {
  total_reports: number;
  resolution_rate: number;
  average_resolution_time: number;
}

export interface TrendPoint {
  period: string;
  count: number;
}

export interface SeverityTrend {
  period: string;
  average_severity: number;
  count: number;
}

export interface HeatZone {
  latitude: number;
  longitude: number;
  report_count: number;
  report_ids: string[];
}

export interface AnalyticsFilters {
  category?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  min_lat?: number;
  max_lat?: number;
  min_lon?: number;
  max_lon?: number;
}
