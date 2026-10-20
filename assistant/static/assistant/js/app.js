const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const promptEl = document.getElementById("prompt");
const sendBtn = document.getElementById("send");
const banner = document.getElementById("offline-banner");
const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;

function addMsg(text, who) {
  const div = document.createElement("div");
  div.className = "msg " + who;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

// Offline detection
function updateOnline() {
  banner.classList.toggle("d-none", navigator.onLine);
  sendBtn.disabled = !navigator.onLine;
}
window.addEventListener("online", updateOnline);
window.addEventListener("offline", updateOnline);
updateOnline();

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptEl.value.trim();
  if (!prompt || !navigator.onLine) return;
  addMsg(prompt, "user");
  promptEl.value = "";
  const loading = addMsg("Thinking...", "bot");
  try {
    const res = await fetch("/api/chat/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify({ prompt }),
    });
    const data = await res.json();
    loading.textContent = data.reply || data.error || "Something went wrong.";
  } catch {
    loading.textContent = "Network error. Please try again.";
  }
});

document.getElementById("clear").addEventListener("click", () => {
  chat.innerHTML = ""; promptEl.value = "";
});

// Register service worker
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}