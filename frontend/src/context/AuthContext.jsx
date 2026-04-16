import { createContext, useContext, useEffect, useState } from "react";
import { getToken, logout as clearAuth } from "../api/auth";
import http from "../api/_http_client";

const AuthContext = createContext();

export function AuthProvider({ children }) {
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

export const useAuth = () => useContext(AuthContext);
