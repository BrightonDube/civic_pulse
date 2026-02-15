/**
 * Tests for API client service.
 * Validates: Requirements 11.2 (API client with auth headers)
 */

// Mock fetch globally
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

// Must import after mocking
import { login, register, getMe, listReports, getLeaderboard } from "../services/api";

beforeEach(() => {
  mockFetch.mockClear();
  localStorage.clear();
});

describe("API Client", () => {
  test("login sends correct payload and returns token", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ access_token: "jwt-123" }),
    });

    const result = await login("test@example.com", "password123");
    expect(result.access_token).toBe("jwt-123");

    const [url, opts] = mockFetch.mock.calls[0];
    expect(url).toContain("/api/auth/login");
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body)).toEqual({
      email: "test@example.com",
      password: "password123",
    });
  });

  test("register sends correct payload", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "1", email: "t@e.com", phone: "+1", role: "user" }),
    });

    const result = await register("t@e.com", "pass1234", "+1");
    expect(result.email).toBe("t@e.com");
  });

  test("authenticated requests include Bearer token", async () => {
    localStorage.setItem("access_token", "my-token");

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "1", email: "a@b.com", role: "user" }),
    });

    await getMe();

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers["Authorization"]).toBe("Bearer my-token");
  });

  test("unauthenticated requests have no Bearer token", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    await getLeaderboard();

    const [, opts] = mockFetch.mock.calls[0];
    expect(opts.headers["Authorization"]).toBeUndefined();
  });

  test("API errors throw with detail message", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Invalid credentials" }),
    });

    await expect(login("bad@e.com", "wrong")).rejects.toThrow(
      "Invalid credentials"
    );
  });

  test("listReports passes query params", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    await listReports({ category: "Pothole", report_status: "Reported" });

    const [url] = mockFetch.mock.calls[0];
    expect(url).toContain("category=Pothole");
    expect(url).toContain("report_status=Reported");
  });
});
