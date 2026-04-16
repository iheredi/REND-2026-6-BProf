import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { login, saveAuth, logout } from "../api/auth";
import http from "../api/_http_client";
import { useAuth } from "../context/AuthContext";
import { ROUTES } from "../routes";
import { consumeFlash, setFlash } from "../utils/flash";

import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Login() {
    const navigate = useNavigate();
    const { setUser } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [flash, setFlashState] = useState("");

    useEffect(() => {
        const msg = consumeFlash();
        if (msg) setFlashState(msg);
    }, []);

    const handleLogin = async () => {
        try {
            // 1. login
            const res = await login(email, password);

            // 2. token mentés
            saveAuth(res.data);

            // 3. user lekérés (VALIDÁCIÓ)
            const meRes = await http.get("/me");

            // 4. globális state frissítés
            setUser(meRes.data);

            setError("");

            // 5. redirect
            navigate(ROUTES.home);
        } catch (err) {
            console.log("LOGIN ERROR RAW:", err);
            console.log("RESPONSE:", err.response);

            const msg = err.response?.data?.msg || "Hiba történt";

            setFlash(msg);
            setFlashState(msg);
        }
    };

    return (
        <>
            <Header />
            <div className="container">
                <div className="row justify-content-center">
                    <div className="col-md-4">

                        <h3 className="mb-4 text-center">Login</h3>

                        {flash && (
                            <div className="alert alert-danger">
                                {flash}
                            </div>
                        )}

                        <form onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
                            <div className="mb-3">
                                <label className="form-label">Email</label>
                                <input
                                    type="email"
                                    className="form-control"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>

                            <div className="mb-3">
                                <label className="form-label">Jelszó</label>
                                <input
                                    type="password"
                                    className="form-control"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>

                            <button type="submit" className="btn btn-primary w-100">
                                Bejelentkezés
                            </button>

                        </form>

                    </div>
                </div>
            </div>
            <Footer />
        </>
    );
}
