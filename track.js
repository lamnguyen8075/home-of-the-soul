/* Đếm lượt xem trang. Chỉ gửi khi stats-config.js có địa chỉ API; tôn trọng "Do Not Track". */
(function () {
  var C = window.NT_STATS || {};
  if (!C.api) return;
  try {
    if (navigator.doNotTrack === "1" || window.doNotTrack === "1") return;
    if (localStorage.getItem("nt_owner")) return;                       // máy của chủ trang (đã mở trang thống kê)
    if (/^(localhost|127\.|\[::1\])/.test(location.hostname) && !/[?&]track=1/.test(location.search)) return;
    var rnd = function () { return Math.random().toString(36).slice(2, 10) + Date.now().toString(36); };
    var vid = localStorage.getItem("nt_vid");
    if (!vid) { vid = rnd(); localStorage.setItem("nt_vid", vid); }
    var sid = sessionStorage.getItem("nt_sid");
    if (!sid) { sid = rnd(); sessionStorage.setItem("nt_sid", sid); }
    var ref = "";
    try { ref = document.referrer ? new URL(document.referrer).hostname : ""; } catch (e) {}
    if (ref === location.hostname) ref = "";
    var body = JSON.stringify({
      t: Date.now(), path: location.pathname, ref: ref, vid: vid, sid: sid,
      lang: navigator.language || "", tz: (Intl.DateTimeFormat().resolvedOptions().timeZone || ""), w: screen.width || 0
    });
    var url = C.api.replace(/\/$/, "") + "/collect";
    if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], { type: "text/plain" }))) return;
    fetch(url, { method: "POST", body: body, headers: { "Content-Type": "text/plain" }, keepalive: true, mode: "cors" }).catch(function () {});
  } catch (e) {}
})();
