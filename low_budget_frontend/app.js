const API_URL = "http://127.0.0.1:5000";

document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");

    if (!token) {        
        return;
    }

    const res = await apiCall("/me", "GET");

    if (!res.ok) {
        logout(); // token hibás / lejárt
        return;
    }

    if (token && role) setupDashboard(role);
});

async function apiCall(endpoint, method = "GET", body = null) {
    const token = localStorage.getItem("token");
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    try {
        const res = await fetch(API_URL + endpoint, options);
        const data = await res.json();
        return { ok: res.ok, status: res.status, data };
    } catch (e) {
        return { ok: false, data: { msg: "API Hiba vagy a szerver nem fut!" } };
    }
}

async function login() {
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;
    const res = await apiCall("/login", "POST", { email, password });
    if (res.ok) {
        localStorage.setItem("token", res.data.access_token);
        localStorage.setItem("role", res.data.role);
        localStorage.setItem("email", res.data.user);
        setupDashboard(res.data.role);
    } else alert(res.data.msg);
}

function logout() { localStorage.clear(); location.reload(); }

async function register() {
    const body = {
        name: document.getElementById("reg-name").value,
        email: document.getElementById("reg-email").value,
        password: document.getElementById("reg-password").value,
        city: document.getElementById("reg-city").value,
        street: document.getElementById("reg-street").value,
        zip_code: document.getElementById("reg-zip").value,
        phone: "+3600000000"
    };
    const res = await apiCall("/register", "POST", body);
    alert(res.data.msg);
}

async function setupDashboard(role) {
    document.getElementById("auth-view").classList.add("hidden");
    document.getElementById("main-view").classList.remove("hidden");
    document.getElementById("user-greeting").innerText = localStorage.getItem("email");
    document.getElementById("user-role-badge").innerText = role.toUpperCase();

    document.getElementById("panel-profile").classList.remove("hidden");
    loadProfileData();

    if (role === "user") {
        document.getElementById("panel-user").classList.remove("hidden");
        refreshUserPanel();
    } else if (role === "librarian") {
        document.getElementById("panel-librarian").classList.remove("hidden");
        // loadAllLoans();
    } else if (role === "admin") {
        document.getElementById("panel-admin").classList.remove("hidden");
    }
}

//teszt 2 -OK, úgy tűnik
async function deleteBook() {
    const book_id = document.getElementById("edit-book-id").value;

    if (!book_id) {
        alert("Add meg a könyv ID-ját!");
        return;
    }

    if (!confirm("Biztosan törölni szeretnéd ezt a könyvet és az összes példányát?")) {
        return;
    }

    const res = await apiCall(`/admin/books/${book_id}`, "DELETE");

    if (res.ok) {
        alert(res.data.msg);
    } else {
        alert(res.data.msg);
    }
}

// ================= PROFIL (Közös) =================
async function loadProfileData() {
    const res = await apiCall("/user/profile");
    if (res.ok) {
        if (document.getElementById("user-balance")) document.getElementById("user-balance").innerText = res.data.balance;

        // JAVÍTÁS: Most már kiírja az irányítószámot is a város előtt
        document.getElementById("current-profile-info").innerHTML = `
                <strong>Név:</strong> ${res.data.name}<br>
                <strong>Email:</strong> ${res.data.email}<br>
                <strong>Tel:</strong> ${res.data.phone || 'Nincs'}<br>
                <strong>Cím:</strong> ${res.data.address.zip_code || ''} ${res.data.address.city || ''}, ${res.data.address.street || ''}`;

        // Beállítjuk az input mezőket is az aktuális értékekre
        document.getElementById("update-phone").value = res.data.phone || "";
        document.getElementById("update-zip").value = res.data.address.zip_code || "";
        document.getElementById("update-city").value = res.data.address.city || "";
        document.getElementById("update-street").value = res.data.address.street || "";
    }
}

async function updateProfile() {
    const body = {
        phone: document.getElementById("update-phone").value,
        zip_code: document.getElementById("update-zip").value,
        city: document.getElementById("update-city").value,
        street: document.getElementById("update-street").value
    };
    const res = await apiCall("/user/profile", "POST", body);
    alert(res.data.msg); loadProfileData();
}

// ================= OLVASÓI FUNKCIÓK =================

async function refreshUserPanel() {
    loadUserBooks();
    loadUserLoans();
    loadUserDebts();
    //loadUserReservations();
}

async function loadUserBooks(isSearch = false) {
    let endpoint = "/user/books";
    if (isSearch) {
        const query = document.getElementById("user-search-input").value;
        endpoint += `?search=${query}`;
    }

    const res = await apiCall(endpoint);
    if (!res.ok) { alert(res.data.msg); return; }

    document.getElementById("user-books-list").innerHTML = res.data.map(b => {
        let actionBtn = "";
        if (b.user_specific_status === "Már nálad van" || b.user_specific_status === "Jóváhagyásra vár") {
            actionBtn = `<button class='btn-info' disabled>${b.user_specific_status}</button>`;
        } else if (!b.is_borrowable) {
            actionBtn = `<span style='color: red; font-weight: bold; padding: 10px;'>Nem kölcsönözhető</span>`;
        } else if (b.can_be_borrowed_now) {
            actionBtn = `<button class='btn-success' onclick='requestLoan(${b.available_item_id})'>Kölcsönzés kérése</button>`;
        } else {
            actionBtn = `<button class='btn-warning' onclick='reserveBook(${b.book_id})'>Előjegyzés (Várólista)</button>`;
        }
        return `
            <div class='card'>
                <strong>${b.title}</strong> (Szerző: ${b.author})<br>
                <div style="margin-top: 10px;">
                    <button class='btn-primary' onclick='showBookDetails(${b.book_id})'>Részletek</button>
                    ${actionBtn}
                </div>
            </div>`;
    }).join('');
}

async function showBookDetails(id) {
    const res = await apiCall(`/user/books/${id}`);
    if (res.ok) {
        alert(`📖 RÉSZLETES ADATOK:\n\nCím: ${res.data.title}\nSzerző: ${res.data.author}\nKölcsönözhető-e: ${res.data.is_borrowable ? 'Igen' : 'Nem'}\nÖsszes példány: ${res.data.total_copies} db\nEbből szabad: ${res.data.available_copies} db`);
    } else { alert(res.data.msg); }
}

async function requestLoan(id) {
    const res = await apiCall("/user/request-loan", "POST", { book_item_id: id });
    alert(res.data.msg); refreshUserPanel();
}

async function reserveBook(bookId) {
    const res = await apiCall("/user/reservations", "POST", { book_id: bookId });
    alert(res.data.msg); refreshUserPanel();
}

async function loadUserLoans() {
    const res = await apiCall("/user/loans");
    if (!res.ok) return;
   
    document.getElementById("user-loans-list").innerHTML = res.data.map(l => `
            <div style='background:${l.is_active ? "#e8f5e9" : "#eee"}; padding:10px; margin-bottom:5px; border-left: 5px solid ${l.is_active ? "green" : "gray"}'>
                Vonalkód: <strong>${l.barcode}</strong><br/>
                <strong>${l.book_title}</strong> <small>(Loan ID: ${l.loan_id})</small><br>
                Státusz: <strong>${l.status}</strong><br>
                ${l.is_active ? `Hátralévő idő: <strong style='color:${l.days_remaining.includes("Lejárt") ? "red" : "black"}'>${l.days_remaining}</strong><br>` : ''}
                Hosszabbítva: ${l.extension_count || 0} / 2 alkalommal<br>
                ${(l.is_active && (l.extension_count || 0) < 2) ? `<button class='btn-primary' style='margin-top:5px;' onclick='extendLoan(${l.loan_id})'>Hosszabbítás (+14 nap)</button>` : ''}
                ${(l.status === 'Jóváhagyásra vár (Pending)') ? `<button class='btn-danger' style='margin-top:5px;' onclick='cancelLoanReq(${l.loan_id})'>Igény Törlése</button>` : ''}
            </div>`).join('');
}

async function extendLoan(id) {
    const res = await apiCall("/user/loan", "POST", { loan_id: id });
    alert(res.data.msg); loadUserLoans();
}

async function cancelLoanReq(id) {
    const res = await apiCall(`/user/loan/${id}`, "DELETE");
    alert(res.data.msg); refreshUserPanel();
}

async function loadUserDebts() {
    const res = await apiCall("/user/debts");
    if (res.ok) document.getElementById("user-debts-list").innerHTML = res.data.length ? res.data.map(d => `<div style='color:red'>${d.amount} Ft - ${d.reason}</div>`).join('') : "Nincs bírság.";
}

async function loadUserReservations() {
    const res = await apiCall("/user/reservations");
    const list = document.getElementById("user-reservations-list");
    if (!res.ok) { list.innerHTML = "<small style='color: red;'>Hiba a betöltéskor.</small>"; return; }
    if (res.data.length === 0) { list.innerHTML = "<small>Nincs aktív előjegyzésed.</small>"; return; }
    list.innerHTML = res.data.map(r => `
            <div style="background: #f1f3f5; padding: 10px; margin-bottom: 5px; border-left: 5px solid var(--info); border-radius: 4px;">
                <strong>${r.title}</strong><br>
                <small>Igényelve: ${r.reserved_at}</small><br>
                <button class="btn-danger" style="padding: 3px 8px; font-size: 11px; margin-top: 5px;" 
                    onclick="cancelReservation(${r.reservation_id})">Visszavonás</button>
            </div>`).join('');
}

async function cancelReservation(id) {
    if (!confirm("Biztosan vissza szeretnéd vonni az előjegyzést?")) return;
    const res = await apiCall(`/user/reservations/${id}`, "DELETE");
    alert(res.data.msg); refreshUserPanel();
}

// ================= KÖNYVTÁROSI FUNKCIÓK =================
//async function loadLibrarianBooks() { alert("API FIGYELMEZTETÉS: A könyvtáros keresőjéhez fel kell készíteni a könyv listázó API-t a ?search paraméterre!"); }
async function loadLibrarianBooks() {
    const query = document.getElementById("lib-search-input").value;

    let endpoint = "/librarian/books";
    if (query) {
        endpoint += `?search=${encodeURIComponent(query)}`;
    }

    const res = await apiCall(endpoint);

    if (!res.ok) {
        alert(res.data.msg || "Hiba történt a könyvek betöltésekor!");
        return;
    }

    const list = document.getElementById("lib-books-list");

    if (!res.data.length) {
        list.innerHTML = "<small>Nincs találat.</small>";
        return;
    }

    list.innerHTML = res.data.map(b => `
        <div class="card">
            <strong>${b.title}</strong> (Szerző: ${b.author})<br>

            <div style="margin-top: 8px;">
                📦 Összes példány: <b>${b.total_copies}</b><br>
                ✅ Elérhető: <b style="color: green;">${b.available_copies}</b><br>
            </div>

            <div style="margin-top: 10px;">      

                <button class="btn-primary" onclick="showBookDetails(${b.book_id})">
                    Részletek
                </button>
            </div>
        </div>
    `).join('');
}

async function loadPendingLoans() {
    const res = await apiCall("/librarian/pending-loans");

    if (!res.ok) {
        alert(res.data.msg || "Hiba a várakozó kölcsönzések betöltésekor!");
        return;
    }

    const list = document.getElementById("lib-all-books-pending");

    if (!res.data.length) {
        list.innerHTML = "<small>Nincs jóváhagyásra váró kérés.</small>";
        return;
    }
    
    list.innerHTML = res.data.map(l => `
        <div class="card" style="border-left: 5px solid var(--warning);">
            <strong>${l.book_title}</strong><br>

            👤 ${l.user_name} (${l.user_email})<br>
            🔖 Vonalkód: ${l.barcode} <small>Item ID: ${l.book_item_id}</small><br>
            📅 Kérés: ${l.request_date}<br>

            <div style="margin-top: 10px;">
                <button class="btn-success" onclick="approveLoan(${l.loan_id})">
                    ✔ Jóváhagyás
                </button>
                <button class="btn-danger" onclick="deleteLoan(${l.loan_id})">
                    X Törlés
                </button>
            </div>
        </div>
    `).join('');
}
async function approveLoan(loanId) {
    if (!confirm("Biztosan jóváhagyod?")) return;

    const res = await apiCall(`/librarian/approve-loan/${loanId}`, "POST");

    alert(res.data.msg || "Jóváhagyva");

    loadPendingLoans();
}

async function deleteLoan(loanId) {
    if (!confirm("Biztosan törlöd?")) return;

    const res = await apiCall(`/librarian/delete-loan/${loanId}`, "DELETE");

    alert(res.data.msg || "Törölve");

    loadPendingLoans();
}

async function libLoanForUser() {
    const userId = document.getElementById("lib-borrow-user").value;
    const itemId = document.getElementById("lib-borrow-item").value;

    if (!userId || !itemId) {
        alert("Add meg a felhasználó ID-t és a könyvpéldány ID-t!");
        return;
    }

    const res = await apiCall("/librarian/create-loan", "POST", {
        user_id: parseInt(userId),
        book_item_id: parseInt(itemId)
    });

    alert(res.data.msg || "Kölcsönzés létrehozva");

    loadAllLoans?.(); // ha létezik, frissít
}

async function loadAllLoans() {
    const res = await apiCall("/librarian/loans");
    if (!res.ok) return;
    
    const list = document.getElementById("lib-all-loans-list")
    list.innerHTML = res.data.map(l => `
            <div style='padding:5px; border-bottom:1px solid #ccc; background:${l.is_overdue ? "#ffdada" : "white"}'>
                Könyv: <strong>${l.book_cim}</strong><br/><small>Barcode: ${l.book_barcode}, Item ID: ${l.book_item_id}</small><br/>
                User: ${l.user_name} (ID: ${l.user_id}) | Loan ID: ${l.loan_id} <br>
                Határidő: ${l.due_date || 'Nincs'}<br>
                <button class='btn-warning' onclick='libReturnLoan("${l.book_barcode}")'>Visszavétel</button>
                <button class='btn-info' onclick='libExtendLoan(${l.loan_id})'>Hosszabbítás</button>
            </div>`).join('');
    if (!res.data.length) {
        list.innerHTML = "<small>Nincs kikölcsönzött könyv.</small>";
        return;
    }
 
}
async function libExtendLoan(id) {
    const res = await apiCall(`/librarian/extend-loan/${id}`, "POST");
    alert(res.data.msg);
    loadAllLoans();
}
async function libReturnLoan(barcode) {
    //const barcode = document.getElementById("return-barcode").value;
    const res = await apiCall("/librarian/return-loan", "POST", { barcode });
    alert(res.data.msg);
    loadAllLoans();
}
async function libReturnLoanManual() {
    const barcode = document.getElementById("return-barcode").value;
    const res = await apiCall("/librarian/return-loan", "POST", { barcode });
    alert(res.data.msg);
    loadAllLoans();
    barcode = "";
}
async function createDebt() {
    const body = { user_id: parseInt(document.getElementById("fine-user-id").value), amount: parseFloat(document.getElementById("fine-amount").value), reason: document.getElementById("fine-reason").value };
    const res = await apiCall("/librarian/debts", "POST", body); alert(res.data.msg);
}

// ================= ADMIN FUNKCIÓK =================

//második próba, hogy hozzá adja a könyv példányokat
async function addBookItems() {
    const book_id = parseInt(document.getElementById("add-item-bookid").value);
    const count = parseInt(document.getElementById("add-item-count").value);

    if (!book_id || !count) {
        alert("Kérlek add meg a könyv ID-t és a darabszámot!");
        return;
    }

    const body = { book_id, count };
    const res = await apiCall("/admin/book-items", "POST", body);

    if (res.ok) {
        alert(res.data.msg + "\nVonalkódok:\n" + res.data.barcodes.join("\n"));
    } else {
        alert(res.data.msg);
    }
}


async function createBook() {
    const body = { title: document.getElementById("add-book-title").value, author: document.getElementById("add-book-author").value, is_borrowable: document.getElementById("add-book-borrowable").value === "true" };
    const res = await apiCall("/admin/books", "POST", body); alert(res.data.msg);
}
async function addBookItems() {
    const body = { book_id: parseInt(document.getElementById("add-item-bookid").value), count: parseInt(document.getElementById("add-item-count").value) };
    const res = await apiCall("/admin/book-items", "POST", body); alert(res.data.msg);
}
async function editBook() { alert("API FIGYELMEZTETÉS: Ehhez hiányzik a PUT /admin/books/<id> végpont!"); }
//async function deleteBook() { alert("API FIGYELMEZTETÉS: Ehhez hiányzik a DELETE /admin/books/<id> végpont!"); }
async function changeItemStatus() { alert("API FIGYELMEZTETÉS: Ehhez hiányzik a PUT /admin/book-items/<id>/status végpont!"); }

