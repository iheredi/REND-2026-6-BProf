import { Link, useNavigate } from "react-router-dom";
import { ROUTES } from "../routes";
import { useAuth } from "../context/AuthContext";

export default function Header() {
    const navigate = useNavigate();
    const { isLoggedIn, logout, role } = useAuth();

    const handleLogout = () => {
        logout();
        navigate(ROUTES.home);
    };


    return (
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark mb-3">
            <div className="container">
                <Link className="navbar-brand" to={ROUTES.home}>
                    Bibliotar
                </Link>

                <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span className="navbar-toggler-icon"></span>
                </button>

                <div className="collapse navbar-collapse navbar-expand-lg align-items-end" id="navbarNav">
                    <ul className="navbar-nav">
                        <li className="nav-item">
                            <Link className="nav-link" to={ROUTES.ping}>
                                Ping
                            </Link>
                        </li>
                        {(role === "librarian" || role === "admin") && (
                            <>
                                <li className="nav-item">
                                    <Link className="nav-link" to="">
                                        Konyvtaros1
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" to="">
                                        Konyvtaros2
                                    </Link>
                                </li>
                            </>
                        )}
                        {role === "admin" && (
                            <>
                                <li className="nav-item">
                                    <Link className="nav-link" to="">
                                        Admin1
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" to="">
                                        Admin2
                                    </Link>
                                </li>
                            </>
                        )}
                    </ul>
                    <ul className="navbar-nav ms-auto">
                        <li className="nav-item">
                            <Link className="nav-link" to={ROUTES.vedett}>
                                Profil
                            </Link>
                        </li>

                        {!isLoggedIn ? (
                            <li className="nav-item">
                                <Link className="nav-link" to={ROUTES.login}>
                                    Login
                                </Link>
                            </li>
                        ) : (
                            <li className="nav-item">
                                <button
                                    className="btn btn-link nav-link"
                                    onClick={handleLogout}
                                >
                                    Logout
                                </button>
                            </li>
                        )}
                    </ul>
                </div>
            </div>
        </nav>
    );
}