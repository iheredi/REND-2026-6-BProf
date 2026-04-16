import { useState } from "react";
import { ping } from "../api/ping";

import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Home() {
    const [msg, setMsg] = useState("");

    const handlePing = async () => {
        try {
            const data = await ping();
            setMsg(data.msg);
        } catch (err) {
            setMsg("error");
        }
    };

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
