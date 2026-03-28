import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "./api";

interface User { id: number; username: string; role: string; discord_id: string | null; }
interface AuthCtx { user: User | null; loading: boolean; login: (u: string, p: string) => Promise<void>; logout: () => void; }

const AuthContext = createContext<AuthCtx>({ user: null, loading: true, login: async () => {}, logout: () => {} });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    const token = localStorage.getItem("kalux_token");
    if (!token) { setLoading(false); return; }
    try {
      const me = await api.get<User>("/auth/me");
      setUser(me);
    } catch {
      localStorage.removeItem("kalux_token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchMe(); }, [fetchMe]);

  const login = async (username: string, password: string) => {
    const data = await api.post<{ token: string; user: User }>("/auth/login", { username, password });
    localStorage.setItem("kalux_token", data.token);
    setUser(data.user);
  };

  const logout = () => {
    localStorage.removeItem("kalux_token");
    setUser(null);
  };

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
