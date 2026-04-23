import Header from "../components/Header";
import Footer from "../components/Footer";
import { useAuth } from "../context/AuthContext";


export default function Home() {
    const { user, isLoggedIn, role } = useAuth();
    return (
        <>
            <Header />
            <div className="container mt-5">
                {!isLoggedIn ? (
                    <div>Válassz a fenti menüből!</div>
                ) : (
                    <div>Válassz a fenti menüből, <strong>{user?.name} ({user?.email})</strong>!
                        <div>Szerepköröd: <strong>{role}</strong></div>
                    </div>
                )}
            </div>
            <Footer />
        </>
    );
}
