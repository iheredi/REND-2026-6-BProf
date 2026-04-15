function goLogin() {
  window.location.href = "login.html";
}

function goIndex() {
    window.location.href = "index.html";
}

function logout() {
  localStorage.removeItem("token");
}

async function ping() {
  try {
    const res = await fetch("http://127.0.0.1:5000/ping");
    const data = await res.json();

    document.getElementById("result").textContent =
      JSON.stringify(data.msg, null, 2);

  } catch (err) {
    document.getElementById("result").textContent =
      "Hiba: " + err;
  }
}