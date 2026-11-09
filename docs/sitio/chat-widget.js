/*
 * GECTAM - Widget de chat (burbuja flotante)
 *
 * Para usarlo en CUALQUIER página (incluida WordPress) basta con pegar:
 *   <script src="chat-widget.js" data-backend="https://gectam-bot.onrender.com" defer></script>
 */
(function () {
  "use strict";

  var script = document.currentScript;
  var BACKEND = (script && script.getAttribute("data-backend")) || "https://gectam-bot.onrender.com";

  /* ---------- Estilos (con prefijo gc- para no chocar con la página) ---------- */
  var css = [
    ".gc-root{--tinta:#16164a;--tinta2:#46467a;--papel:#f0f0ea;--linea:#cfcfd8;--senal:#ff5c93;--azul:#2d4bd8;font-family:'Figtree',system-ui,-apple-system,'Segoe UI',sans-serif;}",
    ".gc-root *{box-sizing:border-box}",
    ".gc-fab{position:fixed;right:20px;bottom:20px;z-index:99998;display:flex;align-items:center;gap:10px;border:2px solid var(--tinta);cursor:pointer;background:var(--senal);color:var(--tinta);font:700 15px/1 inherit;font-family:inherit;padding:13px 18px 13px 16px;border-radius:999px;box-shadow:4px 4px 0 var(--tinta)}",
    ".gc-fab:hover{background:#ff7aa6}",
    ".gc-fab:focus-visible,.gc-send:focus-visible,.gc-close:focus-visible,.gc-chip:focus-visible{outline:3px solid var(--tinta);outline-offset:2px}",
    ".gc-fab svg{width:22px;height:22px;flex:none}",
    ".gc-panel{position:fixed;right:20px;bottom:20px;z-index:99999;width:380px;max-width:calc(100vw - 24px);height:560px;max-height:calc(100vh - 24px);display:none;flex-direction:column;background:#fff;border-radius:14px;overflow:hidden;box-shadow:6px 6px 0 var(--tinta);border:2px solid var(--tinta)}",
    ".gc-panel.gc-open{display:flex}",
    ".gc-head{background:var(--azul);color:#fff;padding:14px 16px;display:flex;align-items:center;justify-content:space-between;gap:10px}",
    ".gc-title{font-weight:700;font-size:16px;line-height:1.2}",
    ".gc-sub{font-size:12.5px;opacity:.75;margin-top:2px}",
    ".gc-close{background:transparent;border:0;color:#fff;cursor:pointer;font-size:26px;line-height:1;padding:4px 8px;border-radius:8px}",
    ".gc-close:hover{background:rgba(255,255,255,.12)}",
    ".gc-msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:9px;background:var(--papel)}",
    ".gc-msg{max-width:85%;padding:9px 13px;border-radius:14px;font-size:14.5px;line-height:1.45;white-space:pre-wrap;word-wrap:break-word}",
    ".gc-bot{background:#fff;color:var(--tinta);align-self:flex-start;border:1px solid var(--linea);border-bottom-left-radius:4px}",
    ".gc-user{background:var(--azul);color:#fff;align-self:flex-end;border-bottom-right-radius:4px}",
    ".gc-note{align-self:flex-start;font-size:12.5px;color:var(--tinta2);padding:0 4px}",
    ".gc-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:2px}",
    ".gc-chip{font:inherit;font-size:13.5px;background:#fff;color:var(--tinta);border:2px solid var(--tinta);border-radius:999px;padding:6px 12px;cursor:pointer}",
    ".gc-chip:hover{background:var(--tinta);color:#fff}",
    ".gc-typing{display:inline-flex;gap:4px;padding:12px 14px}",
    ".gc-typing i{width:7px;height:7px;border-radius:50%;background:var(--tinta2);opacity:.35;animation:gc-b 1.1s infinite}",
    ".gc-typing i:nth-child(2){animation-delay:.18s}.gc-typing i:nth-child(3){animation-delay:.36s}",
    "@keyframes gc-b{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}",
    ".gc-form{display:flex;gap:8px;padding:10px;border-top:1px solid var(--linea);background:#fff}",
    ".gc-input{flex:1;font:inherit;font-size:15px;border:1px solid var(--linea);border-radius:10px;padding:10px 12px;color:var(--tinta);min-width:0}",
    ".gc-input:focus{outline:2px solid var(--tinta2);border-color:transparent}",
    ".gc-send{font:inherit;font-weight:600;font-size:14.5px;background:var(--senal);color:var(--tinta);border:2px solid var(--tinta);border-radius:10px;padding:0 16px;cursor:pointer}",
    ".gc-send:disabled{opacity:.5;cursor:not-allowed}",
    "@media (max-width:480px){.gc-panel{right:0;bottom:0;width:100vw;max-width:100vw;height:100vh;max-height:100vh;border-radius:0}}",
    "@media (prefers-reduced-motion:reduce){.gc-typing i{animation:none;opacity:.6}}"
  ].join("\n");

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  /* ---------- Sesión: el bot recuerda la conversación mientras no cierres la pestaña ---------- */
  function nuevoId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "s" + Date.now() + Math.random().toString(36).slice(2, 12);
  }
  var SESSION_ID = null;
  try { SESSION_ID = sessionStorage.getItem("gectam_session"); } catch (e) {}
  if (!SESSION_ID) {
    SESSION_ID = nuevoId();
    try { sessionStorage.setItem("gectam_session", SESSION_ID); } catch (e) {}
  }

  /* ---------- Construcción del HTML ---------- */
  var root = document.createElement("div");
  root.className = "gc-root";
  root.innerHTML =
    '<button class="gc-fab" type="button" aria-label="Abrir chat de cotizaciones">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg>' +
      '<span>Cotizar en el chat</span></button>' +
    '<section class="gc-panel" role="dialog" aria-label="Chat de cotizaciones GECTAM">' +
      '<header class="gc-head"><div><div class="gc-title">Asistente de GECTAM</div>' +
      '<div class="gc-sub">Te ayudo a cotizar tu servicio</div></div>' +
      '<button class="gc-close" type="button" aria-label="Cerrar chat">&times;</button></header>' +
      '<div class="gc-msgs" aria-live="polite"></div>' +
      '<form class="gc-form" autocomplete="off">' +
        '<input class="gc-input" type="text" maxlength="1000" placeholder="Escribe tu mensaje" aria-label="Tu mensaje">' +
        '<button class="gc-send" type="submit">Enviar</button></form>' +
    '</section>';
  document.body.appendChild(root);

  var fab = root.querySelector(".gc-fab");
  var panel = root.querySelector(".gc-panel");
  var closeBtn = root.querySelector(".gc-close");
  var msgs = root.querySelector(".gc-msgs");
  var form = root.querySelector(".gc-form");
  var input = root.querySelector(".gc-input");
  var sendBtn = root.querySelector(".gc-send");
  var chipsEl = null;
  var started = false;
  var busy = false;

  function scrollDown() { msgs.scrollTop = msgs.scrollHeight; }

  function addMsg(text, who) {
    var d = document.createElement("div");
    d.className = "gc-msg " + (who === "user" ? "gc-user" : "gc-bot");
    // Convierte **negritas** en <strong> sin usar innerHTML (seguro contra HTML inyectado)
    String(text).split(/\*\*(.+?)\*\*/g).forEach(function (parte, i) {
      if (!parte) return;
      if (i % 2 === 1) {
        var s = document.createElement("strong");
        s.textContent = parte;
        d.appendChild(s);
      } else {
        d.appendChild(document.createTextNode(parte));
      }
    });
    msgs.appendChild(d);
    scrollDown();
    return d;
  }

  function showTyping() {
    var t = document.createElement("div");
    t.className = "gc-msg gc-bot gc-typing";
    t.innerHTML = "<i></i><i></i><i></i>";
    t.setAttribute("aria-label", "El asistente está escribiendo");
    msgs.appendChild(t);
    scrollDown();
    return t;
  }

  function open() {
    panel.classList.add("gc-open");
    fab.style.display = "none";
    if (!started) {
      started = true;
      addMsg("¡Hola! Soy el asistente de GECTAM. Cuéntame qué servicio necesitas y te preparo una cotización.", "bot");
      chipsEl = document.createElement("div");
      chipsEl.className = "gc-chips";
      ["¿Qué servicios ofrecen?", "Quiero cotizar un servicio", "Necesito algo especial"].forEach(function (txt) {
        var b = document.createElement("button");
        b.type = "button"; b.className = "gc-chip"; b.textContent = txt;
        b.addEventListener("click", function () { enviar(txt); });
        chipsEl.appendChild(b);
      });
      msgs.appendChild(chipsEl);
    }
    setTimeout(function () { input.focus(); }, 50);
  }

  function close() {
    panel.classList.remove("gc-open");
    fab.style.display = "";
    fab.focus();
  }

  async function enviar(texto) {
    texto = (texto || "").trim();
    if (!texto || busy) return;
    busy = true; sendBtn.disabled = true;
    if (chipsEl) { chipsEl.remove(); chipsEl = null; }
    addMsg(texto, "user");
    input.value = "";

    var typing = showTyping();
    // Render gratis "duerme" al no usarse: la primera respuesta puede tardar.
    var nota = null;
    var timerNota = setTimeout(function () {
      nota = document.createElement("div");
      nota.className = "gc-note";
      nota.textContent = "Estoy despertando el servidor, la primera respuesta puede tardar hasta un minuto.";
      msgs.appendChild(nota); scrollDown();
    }, 7000);

    var ctrl = new AbortController();
    var timeout = setTimeout(function () { ctrl.abort(); }, 90000);

    try {
      var res = await fetch(BACKEND + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: texto, session_id: SESSION_ID }),
        signal: ctrl.signal
      });
      if (!res.ok) throw new Error("http " + res.status);
      var data = await res.json();
      typing.remove();
      addMsg(data.reply, "bot");
    } catch (err) {
      typing.remove();
      addMsg("No pude responder en este momento. Intenta de nuevo en unos minutos o contáctanos directamente.", "bot");
      if (window.console) console.error(err);
    } finally {
      clearTimeout(timerNota); clearTimeout(timeout);
      if (nota) nota.remove();
      busy = false; sendBtn.disabled = false;
      input.focus();
    }
  }

  fab.addEventListener("click", open);
  closeBtn.addEventListener("click", close);
  form.addEventListener("submit", function (e) { e.preventDefault(); enviar(input.value); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && panel.classList.contains("gc-open")) close();
  });

  // Para abrir el chat desde botones de la página: <button data-open-chat>
  document.addEventListener("click", function (e) {
    var el = e.target.closest && e.target.closest("[data-open-chat]");
    if (el) { e.preventDefault(); open(); }
  });

  window.GectamChat = { open: open, close: close };
})();
