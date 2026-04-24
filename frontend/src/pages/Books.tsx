import { useEffect, useState } from "react";
import Header from "../components/Header";
import Footer from "../components/Footer";
import http from "../api/_http_client";

interface Book {
    book_id: number;
    title: string;
    author: string;
    available_item_id: number;
    is_borrowable: boolean;
    can_be_borrowed_now: boolean;
}

export default function Books() {
    const [books, setBooks] = useState<Book[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchBooks = async () => {
            try {
                const res = await http.get("/books-with-available-item");
                setBooks(res.data);
            } catch (err) {
                console.error("Hiba a könyvek lekérésekor:", err);
            } finally {
                setLoading(false);
            }
        };

        fetchBooks();
    }, []);

    const handleReserve = async (bookId: number) => {
        try {
            await http.post("/reservations", {
                book_id: bookId
            });

            // ujra beallitjuk a konyveket
            setBooks(prev => {
                return prev.map(book => {
                    if (book.book_id === bookId) {
                        return {
                            ...book,
                            can_be_borrowed_now: false
                        };
                    }

                    return book;
                });
            });

            alert("Sikeres foglalás!");

        } catch (err: any) {
            const status = err.response?.status;

            if (status === 400) {
                alert("Már van aktív foglalásod erre a könyvre.");
            } else if (status === 404) {
                alert("A könyv nem található.");
            } else if (status === 401) {
                alert("Be kell jelentkezned.");
            } else {
                alert("Ismeretlen hiba történt.");
            }

            console.error("Foglalás hiba:", err);
        }
    };

    return (
        <>
            <Header />
            <div className="container">
                <h3 className="mb-4 text-start">Kölcsönözhető könyvek</h3>
                {loading && <div>Loading...</div>}

                {!loading && books.length === 0 && (
                    <div>Nincs elérhető könyv.</div>
                )}

                {!loading && books.length > 0 && (
                    <table className="table table-striped">
                        <thead>
                            <tr>
                                <th>Cím</th>
                                <th>Szerző</th>
                                <th>Kölcsönözhető</th>
                                <th>Elérhető most</th>
                                <td>Műveletek</td>
                            </tr>
                        </thead>
                        <tbody>
                            {books.map((book) => (
                                <tr key={book.book_id}>
                                    <td>{book.title}</td>
                                    <td>{book.author}</td>
                                    <td>
                                        {book.is_borrowable ? "Igen" : "Nem"}
                                    </td>
                                    <td>
                                        {book.can_be_borrowed_now ? "✔" : "✖"}
                                    </td>
                                    <td>
                                        {book.is_borrowable && book.can_be_borrowed_now ? (
                                            <button
                                                className="btn btn-sm btn-primary"
                                                onClick={() => handleReserve(book.book_id)}
                                            >
                                                Foglalás
                                            </button>
                                        ) : (
                                            "-"
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
            <Footer />
        </>
    );
}
