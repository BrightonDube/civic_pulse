import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import ReportIssue from "../pages/ReportIssue";
import AdminDashboard from "../pages/AdminDashboard";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/report" element={<ReportIssue />} />
      <Route path="/admin" element={<AdminDashboard />} />
    </Routes>
  );
}
