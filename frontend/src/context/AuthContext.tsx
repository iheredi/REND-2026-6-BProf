import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getToken, logout as clearAuth } from "../api/auth";
import http from "../api/_http_client";

interface User {
    id: string;
    email: string;
    name: string;
}

interface AuthContextType {
    user: User | null;    
    setUser: (user: User | null) => void;
    role: string | null;
    setRole: (role: string | null) => void;
    loading: boolean;
    logout: () => void;
    isLoggedIn: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [role, setRole] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const loadUser = async () => {
        const token = getToken();

        if (!token) {
            setUser(null);
            setRole(null);
            setLoading(false);
            return;
        }
        
        try {        
            const res = await http.get("/me");
            setRole(res.data.role);
            setUser({
                id: res.data.id,
                email: res.data.email,
                name: res.data.name
            });            
        } catch (err: any) {
            if (err.response?.status === 401) {
                clearAuth();
                setUser(null);
                setRole(null);
            } else {
                // nem auth hiba - nem kell logout
                console.error("Auth check hiba:", err)
            }
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
        setRole(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,                
                setUser,
                role,
                setRole,
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
