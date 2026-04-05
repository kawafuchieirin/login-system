import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { authApi } from "../services/api";
import type { User } from "../types";
import { AuthContext } from "./authContextValue";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );
  const [loading, setLoading] = useState(() => !!token);

  useEffect(() => {
    let cancelled = false;
    if (!token) {
      return;
    }
    authApi
      .me()
      .then((res) => {
        if (!cancelled) setUser(res.data);
      })
      .catch(() => {
        if (!cancelled) {
          localStorage.removeItem("token");
          setToken(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    localStorage.setItem("token", res.data.access_token);
    setToken(res.data.access_token);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    await authApi.register(email, password);
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    authApi.logout().catch(() => {});
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
