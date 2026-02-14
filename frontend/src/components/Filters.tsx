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
    <div className="filters flex gap-4 mb-4">
      <select
        value={filters.category}
        onChange={(e) =>
          setFilters({ ...filters, category: e.target.value })
        }
      >
        <option value="">All Categories</option>
        <option value="Pothole">Pothole</option>
        <option value="Water Leak">Water Leak</option>
        <option value="Vandalism">Vandalism</option>
      </select>

      <select
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
      >
        <option value="">All Status</option>
        <option value="Reported">Reported</option>
        <option value="In Progress">In Progress</option>
        <option value="Fixed">Fixed</option>
      </select>

      <input
        type="date"
        value={filters.date}
        onChange={(e) => setFilters({ ...filters, date: e.target.value })}
      />
    </div>
  );
};
