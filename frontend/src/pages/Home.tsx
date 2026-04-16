import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Home() {    
    return (
        <>
            <Header />
            <div className="container mt-5">
                <div>Válassz a fenti menüből!</div>
            </div>
            <Footer />
        </>
    );
}
