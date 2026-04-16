import { useState } from "react";
import { ping } from "../api/ping";

import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Ping() {
    const [msg, setMsg] = useState("");
    const [status, setStatus] = useState("");
    const [headers, setHeaders] = useState({});

    const handlePing = async () => {
        try {
            const res = await ping();

            setMsg(res.data.msg);
            setStatus(res.status);
            setHeaders(res.headers);
            console.log(res);
        } catch (err) {
            console.log(err);
        }
    };

    return (
        <>
            <Header />
            <div className="container">

                <h3 className="mb-4 text-start">Backend Ping</h3>

                <div className="d-flex gap-2 align-items-center">
                    <button className="btn btn-primary" onClick={handlePing}>
                        Ping
                    </button>

                    <span className="badge bg-secondary">
                        {msg || "no response yet"}
                    </span>
                </div>
                <div className="mt-3">
                    <div>Status: {status}</div>
                    <div>Message: {msg}</div>

                    <pre className="mt-2 small">
                        {JSON.stringify(headers, null, 2)}
                    </pre>
                </div>
            </div>
            <Footer />
        </>
    );
}
