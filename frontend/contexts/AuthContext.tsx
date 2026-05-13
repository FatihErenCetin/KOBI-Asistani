"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  clearAuth,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
  type User,
} from "@/lib/auth";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const storedToken = getToken();
    const storedUser = getStoredUser();
    if (storedToken && storedUser) {
      setTokenState(storedToken);
      setUser(storedUser);
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({ email, password }),
    });

    if (!resp.ok) {
      let message = "Email veya şifre hatalı";
      try {
        const body = await resp.json();
        if (body?.detail && typeof body.detail === "string") {
          message = body.detail;
        }
      } catch {
        /* keep default */
      }
      throw new Error(message);
    }

    const data: LoginResponse = await resp.json();
    setToken(data.access_token);
    setStoredUser(data.user);
    setTokenState(data.access_token);
    setUser(data.user);
  }, []);

  const register = useCallback(
    async (email: string, password: string, name: string) => {
      const resp = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        body: JSON.stringify({ email, password, name }),
      });

      if (!resp.ok) {
        let message = "Kayıt sırasında bir hata oluştu";
        try {
          const body = await resp.json();
          if (resp.status === 409) {
            message = "Bu email zaten kayıtlı";
          } else if (body?.detail) {
            if (typeof body.detail === "string") {
              message = body.detail;
            } else if (Array.isArray(body.detail) && body.detail[0]?.msg) {
              message = body.detail[0].msg;
            }
          }
        } catch {
          /* keep default */
        }
        throw new Error(message);
      }

      const data: LoginResponse = await resp.json();
      setToken(data.access_token);
      setStoredUser(data.user);
      setTokenState(data.access_token);
      setUser(data.user);
    },
    []
  );

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    setTokenState(null);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, isLoading, login, register, logout }),
    [user, token, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an <AuthProvider>");
  }
  return ctx;
}
