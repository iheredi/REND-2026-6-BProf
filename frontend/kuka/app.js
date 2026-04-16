const SERVER = "http://127.0.0.1:5000"
const CLIENT = "http://127.0.0.1:8000"


function initHeader() {
  const container = document.getElementById("nav-buttons");
  if (!container) return;

  const token = localStorage.getItem("token");

  if (token) {
    container.innerHTML = `        
      <button class="btn btn-sm btn-outline-light" onclick="logout()">Logout</button>
    `;
  } else {
    container.innerHTML = `
      <button class="btn btn-sm btn-light" onclick="goLogin()">Login</button>
    `;
  }
}

async function loadComponent(id, file) {
  file = file + ".html"
  try {
    const res = await fetch(file);
    if (!res.ok) throw new Error("Nem sikerült betölteni: " + file);

    const html = await res.text();
    document.getElementById(id).innerHTML = html;

  } catch (err) {
    console.error(err);
  }
}



// token helpers
function getToken(){ return localStorage.getItem("token"); }
function removeToken(){ localStorage.removeItem("token"); }

// returns payload or null
function decodeToken(token){
  try { return token ? jwt_decode(token) : null; }
  catch { return null; }
}

// returns true if token exists and not expired
function isAuthenticated(){
  const token = getToken();
  const payload = decodeToken(token);
  if(!payload) return false;
  if(payload.exp && typeof payload.exp === "number"){
    const now = Math.floor(Date.now()/1000);
    return now < payload.exp;
  }
  return true; // no exp claim => treat as valid for UI
}


document.addEventListener("DOMContentLoaded", async () => {
  await loadComponent("header", "_header");
  await loadComponent("footer", "_footer");

  initHeader();

  if (!isAuthenticated()) {
    removeToken();

    if (!isPublicPage()) {
      goLogin();
    }
  }
});


function isPublicPage() {  
  const p = location.pathname;      
  return p.endsWith("/login.html") || p === "/login" || p === "/";
}

function goLogin() {
  window.location.href = "login.html";
}

function goIndex() {
    window.location.href = "index.html";
}

function logout() {
  localStorage.removeItem("token");
  window.location.href=CLIENT + "/index.html"
}

async function ping() {
  try {
    const res = await fetch(SERVER+"/ping");
    const data = await res.json();

    document.getElementById("result").textContent =
      JSON.stringify(data.msg, null, 2);

  } catch (err) {
    document.getElementById("result").textContent =
      "Hiba: " + err;
  }
}