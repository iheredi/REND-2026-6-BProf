import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getToken, logout as clearAuth } from "../api/auth";
import http from "../api/_http_client";

interface User {
  id: string;
  email: string;
  name?: string; // opcionális
}

interface AuthContextType {
  user: User | null;
  setUser: (user: User | null) => void;
  loading: boolean;
  logout: () => void;
  isLoggedIn: boolean;
}

const AuthContext = createContext<AuthContextType|undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadUser = async () => {
        const token = getToken();

        if (!token) {
            setUser(null);
            setLoading(false);
            return;
        }

        try {
            const res = await http.get("/me");
            setUser(res.data);
        } catch (err) {
            clearAuth();
            setUser(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadUser();
    }, []);

    const logout = () => {
        clearAuth();
        setUser(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                setUser,
                loading,
                logout,
                isLoggedIn: !!user,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
};
