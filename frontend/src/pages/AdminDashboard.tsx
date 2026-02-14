import { useState } from "react";
import { AdminMap } from "../components/AdminMap";
import { Filters } from "../components/Filters";
import { OfflineBanner } from "../components/offlineBanner";

export const AdminDashboard = () => {
  const [filters, setFilters] = useState({
    category: "",
    status: "",
    date: "",
  });

  return (
    <div className="container mx-auto p-4">
      {/* Show offline banner at the top */}
      <OfflineBanner />

      <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>

      {/* Filters controls */}
      <Filters filters={filters} setFilters={setFilters} />

      {/* Map displaying reports */}
      <AdminMap filters={filters} />
    </div>
  );
};
