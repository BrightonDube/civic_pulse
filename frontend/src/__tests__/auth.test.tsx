/**
 * Tests for AuthContext.
 * Validates: Requirements 8.1, 8.3, 8.6
 */
import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock localStorage
const store: Record<string, string> = {};
Object.defineProperty(global, "localStorage", {
  value: {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, val: string) => { store[key] = val; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
  },
  writable: true,
});

import { AuthProvider, useAuth } from "../context/AuthContext";

const TestComponent = () => {
  const { user, isAuthenticated, isAdmin, loading, error, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="admin">{String(isAdmin)}</span>
      <span data-testid="error">{error || "none"}</span>
      <span data-testid="email">{user?.email || "none"}</span>
      <button data-testid="login" onClick={() => login("a@b.com", "pass")}>Login</button>
      <button data-testid="logout" onClick={logout}>Logout</button>
    </div>
  );
};

beforeEach(() => {
  mockFetch.mockClear();
  localStorage.clear();
});

describe("AuthContext", () => {
  test("starts unauthenticated when no token", async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for loading to finish
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    expect(screen.getByTestId("authenticated").textContent).toBe("false");
    expect(screen.getByTestId("email").textContent).toBe("none");
  });

  test("login stores token and sets user", async () => {
    // Mock login endpoint
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: "jwt-123" }),
    });
    // Mock getMe endpoint
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: "1",
        email: "a@b.com",
        phone: "+1",
        role: "user",
        email_verified: false,
        report_count: 0,
        leaderboard_opt_out: false,
      }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    await act(async () => {
      screen.getByTestId("login").click();
    });

    // Wait for async operations
    await act(async () => { await new Promise((r) => setTimeout(r, 50)); });

    expect(localStorage.getItem("access_token")).toBe("jwt-123");
    expect(screen.getByTestId("authenticated").textContent).toBe("true");
    expect(screen.getByTestId("email").textContent).toBe("a@b.com");
  });

  test("logout clears token and user", async () => {
    localStorage.setItem("access_token", "old-token");

    // Mock getMe for initial load
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: "1",
        email: "a@b.com",
        phone: "+1",
        role: "admin",
        email_verified: true,
        report_count: 5,
        leaderboard_opt_out: false,
      }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await act(async () => { await new Promise((r) => setTimeout(r, 50)); });

    expect(screen.getByTestId("authenticated").textContent).toBe("true");
    expect(screen.getByTestId("admin").textContent).toBe("true");

    act(() => {
      screen.getByTestId("logout").click();
    });

    expect(screen.getByTestId("authenticated").textContent).toBe("false");
    expect(localStorage.getItem("access_token")).toBeNull();
  });

  test("admin role is detected correctly", async () => {
    localStorage.setItem("access_token", "admin-token");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: "1",
        email: "admin@test.com",
        phone: "+1",
        role: "admin",
        email_verified: true,
        report_count: 10,
        leaderboard_opt_out: false,
      }),
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await act(async () => { await new Promise((r) => setTimeout(r, 50)); });

    expect(screen.getByTestId("admin").textContent).toBe("true");
  });
});
