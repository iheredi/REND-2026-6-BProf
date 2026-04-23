
import Header from "../components/Header";
import Footer from "../components/Footer";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
    const { user, role } = useAuth();
    return (
        <>
            <Header />
            <div className="container">
                <h3 style={{ "color": "blue" }}>
                    Csak sikeres login után érhető el.
                </h3>
                <p>
                    ID: {user.id}
                    <br />
                    Név: {user.name}
                    <br/>
                    Email: {user.email}
                    <br/>
                </p>
                <p>
                    Szerepkör: {role}
                </p>
            </div>
            <Footer />
        </>
    );
}
