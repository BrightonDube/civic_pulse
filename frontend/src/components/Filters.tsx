import React from "react";

interface FiltersProps {
  filters: {
    category: string;
    status: string;
    date: string;
  };
  setFilters: (filters: any) => void;
}

export const Filters: React.FC<FiltersProps> = ({ filters, setFilters }) => {
  return (
    <div className="flex flex-wrap gap-3 mb-6">
      <select
        value={filters.category}
        onChange={(e) =>
          setFilters({ ...filters, category: e.target.value })
        }
        className="px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
      >
        <option value="">All Categories</option>
        <option value="Pothole">🕳️ Pothole</option>
        <option value="Water Leak">💧 Water Leak</option>
        <option value="Vandalism">🎨 Vandalism</option>
        <option value="Broken Light">💡 Broken Light</option>
        <option value="Road Damage">🛣️ Road Damage</option>
        <option value="Other">📋 Other</option>
      </select>

      <select
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        className="px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
      >
        <option value="">All Statuses</option>
        <option value="Reported">Reported</option>
        <option value="In Progress">In Progress</option>
        <option value="Fixed">Fixed</option>
      </select>

      <input
        type="date"
        value={filters.date}
        onChange={(e) => setFilters({ ...filters, date: e.target.value })}
        className="px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
      />
    </div>
  );
};
