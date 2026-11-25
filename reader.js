/* Reader: loads data/book.json (table of contents), then each section's
   pages on demand (data/<id>.json). Page 0 is the title page. */

const $ = (s, el = document) => el.querySelector(s);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const body = document.body;
try { history.scrollRestoration = "manual"; } catch (e) {}   // we restore the exact spot ourselves

/* storage that never throws (Safari private mode, blocked cookies...) */
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};
const PDF_URL = "assets/Nhan-Thoai-Nguyen-Hong-Phuc.pdf";
const DL_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11M7 11l5 5 5-5M5 20h14"/></svg>';

/* ---------- remember where each reader stopped (kept only in their own browser) ---------- */
function getResume() {
  try {
    const r = JSON.parse(store.get("resume") || "null");
    if (r && r.pg >= 1) return { pg: r.pg | 0, y: Math.min(1, Math.max(0, +r.y || 0)) };
  } catch (e) {}
  const old = +store.get("pg");                        // older versions only stored the page number
  return old >= 1 ? { pg: old, y: 0 } : null;
}
function scrollFraction() {
  const h = document.documentElement, max = h.scrollHeight - h.clientHeight;
  return max > 0 ? Math.min(1, Math.max(0, h.scrollTop / max)) : 0;
}
function saveResume() {
  if (current < 1 || !PAGES.length) return;           // the title page is not "a place in the book"
  store.set("resume", JSON.stringify({ pg: current, y: +scrollFraction().toFixed(4), t: Date.now() }));
  store.set("pg", current);
}
function jumpTo(y) {                                    // instant scroll, even though the site uses smooth scrolling
  const h = document.documentElement, prev = h.style.scrollBehavior;
  h.style.scrollBehavior = "auto"; window.scrollTo(0, y); h.style.scrollBehavior = prev;
}

let BOOK, PAGES = [], ENTRY_PAGE = {}, current = 0;
const cache = {};   // section id -> pages

const sectionTitle = (s) => s.id === "open" ? "Mở đầu" : s.id === "end" ? "Cuối sách" : "Phần " + s.label;
const entryRange = (e) => !e ? "" : e[0] === e[1] ? `Mục ${e[0]}` : `Mục ${e[0]}–${e[1]}`;

async function loadSection(id) {
  if (!cache[id]) cache[id] = fetch(`data/${id}.json`).then((r) => r.json()).then((d) => d.pages);
  return cache[id];
}

/* ---------- build global page list + TOC ---------- */
function init() {
  PAGES.push({ cover: true });
  BOOK.sections.forEach((s) => s.pages.forEach((m, i) => {
    const idx = PAGES.length;
    PAGES.push({ sec: s, i, meta: m });
    if (m.entries) for (let n = m.entries[0]; n <= m.entries[1]; n++) ENTRY_PAGE[n] = idx;
  }));

  const list = $("#tocList");
  const cover = el("button", "toc-sec toc-cover");
  cover.dataset.idx = 0;
  cover.innerHTML = `<span class="thumb-ph">Bìa</span><span><b>Trang bìa</b><small>Nhàn Thoại</small></span>`;
  cover.onclick = () => go(0);
  list.appendChild(cover);
  BOOK.sections.forEach((s) => {
    const det = el("details", "toc-sec");
    const first = PAGES.findIndex((p) => p.sec === s);
    const thumb = `<span class="thumb-ph">${s.label.length < 5 ? s.label : "✦"}</span>`;
    det.innerHTML = `<summary>${thumb}<span><b>${sectionTitle(s)}</b><small>${s.entries ? entryRange(s.entries) + " · " : ""}${s.pages.length} trang</small></span></summary>`;
    s.pages.forEach((m, i) => {
      const idx = first + i;
      if (m.heads && m.heads.length) {
        m.heads.forEach(([n, t]) => det.appendChild(tocLink(idx, t, "", n)));
      } else if (!m.cont) {
        det.appendChild(tocLink(idx, `Trang ${idx}`, m.preview));
      }
    });
    det.dataset.first = first; det.dataset.last = first + s.pages.length - 1;
    list.appendChild(det);
  });
}

function tocLink(idx, title, preview, num) {
  const b = el("button", "toc-link");
  b.dataset.idx = idx;
  b.innerHTML = `${num ? `<span class="no">${num}</span>` : ""}<span class="tx"><span class="t">${esc(title)}</span>${preview ? `<span class="pv">${esc(preview)}</span>` : ""}</span>`;
  b.onclick = () => go(idx);
  return b;
}

/* ---------- rendering ---------- */
function renderBlock(b) {
  switch (b.t) {
    case "n": return `<h2 class="entry-no" id="e${b.x}"><span>${b.x}</span></h2>`;
    case "q": return `<blockquote class="bq"><p>${esc(b.x)}</p>${b.s ? `<cite>${esc(b.s)}</cite>` : ""}</blockquote>`;
    case "l": return `<p class="ln">${esc(b.x)}</p>`;
    default:  return `<p>${esc(b.x)}</p>`;
  }
}

function renderCover() {
  const c = BOOK.cover, T = BOOK.totals, rs = getResume();
  return `
    <div class="title-page">
      <div class="portrait photo"><img src="${c.photo}" alt="${esc(c.author)}"></div>
      <p class="eyebrow">${esc(c.credits[0])}</p>
      <h1>${esc(c.title)}</h1>
      <p class="subtitle">${esc(c.subtitle)}</p>
      <p class="tagline">${esc(c.tagline)}</p>
      <p class="byline">${esc(c.author)} <em>(${esc(c.nick)})</em></p>
      <p class="dates">${esc(c.dates)}</p>
      <div class="ornament"></div>
      <p class="credits">${esc(c.credits[1])} · ${esc(c.credits[2])}</p>
      <blockquote class="epi">${esc(c.epigraph)}<cite>${esc(c.epigraphSrc)}</cite></blockquote>
      <p class="facts">${T.entries} mục · ${BOOK.sections.length - 2} phần · khoảng ${Math.round(T.words / 1000)}.000 từ · ${T.pages} trang đọc</p>
      <div class="actions">
        ${rs ? `<button class="btn btn-primary" id="startBtn">Tiếp tục đọc · trang ${rs.pg}</button><button class="btn btn-ghost" id="fromStart">Đọc từ đầu</button>`
             : `<button class="btn btn-primary" id="startBtn">Đọc sách</button>`}
        <a class="btn btn-ghost" href="${PDF_URL}" download="Nhan-Thoai-Nguyen-Hong-Phuc.pdf">${DL_ICON}Tải PDF</a>
      </div>
    </div>`;
}

async function render() {
  const pg = PAGES[current], art = $("#page");
  let html;
  if (pg.cover) {
    html = renderCover();
  } else {
    const blocks = (await loadSection(pg.sec.id))[pg.i];
    const s = pg.sec;
    html = "";
    if (pg.i === 0) {
      const imgs = s.images.map((im) => `<figure class="interlude"><img src="${im.src}" alt="" loading="lazy">${im.cap ? `<figcaption>${esc(im.cap)}</figcaption>` : ""}</figure>`).join("");
      html += `<header class="section-open"><p class="eyebrow">${s.id === "open" || s.id === "end" ? "" : "Phần"}</p><h1>${s.id === "open" ? "Mở đầu" : s.id === "end" ? "Cuối sách" : s.label}</h1><div class="ornament"></div>${imgs}</header>`;
    } else {
      html += `<p class="running">${sectionTitle(s)}${pg.meta.cont ? ` · Mục ${pg.meta.cont} (tiếp)` : ""}</p>`;
    }
    html += `<div class="prose">${blocks.map(renderBlock).join("")}</div>`;
  }
  art.innerHTML = html;
  const rs = getResume();
  $("#startBtn")?.addEventListener("click", () => rs ? go(rs.pg, null, rs.y) : go(1));
  $("#fromStart")?.addEventListener("click", () => go(1));
  $("#prev").disabled = current === 0;
  $("#next").disabled = current === PAGES.length - 1;
  $("#pos").textContent = current === 0 ? "" : `Trang ${current} / ${PAGES.length - 1}`;
  syncToc();
  try { history.replaceState(null, "", "#p" + current); } catch (e) {}
}

function syncToc() {
  $(".toc-cover")?.classList.toggle("on", current === 0);
  document.querySelectorAll(".toc-link").forEach((b) => b.classList.toggle("on", +b.dataset.idx === current));
  document.querySelectorAll(".toc-sec").forEach((d) => { d.open = current >= +d.dataset.first && current <= +d.dataset.last; });
  $(".toc-link.on")?.scrollIntoView({ block: "nearest" });
}

function go(idx, anchor, frac) {
  current = Math.max(0, Math.min(PAGES.length - 1, idx));
  return render().then(() => {
    if (anchor) document.getElementById(anchor)?.scrollIntoView({ block: "start" });
    else if (frac > 0) { const h = document.documentElement; jumpTo(frac * Math.max(0, h.scrollHeight - h.clientHeight)); }
    else jumpTo(0);
    $("#toc").classList.remove("open");
    saveResume();
  });
}

/* ---------- controls ---------- */
$("#prev").onclick = () => go(current - 1);
$("#next").onclick = () => go(current + 1);
$("#menuBtn").onclick = () => $("#toc").classList.toggle("open");
$("#closeToc").onclick = () => $("#toc").classList.remove("open");
$("#jump").onsubmit = (e) => {
  e.preventDefault();
  const n = +$("#jumpN").value;
  if (ENTRY_PAGE[n]) go(ENTRY_PAGE[n], "e" + n);
};
document.addEventListener("keydown", (e) => {
  if (e.target.matches("input,textarea")) return;
  if (e.key === "ArrowRight") go(current + 1);
  if (e.key === "ArrowLeft") go(current - 1);
  if (e.key === "/") { e.preventDefault(); openSearch(); }
});

let size = Number(store.get("size") || 1.2);
function applySize() { size = Math.min(1.7, Math.max(1.0, size)); body.style.setProperty("--r-size", size + "rem"); store.set("size", size); }
$("#bigger").onclick = () => { size += 0.1; applySize(); };
$("#smaller").onclick = () => { size -= 0.1; applySize(); };
$("#bigger2").onclick = () => { size += 0.1; applySize(); };
$("#smaller2").onclick = () => { size -= 0.1; applySize(); };

function applyTheme(t) {
  body.dataset.theme = t;
  document.querySelectorAll(".swatch").forEach((s) => s.setAttribute("aria-pressed", s.dataset.t === t));
  store.set("theme", t);
}
document.querySelectorAll(".swatch").forEach((s) => (s.onclick = () => applyTheme(s.dataset.t)));

window.addEventListener("scroll", () => {
  const h = document.documentElement;
  const within = h.scrollTop / (h.scrollHeight - h.clientHeight || 1);
  $("#progress").style.width = (((current - 1 + within) / (PAGES.length - 1)) * 100).toFixed(2) + "%";
  clearTimeout(saveTimer); saveTimer = setTimeout(saveResume, 350);
});
let saveTimer;
window.addEventListener("pagehide", saveResume);
document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") saveResume(); });

/* ---------- search (accent-insensitive, whole book) ---------- */
const fold = (s) => s.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
let INDEX = null;
async function buildIndex() {
  if (INDEX) return INDEX;
  INDEX = [];
  let g = 1;
  for (const s of BOOK.sections) {
    const pages = await loadSection(s.id);
    pages.forEach((blocks, i) => {
      let entry = s.pages[i].cont || null;
      blocks.forEach((b) => {
        if (b.t === "n") entry = +b.x;
        else if (b.x.length > 2) INDEX.push({ g: g + 0, entry, text: b.x, f: fold(b.x) });
      });
      g++;
    });
  }
  return INDEX;
}
async function openSearch() {
  $("#search").hidden = false; $("#q").focus();
  $("#searchMeta").textContent = "Đang tải quyển sách…";
  await buildIndex();
  $("#searchMeta").textContent = "Gõ ít nhất 2 chữ cái.";
}
function closeSearch() { $("#search").hidden = true; }
$("#searchBtn").onclick = openSearch;
$("#closeSearch").onclick = closeSearch;
$("#search").addEventListener("click", (e) => { if (e.target.id === "search") closeSearch(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSearch(); });

let timer;
$("#q").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(runSearch, 200); });
async function runSearch() {
  const q = fold($("#q").value.trim());
  const out = $("#results"); out.innerHTML = "";
  if (q.length < 2) { $("#searchMeta").textContent = "Gõ ít nhất 2 chữ cái."; return; }
  const idx = await buildIndex();
  let n = 0, shown = 0;
  for (const r of idx) {
    const at = r.f.indexOf(q);
    if (at < 0) continue;
    n++;
    if (shown >= 40) continue;
    shown++;
    const a = Math.max(0, at - 50), b = Math.min(r.text.length, at + q.length + 90);
    const li = el("li", "", `<span class="loc">${r.entry ? "Mục " + r.entry : "Trang " + r.g}</span> …${esc(r.text.slice(a, at))}<mark>${esc(r.text.slice(at, at + q.length))}</mark>${esc(r.text.slice(at + q.length, b))}…`);
    li.onclick = () => { closeSearch(); go(r.g); };
    out.appendChild(li);
  }
  $("#searchMeta").textContent = n ? `Tìm thấy ${n} đoạn${n > shown ? ` — hiển thị ${shown} đoạn đầu` : ""}` : "Không tìm thấy.";
}

/* ---------- boot ---------- */
(async function () {
  applyTheme(store.get("theme") || "light");
  applySize();
  BOOK = await (await fetch("data/book.json")).json();
  init();
  const h = location.hash.match(/^#p(\d+)$/);
  const q = new URLSearchParams(location.search).get("q");
  const rs = getResume();
  if (location.hash === "#random") await go(1 + Math.floor(Math.random() * (PAGES.length - 1)));   // "open any page"
  else if (h) {
    const n = +h[1];
    await go(n, null, rs && rs.pg === n ? rs.y : 0);          // same page as last time -> also the same spot on it
    if (rs && rs.pg === n && (n > 1 || rs.y > 0.03)) welcomeBack(rs);
  } else if (q) await go(0);
  else if (rs && rs.pg < PAGES.length) { await go(rs.pg, null, rs.y); welcomeBack(rs); }
  else await go(0);
  if (q) { await openSearch(); $("#q").value = q; runSearch(); }                                  // ?q=Nietzsche
})();

/* ---------- "welcome back" note ---------- */
let toastTimer;
function welcomeBack(rs) {
  const t = $("#toast");
  $("#toastTx").innerHTML = `<b>Chào mừng bạn trở lại 👋</b><small>Đã mở đúng chỗ bạn đang đọc · trang ${rs.pg} / ${PAGES.length - 1}</small>`;
  t.classList.add("show");
  const hide = () => t.classList.remove("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(hide, 8000);
  $("#toastBtn").onclick = () => { hide(); go(1); };
}
