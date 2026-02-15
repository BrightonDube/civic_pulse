import { Routes, Route } from "react-router-dom";
import { Home } from "../pages/Home";
import { AdminDashboard } from "../pages/AdminDashboard";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { UserDashboard } from "../pages/UserDashboard";
import { LeaderboardPage } from "../pages/LeaderboardPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ProtectedRoute } from "../components/ProtectedRoute";

export const AppRoutes = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/" element={<ProtectedRoute><Home /></ProtectedRoute>} />
    <Route path="/my-reports" element={<ProtectedRoute><UserDashboard /></ProtectedRoute>} />
    <Route path="/leaderboard" element={<ProtectedRoute><LeaderboardPage /></ProtectedRoute>} />
    <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
    <Route path="/admin" element={<ProtectedRoute requireAdmin><AdminDashboard /></ProtectedRoute>} />
  </Routes>
);
