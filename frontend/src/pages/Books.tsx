
import Header from "../components/Header";
import Footer from "../components/Footer";
import { useAuth } from "../context/AuthContext";

export default function Books() { 
    return (
        <>
            <Header />
            <div className="container">
                <h3 style={{ "color": "blue" }}>
                    Books
                </h3>                
            </div>
            <Footer />
        </>
    );
}
