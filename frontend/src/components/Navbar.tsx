import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useState } from "react";

export const Navbar = () => {
  const { isAuthenticated, isAdmin, user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white shadow-lg sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 text-xl font-bold tracking-tight">
            <span className="text-2xl">🏙️</span>
            <span>CivicPulse</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {isAuthenticated ? (
              <>
                <NavLink to="/">Home</NavLink>
                <NavLink to="/my-reports">My Reports</NavLink>
                <NavLink to="/leaderboard">Leaderboard</NavLink>
                <NavLink to="/settings">Settings</NavLink>
                {isAdmin && <NavLink to="/admin">Admin</NavLink>}
                {isAdmin && <NavLink to="/analytics">Analytics</NavLink>}
                <div className="ml-3 pl-3 border-l border-white/20 flex items-center gap-3">
                  <span className="text-blue-200 text-sm truncate max-w-[160px]">{user?.email}</span>
                  <button
                    onClick={handleLogout}
                    className="bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <NavLink to="/login">Login</NavLink>
                <Link
                  to="/register"
                  className="ml-2 bg-white text-indigo-700 hover:bg-blue-50 px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors"
                >
                  Register
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-indigo-900/50 backdrop-blur-sm">
          <div className="px-4 py-3 space-y-1">
            {isAuthenticated ? (
              <>
                <MobileNavLink to="/" onClick={() => setMobileOpen(false)}>Home</MobileNavLink>
                <MobileNavLink to="/my-reports" onClick={() => setMobileOpen(false)}>My Reports</MobileNavLink>
                <MobileNavLink to="/leaderboard" onClick={() => setMobileOpen(false)}>Leaderboard</MobileNavLink>
                <MobileNavLink to="/settings" onClick={() => setMobileOpen(false)}>Settings</MobileNavLink>
                {isAdmin && <MobileNavLink to="/admin" onClick={() => setMobileOpen(false)}>Admin</MobileNavLink>}
                {isAdmin && <MobileNavLink to="/analytics" onClick={() => setMobileOpen(false)}>Analytics</MobileNavLink>}
                <div className="pt-2 mt-2 border-t border-white/10">
                  <p className="text-blue-200 text-sm px-3 py-1">{user?.email}</p>
                  <button
                    onClick={() => { handleLogout(); setMobileOpen(false); }}
                    className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/10 text-red-300 text-sm"
                  >
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <MobileNavLink to="/login" onClick={() => setMobileOpen(false)}>Login</MobileNavLink>
                <MobileNavLink to="/register" onClick={() => setMobileOpen(false)}>Register</MobileNavLink>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

const NavLink = ({ to, children }: { to: string; children: React.ReactNode }) => (
  <Link to={to} className="px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-white/10 transition-colors">
    {children}
  </Link>
);

const MobileNavLink = ({ to, children, onClick }: { to: string; children: React.ReactNode; onClick: () => void }) => (
  <Link to={to} onClick={onClick} className="block px-3 py-2 rounded-lg text-sm hover:bg-white/10 transition-colors">
    {children}
  </Link>
);
