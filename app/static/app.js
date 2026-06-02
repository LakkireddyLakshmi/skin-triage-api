// Tiny vanilla-JS frontend for the Skin Triage API.
// Talks to the same server it is served from, so no base URL / CORS needed.

const TOKEN_KEY = "skin_triage_token";
const $ = (id) => document.getElementById(id);

let mode = "login"; // "login" | "register"

// ---- helpers ----
function token() {
  return localStorage.getItem(TOKEN_KEY);
}
function setMsg(el, text, kind) {
  el.textContent = text;
  el.className = "msg" + (kind ? " " + kind : "");
}
async function api(path, { method = "GET", body, auth = false } = {}) {
  const headers = {};
  if (auth) headers["Authorization"] = "Bearer " + token();
  // JSON bodies are strings → declare the type. FormData (file upload) must be
  // left alone so the browser sets the multipart boundary itself.
  if (typeof body === "string") headers["Content-Type"] = "application/json";
  const res = await fetch(path, { method, headers, body });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`);
  return data;
}

// ---- view switching ----
function showApp() {
  $("auth-view").classList.add("hidden");
  $("app-view").classList.remove("hidden");
  loadMe();
  loadHistory();
}
function showAuth() {
  $("app-view").classList.add("hidden");
  $("auth-view").classList.remove("hidden");
}

// ---- auth tabs ----
function setMode(next) {
  mode = next;
  const login = next === "login";
  $("tab-login").classList.toggle("active", login);
  $("tab-register").classList.toggle("active", !login);
  $("auth-submit").textContent = login ? "Log in" : "Sign up";
  setMsg($("auth-msg"), "");
}
$("tab-login").onclick = () => setMode("login");
$("tab-register").onclick = () => setMode("register");

// ---- auth submit ----
$("auth-form").onsubmit = async (e) => {
  e.preventDefault();
  const btn = $("auth-submit");
  btn.disabled = true;
  const payload = JSON.stringify({ email: $("email").value, password: $("password").value });
  try {
    if (mode === "register") {
      await api("/auth/register", { method: "POST", body: payload, });
      setMsg($("auth-msg"), "Account created! Logging you in…", "ok");
    }
    const data = await api("/auth/login", { method: "POST", body: payload });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    showApp();
  } catch (err) {
    setMsg($("auth-msg"), err.message, "err");
  } finally {
    btn.disabled = false;
  }
};

// ---- logged-in actions ----
async function loadMe() {
  try {
    const me = await api("/auth/me", { auth: true });
    $("who").textContent = "Signed in as " + me.email;
  } catch {
    logout();
  }
}

async function loadHistory() {
  const list = $("history");
  try {
    const scans = await api("/scans", { auth: true });
    if (!scans.length) {
      list.innerHTML = '<li class="history-empty">No scans yet — upload one above.</li>';
      return;
    }
    list.innerHTML = scans
      .map((s) => {
        const pct = (s.confidence * 100).toFixed(1);
        const date = new Date(s.created_at).toLocaleString();
        return `<li><span>${s.predicted_label} <small>(${pct}%)</small></span><span class="h-date">${date}</span></li>`;
      })
      .join("");
  } catch (err) {
    list.innerHTML = `<li class="history-empty">${err.message}</li>`;
  }
}

$("scan-form").onsubmit = async (e) => {
  e.preventDefault();
  const btn = $("scan-submit");
  const fileInput = $("file");
  if (!fileInput.files.length) return;
  btn.disabled = true;
  setMsg($("scan-msg"), "Analyzing… (the model may take up to a minute to wake up)", "");
  $("result").classList.add("hidden");
  try {
    const fd = new FormData();
    fd.append("file", fileInput.files[0]);
    const scan = await api("/scans", { method: "POST", body: fd, auth: true });
    $("result-label").textContent = scan.predicted_label;
    $("result-conf").textContent = (scan.confidence * 100).toFixed(1) + "% confidence";
    $("result").classList.remove("hidden");
    setMsg($("scan-msg"), "Saved to your history.", "ok");
    fileInput.value = "";
    loadHistory();
  } catch (err) {
    setMsg($("scan-msg"), err.message, "err");
  } finally {
    btn.disabled = false;
  }
};

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  showAuth();
}
$("logout").onclick = logout;

// ---- boot ----
setMode("login");
if (token()) showApp();
else showAuth();
