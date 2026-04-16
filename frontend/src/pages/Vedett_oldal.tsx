
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Vedett() {    
    return (
        <>
            <Header />
            <div className="container">
                <h3 style={{"color": "red"}}>
                Csak sikeres login után érhető el.
                </h3>
            </div>
            <Footer />
        </>
    );
}
