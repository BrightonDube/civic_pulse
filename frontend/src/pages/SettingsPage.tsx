import { useAuth } from "../context/AuthContext";

export const SettingsPage = () => {
  const { user } = useAuth();

  return (
    <div className="container mx-auto p-4 max-w-md">
      <h1 className="text-2xl font-bold mb-4">Settings</h1>

      <div className="bg-white border rounded-lg p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Profile</h2>
        <p className="text-gray-600 mb-2">
          <span className="font-medium">Email:</span> {user?.email}
        </p>
        <p className="text-gray-600 mb-2">
          <span className="font-medium">Role:</span> {user?.role}
        </p>
        <p className="text-gray-600 mb-4">
          <span className="font-medium">Reports submitted:</span>{" "}
          {user?.report_count}
        </p>

        <h2 className="text-lg font-semibold mb-2">Privacy</h2>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={user?.leaderboard_opt_out ?? false}
            readOnly
            className="h-4 w-4"
          />
          <span className="text-gray-700">
            Opt out of leaderboard (contact admin to change)
          </span>
        </label>
      </div>
    </div>
  );
};
