export interface User {
  id: number;
  email: string;
  name: string;
  is_active: boolean;
  created_at: string;
}

const TOKEN_KEY = "kobi-auth-token";
const USER_KEY = "kobi-auth-user";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getToken(): string | null {
  if (!isBrowser()) return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* quota / private mode — silent */
  }
}

export function clearToken(): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* silent */
  }
}

export function getStoredUser(): User | null {
  if (!isBrowser()) return null;
  try {
    const raw = window.localStorage.getItem(USER_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (
      parsed &&
      typeof parsed === "object" &&
      typeof parsed.id === "number" &&
      typeof parsed.email === "string"
    ) {
      return parsed as User;
    }
    return null;
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    /* silent */
  }
}

export function clearStoredUser(): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.removeItem(USER_KEY);
  } catch {
    /* silent */
  }
}

export function clearAuth(): void {
  clearToken();
  clearStoredUser();
}
