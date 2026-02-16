import { useAuth } from "../context/AuthContext";

export const SettingsPage = () => {
  const { user } = useAuth();

  return (
    <div className="max-w-xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-gray-500">Manage your account preferences</p>
      </div>

      <div className="bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span>👤</span> Profile
          </h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-500">Email</span>
            <span className="font-medium text-gray-900">{user?.email}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-50">
            <span className="text-sm text-gray-500">Role</span>
            <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
              user?.role === "admin" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"
            }`}>
              {user?.role}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-t border-gray-50">
            <span className="text-sm text-gray-500">Reports submitted</span>
            <span className="text-2xl font-bold text-indigo-600">{user?.report_count ?? 0}</span>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-white rounded-2xl shadow-md border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <span>🔒</span> Privacy
          </h2>
        </div>
        <div className="p-6">
          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={user?.leaderboard_opt_out ?? false}
              readOnly
              className="h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <div>
              <span className="text-sm font-medium text-gray-900">Opt out of leaderboard</span>
              <p className="text-xs text-gray-500 mt-0.5">Contact admin to change this setting</p>
            </div>
          </label>
        </div>
      </div>
    </div>
  );
};
