import { Routes, Route } from "react-router-dom";
import { ReportForm } from "../components/ReportForm";
import { AdminDashboard } from "../pages/AdminDashboard";

export const AppRoutes = () => (
  <Routes>
    <Route path="/" element={<ReportForm />} />
    <Route path="/admin" element={<AdminDashboard />} />
  </Routes>
);
