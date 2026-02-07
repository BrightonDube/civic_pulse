import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

type AppShellProps = {
  children: ReactNode;
};

export default function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Civic Pulse</h1>
        <nav>
          <NavLink to="/">Home</NavLink>
          <NavLink to="/report">Report</NavLink>
          <NavLink to="/admin">Admin</NavLink>
        </nav>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
