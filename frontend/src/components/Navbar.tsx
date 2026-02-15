import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export const Navbar = () => {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-blue-600 text-white shadow-md">
      <div className="container mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-xl font-bold">
          Civic Pulse
        </Link>

        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <>
              <Link to="/" className="hover:text-blue-200">
                Home
              </Link>
              <Link to="/my-reports" className="hover:text-blue-200">
                My Reports
              </Link>
              <Link to="/leaderboard" className="hover:text-blue-200">
                Leaderboard
              </Link>
              {isAdmin && (
                <Link to="/admin" className="hover:text-blue-200">
                  Admin
                </Link>
              )}
              <span className="text-blue-200 text-sm">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="bg-blue-700 px-3 py-1 rounded hover:bg-blue-800"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="hover:text-blue-200">
                Login
              </Link>
              <Link to="/register" className="hover:text-blue-200">
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};
