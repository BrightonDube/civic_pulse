import React, { useEffect, useState } from "react";
import { getCategories, getStatuses } from "../services/api";

interface FiltersProps {
  filters: {
    category: string;
    status: string;
    date: string;
  };
  setFilters: (filters: any) => void;
}

export const Filters: React.FC<FiltersProps> = ({ filters, setFilters }) => {
  const [categories, setCategories] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);

  useEffect(() => {
    getCategories().then(setCategories).catch(console.error);
    getStatuses().then(setStatuses).catch(console.error);
  }, []);

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
        {categories.map((cat) => (
          <option key={cat} value={cat}>{cat}</option>
        ))}
      </select>

      <select
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        className="px-4 py-2.5 border border-gray-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-sm"
      >
        <option value="">All Statuses</option>
        {statuses.map((status) => (
          <option key={status} value={status}>{status}</option>
        ))}
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
