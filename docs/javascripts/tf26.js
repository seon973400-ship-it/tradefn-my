/* tf26.js — 과정 사이트 동작 (의존성 없음 · Material 즉시 이동(navigation.instant)과 함께 동작)
   쪽을 열 때마다(즉시 이동 포함) init()이 다시 돈다. 매번 지난 쪽이 남긴 것(추적기 · 아래 막대 · 타이머)을 먼저 지운다.
   1) 오늘        : 서울 날짜로 [data-tf-day] 카드 · [data-tf-today] 단추 · [data-tf-now] 한 줄 · [data-tf-daystate] 칩 · 시간표 '지금' · 탭 '오늘'
   2) 단계 카드   : .step 제목 아래를 카드(section.tf-step)로 감싸고 번호 · 시각 칩 · 도구 칩 · '이 단계 완료' 단추
   3) 진행 추적   : 오른쪽 사이드바(넓은 화면) · 아래 막대(좁은 화면) · 지금 권장 단계 · 다음 점검 시각
   4) 체크박스    : 모든 - [ ] 항목을 이 브라우저(localStorage)에 저장, 단계 '확인'을 다 채우면 그 단계 완료
   5) 열기 시각   : 내려받기 카드의 data-tf-open · data-tf-release(생성기) · data-open-at(UTC ISO) — 그 시각 전까지 잠금 칩 'HH:MM 공개', 지나면 보통 링크(새로 빌드 필요 없음)
   6) 그 밖       : 그림 확대 · 4열 이상 표 → 모바일 줄 카드 · 프롬프트 {빈칸} 강조 · 제목 카드(.tf-card) · 체크리스트 진행 · 용어 거르기 · 인쇄 때 접힌 상자 펼치기
   점검용 주소: 아무 쪽에나 ?tf-date=2026-10-15T08:40 (서울 시각) — 이 탭에서만 기억, ?tf-date=clear 로 지움. */
(function () {
  "use strict";

  /* 과정 날짜(서울) — 이 표만 고치면 모든 쪽의 '오늘'이 따라온다 */
  var DAYS = { 1: "2026-10-14", 2: "2026-10-15", 3: "2026-10-16", 4: "2026-10-19", 5: "2026-10-20", 6: "2026-10-21" };
  var DOW = ["일", "월", "화", "수", "목", "금", "토"];
  var DAY_START = "09:00", DAY_END = "18:00";
  var KEY = "tf26:v1:";
  var CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳";

  /* ---------- 공통 ---------- */
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function toMin(hm) { var p = String(hm).split(":"); return (+p[0]) * 60 + (+p[1]); }
  function hash(s) { var h = 5381; for (var i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) | 0; return (h >>> 0).toString(36); }
  function norm(s) { return String(s || "").replace(/\s+/g, " ").trim(); }

  function store(kind) { try { return window[kind]; } catch (e) { return null; } }
  function lsGet(k) { var s = store("localStorage"); try { return s ? s.getItem(k) : null; } catch (e) { return null; } }
  function lsSet(k, v) { var s = store("localStorage"); try { if (s) s.setItem(k, v); } catch (e) { /* 저장을 못 해도 화면은 동작 */ } }
  function ssGet(k) { var s = store("sessionStorage"); try { return s ? s.getItem(k) : null; } catch (e) { return null; } }
  function ssSet(k, v) { var s = store("sessionStorage"); try { if (!s) return; if (v == null) s.removeItem(k); else s.setItem(k, v); } catch (e) { /* 무시 */ } }

  /* 지금(서울) — {date:"2026-10-15", hm:"08:40", ms:UTC 밀리초, fake:점검용인가} */
  function now() {
    var m = location.search.match(/[?&]tf-date=([^&#]*)/), q = m ? decodeURIComponent(m[1]) : null;
    if (q === "clear" || q === "") { ssSet(KEY + "date", null); q = null; }
    else if (q) ssSet(KEY + "date", q);
    else q = ssGet(KEY + "date");
    var f = q && q.match(/^(\d{4}-\d{2}-\d{2})(?:[T ](\d{1,2}:\d{2}))?$/);
    if (f) {
      var hm = f[2] ? (f[2].length === 4 ? "0" + f[2] : f[2]) : DAY_START;
      return { date: f[1], hm: hm, ms: Date.parse(f[1] + "T" + hm + ":00+09:00"), fake: true };
    }
    var t = Date.now(), k = new Date(t + 9 * 3600 * 1000);   /* 서울은 일광절약시간이 없어 +9시간이면 된다 */
    return { date: k.getUTCFullYear() + "-" + pad(k.getUTCMonth() + 1) + "-" + pad(k.getUTCDate()), hm: pad(k.getUTCHours()) + ":" + pad(k.getUTCMinutes()), ms: t, fake: false };
  }
  function kstParts(ms) { var k = new Date(ms + 9 * 3600 * 1000); return { date: k.getUTCFullYear() + "-" + pad(k.getUTCMonth() + 1) + "-" + pad(k.getUTCDate()), md: (k.getUTCMonth() + 1) + "/" + k.getUTCDate(), hm: pad(k.getUTCHours()) + ":" + pad(k.getUTCMinutes()), dow: DOW[k.getUTCDay()] }; }
  function md(date) { var p = date.split("-"); return (+p[1]) + "/" + (+p[2]); }
  function dow(date) { return DOW[new Date(date + "T00:00:00Z").getUTCDay()]; }
  function daysBetween(a, b) { return Math.round((Date.parse(b + "T00:00:00Z") - Date.parse(a + "T00:00:00Z")) / 86400000); }

  /* 오늘이 과정의 어디인가 */
  function courseState(t) {
    var s = { today: 0, next: 0, prev: 0, phase: "" };
    Object.keys(DAYS).forEach(function (n) {
      n = +n;
      if (DAYS[n] === t.date) s.today = n;
      if (DAYS[n] > t.date && !s.next) s.next = n;
      if (DAYS[n] < t.date) s.prev = n;
    });
    s.phase = s.today ? "day" : (t.date < DAYS[1] ? "before" : (s.next ? "gap" : "after"));
    return s;
  }

  function pageKey() { return location.pathname.replace(/index\.html$/, "").replace(/\/+$/, "/") || "/"; }
  function dayOfPage() { var m = location.pathname.match(/\/day(\d)\//); return m ? +m[1] : 0; }
  function load() { try { var o = JSON.parse(lsGet(KEY + pageKey()) || "{}"); o.steps = o.steps || {}; o.checks = o.checks || {}; return o; } catch (e) { return { steps: {}, checks: {} }; } }
  function save(state) { lsSet(KEY + pageKey(), JSON.stringify(state)); }

  /* 지난 쪽에서 건 타이머 · 감시를 쪽이 바뀔 때 모두 끊는다 */
  var cleanups = [];
  function onCleanup(fn) { cleanups.push(fn); }
  function cleanup() { cleanups.splice(0).forEach(function (fn) { try { fn(); } catch (e) { /* 무시 */ } }); }

  /* ---------- 1) 오늘 ---------- */
  function today(content) {
    var t = now(), s = courseState(t);
    document.documentElement.setAttribute("data-tf-phase", s.phase);

    /* 일차 카드 : 오늘 · 지난 수업 · 다음 수업 */
    $$("[data-tf-day]", content).forEach(function (mark) {
      var n = +mark.getAttribute("data-tf-day"); var card = mark.closest("li") || mark.closest(".tf-hero") || mark;
      card.classList.toggle("is-today", n === s.today);
      card.classList.toggle("is-past", !!DAYS[n] && DAYS[n] < t.date);
      card.classList.toggle("is-next", !s.today && n === s.next);
    });

    /* '오늘 열기' 단추 : href의 dayN/ 부분만 바꾼다(쪽 깊이와 상관없이 동작) */
    $$("a[data-tf-today]", content).forEach(function (a) {
      if (!a.hasAttribute("data-tf-href")) a.setAttribute("data-tf-href", a.getAttribute("href") || "");
      if (!a.hasAttribute("data-tf-text")) a.setAttribute("data-tf-text", (a.querySelector(".tf-today-label") || a).textContent);
      var base = a.getAttribute("data-tf-href"), label = a.querySelector(".tf-today-label") || a, n = 0, text = a.getAttribute("data-tf-text");
      if (s.phase === "day") { n = s.today; text = "오늘 · " + n + "일차 열기"; }
      else if (s.phase === "before") { n = 1; text = "1일차 미리 보기 · " + md(DAYS[1]) + "(" + dow(DAYS[1]) + ")"; }
      else if (s.phase === "gap") { n = s.next; text = "다음 수업 · " + n + "일차 " + md(DAYS[n]) + "(" + dow(DAYS[n]) + ")"; }
      if (n) a.setAttribute("href", base.replace(/day\d\//, "day" + n + "/"));
      else a.setAttribute("href", base);
      label.textContent = text;
    });

    /* 지금 한 줄 */
    $$("[data-tf-now]", content).forEach(function (p) {
      var msg = "";
      var nowTxt = md(t.date) + "(" + dow(t.date) + ") " + t.hm;
      if (s.phase === "before") {
        var dd = daysBetween(t.date, DAYS[1]);
        msg = "개강까지 " + dd + "일 · " + md(DAYS[1]) + "(" + dow(DAYS[1]) + ") " + DAY_START + " 시작";
      } else if (s.phase === "day") {
        var m = toMin(t.hm);
        if (m < toMin(DAY_START)) msg = "오늘은 " + s.today + "일차 · " + DAY_START + " 시작 — 지금 " + t.hm;
        else if (m < toMin(DAY_END)) msg = "지금 " + s.today + "일차 수업 중 · " + nowTxt;
        else msg = s.today + "일차 끝 · " + (s.today < 6 ? "다음 수업 " + (s.today + 1) + "일차 " + md(DAYS[s.today + 1]) + "(" + dow(DAYS[s.today + 1]) + ")" : "6일 과정을 마쳤습니다");
      } else if (s.phase === "gap") {
        msg = "다음 수업 " + s.next + "일차 · " + md(DAYS[s.next]) + "(" + dow(DAYS[s.next]) + ") " + DAY_START;
      } else {
        msg = "과정이 끝났습니다 — 자료는 계속 열려 있습니다";
      }
      p.textContent = msg + (t.fake ? " · 점검용 시각" : "");
    });

    /* 일차 상태 칩 */
    $$("[data-tf-daystate]", content).forEach(function (c) {
      var n = +c.getAttribute("data-tf-daystate"), txt = "";
      c.classList.remove("is-today");
      if (!DAYS[n]) return;
      if (n === s.today) { txt = "오늘"; c.classList.add("is-today"); }
      else if (DAYS[n] < t.date) txt = "지난 수업 · 다시 보기";
      else { var d = daysBetween(t.date, DAYS[n]); txt = d === 1 ? "내일" : "D-" + d; }
      c.textContent = txt;
    });

    /* 시간표 : 그날 쪽이면(또는 data-tf-days="1-5"처럼 정한 수업일이면) 지금 칸 */
    var pd = dayOfPage();
    $$(".tf-timeline > ol > li", content).forEach(function (li) {
      li.classList.remove("is-now", "is-past");
      var tl = li.closest(".tf-timeline"), range = tl && tl.getAttribute("data-tf-days"), active;
      if (range) { var rg = range.split("-"); active = s.today >= +rg[0] && s.today <= +(rg[1] || rg[0]); }
      else active = !!pd && pd === s.today;
      if (!active) return;
      var tm = li.querySelector("time"); if (!tm) return;
      var r = tm.textContent.match(/(\d{1,2}:\d{2})\s*[–~\-—]\s*(\d{1,2}:\d{2})/); if (!r) return;
      var m = toMin(t.hm);
      if (m >= toMin(r[2])) li.classList.add("is-past");
      else if (m >= toMin(r[1])) li.classList.add("is-now");
    });

    /* 위쪽 탭 : 오늘 일차 탭에 '오늘' */
    $$(".md-tabs__item").forEach(function (it) {
      var a = it.querySelector("a"); var on = false;
      if (a && s.today) on = new RegExp("(^|/)day" + s.today + "/").test(a.getAttribute("href") || "");
      it.classList.toggle("tf-tab-today", on);
    });
  }

  /* ---------- 2) 단계 카드 ---------- */
  /* 단계 번호(인쇄된 실습 장 그대로) — 맨 앞에서 찾는다
     "A-1 · 01" · "A-2 ③" · "Step 3" · "①" · "B1" · "B1b" · "3-1" · "1." */
  var NUM_PATTERNS = [
    { re: /^\s*([A-Z]-\d{1,2})\s*[·.]?\s*(\d{1,2}|[①-⑳])(?=[\s·.)—–:-]|$)\s*[·.):]?\s*/, make: function (m) { return { badge: num(m[2]), phase: m[1], label: m[1] + "·" + num(m[2]) }; } },
    { re: /^\s*(?:Step|STEP|스텝)\s*(\d{1,2})(?=[\s·.)—–:-]|$)\s*[·.):]?\s*/, make: function (m) { return { badge: m[1], step: true, label: "Step " + m[1] }; } },
    { re: /^\s*([①-⑳])\s*[·.):]?\s*/, make: function (m) { return { badge: num(m[1]), label: m[1] }; } },
    { re: /^\s*([A-Z]{1,2}\d{1,2}[a-z]?)(?=[\s·.)—–:-]|$)\s*[·.):]?\s*/, make: function (m) { return { badge: m[1], label: m[1] }; } },
    { re: /^\s*(\d{1,2}-\d{1,2})(?=[\s·.)—–:-]|$)\s*[·.):]?\s*/, make: function (m) { return { badge: m[1], label: m[1] }; } },
    { re: /^\s*(\d{1,2})[.)]\s+/, make: function (m) { return { badge: m[1], label: m[1] }; } }
  ];
  function num(s) { var i = CIRCLED.indexOf(s); return i >= 0 ? String(i + 1) : s; }
  /* 진행 목록의 작은 원에는 두 글자까지만 — '0-1' → '1', 'B-1·01' → '01', 'B12' → 'B12'는 '12' */
  function dotText(s) { s = String(s || ""); return s.length <= 2 ? s : s.replace(/^.*[-·.]/, "").replace(/^[A-Za-z]+/, "").slice(-2) || s.slice(-2); }
  var TIME_RE = /\s*[(（]\s*(\d{1,2}:\d{2})\s*[–~\-—]\s*(\d{1,2}:\d{2})\s*(?:[·,]\s*([^()（）]{1,24}?))?\s*[)）]\s*$/;
  function level(n) { var m = /^H([1-6])$/.exec(n.tagName || ""); return m ? +m[1] : 9; }

  /* 제목 글자의 맨 앞(번호) · 맨 끝(시각)만 떼어 내고 나머지 글자 모양(코드 · 굵게)은 그대로 둔다 */
  function firstText(node) { var w = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, null), n; while ((n = w.nextNode())) { if (n.nodeValue.trim()) return n; } return null; }
  function lastText(node) { var w = document.createTreeWalker(node, NodeFilter.SHOW_TEXT, null), n, last = null; while ((n = w.nextNode())) { if (n.nodeValue.trim()) last = n; } return last; }

  function wrapSection(h, cls, stopAtPhase) {
    var lv = level(h);
    var sec = el("section", cls);
    h.parentNode.insertBefore(sec, h);
    var n = h, nodes = [];
    while (n) {
      nodes.push(n); n = n.nextElementSibling;
      if (!n || level(n) <= lv || n.tagName === "HR" || (stopAtPhase && n.classList && (n.classList.contains("tf-phase") || n.classList.contains("tf-step")))) break;
    }
    nodes.forEach(function (x) { sec.appendChild(x); });
    return sec;
  }

  function steps(content) {
    $$("h2.step, h3.step, h4.step", content).forEach(function (h) {
      if (h.closest(".tf-step")) return;
      var sec = wrapSection(h, "tf-step", true);
      sec.setAttribute("data-step", h.id || ("step-" + hash(h.textContent)));
      sec.setAttribute("data-level", level(h));
      decorate(h, sec);
    });
    return $$("section.tf-step", content);
  }

  function decorate(h, sec) {
    var link = h.querySelector("a.headerlink"); if (link) link.remove();
    var start = h.getAttribute("data-start") || "", end = h.getAttribute("data-end") || "", note = "";
    /* 끝의 (13:00–13:20) */
    var lt = lastText(h);
    if (lt && !start) {
      var tm = lt.nodeValue.match(TIME_RE);
      if (tm) { start = tm[1]; end = tm[2]; note = (tm[3] || "").trim(); lt.nodeValue = lt.nodeValue.replace(TIME_RE, ""); }
    }
    /* 맨 앞의 번호 */
    var info = null, explicit = h.getAttribute("data-num");
    var ft = firstText(h);
    if (ft) {
      for (var i = 0; i < NUM_PATTERNS.length; i++) {
        var m = ft.nodeValue.match(NUM_PATTERNS[i].re);
        if (m) { info = NUM_PATTERNS[i].make(m); if (!explicit || norm(explicit) === norm(m[0]).replace(/[·.):]$/, "")) ft.nodeValue = ft.nodeValue.slice(m[0].length); break; }
      }
    }
    if (explicit) info = { badge: explicit, label: explicit };
    /* 제목 다시 짜기 : [번호] [제목 …] [시각 칩] [도구 칩] [¶] */
    var title = el("span", "tf-step__title");
    while (h.firstChild) title.appendChild(h.firstChild);
    var badge = null;
    if (info) {
      badge = el("span", "tf-badge");
      if (info.step) { badge.classList.add("tf-badge--stack"); badge.appendChild(el("small", "", "STEP")); badge.appendChild(document.createTextNode(info.badge)); }
      else { badge.textContent = info.badge; if (String(info.badge).length > 2) badge.classList.add("tf-badge--wide"); }
      h.appendChild(badge);
    }
    h.appendChild(title);
    if (start && end) {
      var mins = toMin(end) - toMin(start);
      h.appendChild(el("span", "tf-chip tf-chip--time", start + "–" + end + (mins > 0 ? " · " + mins + "분" : "") + (note ? " · " + note : "")));
      sec.setAttribute("data-start", start); sec.setAttribute("data-end", end);
    }
    (h.getAttribute("data-tool") || "").split(/\s*[,·]\s*/).filter(Boolean).forEach(function (tool) { h.appendChild(el("span", "tf-chip tf-chip--tool", tool)); });
    if (link) h.appendChild(link);
    var label = norm(title.textContent);
    sec.setAttribute("data-label", label);
    sec.setAttribute("data-num", info ? info.badge : "");
    sec.setAttribute("data-full", info ? info.label : "");
    if (info && info.phase) sec.setAttribute("data-phase", info.phase);
    else if (h.getAttribute("data-phase")) sec.setAttribute("data-phase", h.getAttribute("data-phase"));   // 번호 꼴로 구간을 못 찾으면 제목의 data-phase(예: 실습 B · 8교시)
    var foot = el("div", "tf-step__foot");
    foot.appendChild(el("span", "", "끝났으면 눌러 두세요 — 진행 막대에 반영됩니다"));
    var btn = el("button", "tf-done", "이 단계 완료"); btn.type = "button"; btn.setAttribute("aria-pressed", "false");
    foot.appendChild(btn); sec.appendChild(foot);
  }

  /* 제목 하나를 카드로(.tf-card) — FAQ 같은 쪽 */
  function cards(content) {
    $$("h2.tf-card, h3.tf-card, h4.tf-card", content).forEach(function (h) {
      if (h.closest(".tf-qa") || h.closest(".tf-step")) return;
      wrapSection(h, "tf-qa", false);
    });
  }

  /* ---------- 3) 진행 추적 + 4) 체크박스 ---------- */
  function checkKey(cb, scope) {
    var li = cb.closest("li"); var txt = li ? norm(li.textContent).slice(0, 120) : "";
    return scope + "#" + hash(txt);
  }

  function checkboxes(content, state, onChange) {
    $$(".task-list-item input[type=checkbox]", content).forEach(function (c) {
      if (c.hasAttribute("data-tf-check")) return;
      var sec = c.closest("section.tf-step");
      var key = checkKey(c, sec ? sec.getAttribute("data-step") : "page");
      c.disabled = false; c.setAttribute("data-tf-check", key);
      if (state.checks[key]) c.checked = true;
      c.addEventListener("change", function () {
        state.checks[key] = c.checked;
        if (sec && c.checked) {
          var all = $$("input[data-tf-check]", sec);
          if (all.length && all.every(function (x) { return x.checked; })) state.steps[sec.getAttribute("data-step")] = true;
        }
        save(state); onChange();
      });
    });
  }

  function checklists(content) {
    $$(".tf-checklist", content).forEach(function (box) {
      if (box.querySelector(".tf-checklist__head")) return;
      var head = el("div", "tf-checklist__head"); head.appendChild(el("span", "", box.getAttribute("data-title") || "체크리스트")); var cnt = el("span", ""); head.appendChild(cnt);
      var bar = el("div", "tf-checklist__bar"); var fill = el("span"); bar.appendChild(fill);
      box.insertBefore(bar, box.firstChild); box.insertBefore(head, box.firstChild);
      function upd() {
        var all = $$("input[type=checkbox]", box), on = all.filter(function (x) { return x.checked; }).length;
        cnt.textContent = on + " / " + all.length + " 완료"; fill.style.width = (all.length ? Math.round(on * 100 / all.length) : 0) + "%";
      }
      box.addEventListener("change", upd); upd();
    });
  }

  function tracker(content, secs, state) {
    document.body.classList.add("tf-has-progress");
    var h1 = content.querySelector("h1"), title = h1 ? norm(h1.textContent.replace(/¶/g, "")) : "실습";
    var short = (title.match(/^(실습\s*[A-Z](?:-\d)?|해커톤|실습)/) || [title.split(/\s*[—–:·]\s*/)[0]])[0];
    if (short.length > 14) short = short.slice(0, 14) + "…";

    var h3mode = secs.some(function (s) { return +s.getAttribute("data-level") >= 3; });
    var items = [];
    $$("h2[id], h3[id], section.tf-step", content).forEach(function (n) {
      if (n.tagName !== "SECTION" && n.closest(".tf-step")) return;      /* 단계 카드 안의 제목은 목록에 넣지 않는다 */
      if (n.closest(".tf-qa") && n.tagName !== "H2") return;
      if (n.closest(".tf-lab") || n.closest(".tf-hero")) return;
      if (n.tagName === "SECTION") {
        items.push({ kind: "step", id: n.getAttribute("data-step"), label: n.getAttribute("data-label"), num: n.getAttribute("data-num") || "", full: n.getAttribute("data-full") || "", start: n.getAttribute("data-start") || "", end: n.getAttribute("data-end") || "", sec: n });
      } else if (n.tagName === "H2") {
        var lab = norm(n.textContent).replace(/¶$/, "");
        items.push({ kind: h3mode ? "phase" : "extra", id: n.id, label: lab });
      } else if (h3mode) {
        items.push({ kind: "extra", id: n.id, label: norm(n.textContent).replace(/¶$/, "") });
      }
    });
    var stepItems = items.filter(function (i) { return i.kind === "step"; });
    stepItems.forEach(function (i, k) {
      if (!i.num) i.num = String(k + 1); if (!i.full) i.full = i.num;
      /* 제목의 data-phase(예: 8교시)로 구간을 정한 단계는 이름 앞에 구간을 붙인다 — '실습 B · 02'와 '8교시 · 02'가 섞이지 않게 */
      var ph = i.sec.getAttribute("data-phase") || "";
      if (ph && ph !== short && i.full.indexOf(ph) !== 0) i.full = ph + " · " + i.full;
    });

    function build() {
      var nav = el("nav", "tf-progress"); nav.setAttribute("aria-label", "실습 진행");
      var card = el("div", "tf-progress__card"); nav.appendChild(card);
      var head = el("div", "tf-progress__head"); head.appendChild(el("span", "", short + " 진행")); head.appendChild(el("span", "tf-progress__count", "")); card.appendChild(head);
      var bar = el("div", "tf-progress__bar"); bar.appendChild(el("span")); card.appendChild(bar);
      var nw = el("p", "tf-progress__now"); nw.hidden = true; card.appendChild(nw);
      var ol = el("ol"); card.appendChild(ol);
      items.forEach(function (i) {
        var li = el("li", i.kind === "phase" ? "tf-progress__phase" : "tf-progress__item" + (i.kind === "extra" ? " is-extra" : ""));
        li.setAttribute("data-id", i.id);
        var a = el("a"); a.href = "#" + i.id;
        if (i.kind === "phase") { a.textContent = i.label; }
        else { a.appendChild(el("span", "tf-progress__dot", i.kind === "step" ? dotText(i.num) : "")); a.appendChild(el("span", "", i.label)); a.appendChild(el("time", "", i.start || "")); }
        li.appendChild(a); ol.appendChild(li);
      });
      var reset = el("button", "tf-progress__reset", "이 쪽의 완료 표시 지우기"); reset.type = "button";
      reset.addEventListener("click", function () {
        if (!window.confirm("이 쪽의 완료 표시와 체크를 모두 지울까요?")) return;
        state.steps = {}; state.checks = {}; save(state);
        $$("input[data-tf-check]", content).forEach(function (c) { c.checked = false; });
        $$(".tf-checklist", content).forEach(function (b) { b.dispatchEvent(new Event("change")); });
        render();
      });
      card.appendChild(reset);
      return nav;
    }

    /* 넓은 화면 : 오른쪽 사이드바 맨 위(원래 목차는 숨김) */
    var side = $(".md-sidebar--secondary .md-sidebar__inner");
    if (side) side.insertBefore(build(), side.firstChild);
    /* 좁은 화면 : 아래 막대 + 펼치는 목록 */
    var mini = el("div", "tf-mini");
    var mbtn = el("button", "tf-mini__bar"); mbtn.type = "button"; mbtn.setAttribute("aria-expanded", "false");
    mbtn.appendChild(el("span", "tf-mini__label", short)); mbtn.appendChild(el("span", "tf-mini__count", ""));
    var track = el("span", "tf-mini__track"); track.appendChild(el("span")); mbtn.appendChild(track);
    var sheet = el("div", "tf-mini__sheet"); sheet.appendChild(build());
    mini.appendChild(sheet); mini.appendChild(mbtn); content.appendChild(mini);
    function closeMini() { mini.classList.remove("is-open"); mbtn.setAttribute("aria-expanded", "false"); }
    mbtn.addEventListener("click", function () { var open = mini.classList.toggle("is-open"); mbtn.setAttribute("aria-expanded", open ? "true" : "false"); });
    sheet.addEventListener("click", function (e) { if (e.target.closest("a")) closeMini(); });
    var onKey = function (e) { if (e.key === "Escape") closeMini(); };
    document.addEventListener("keydown", onKey); onCleanup(function () { document.removeEventListener("keydown", onKey); });

    /* 머리 카드의 번호 지도 [data-tf-map] */
    $$("[data-tf-map]", content).forEach(function (box) {
      box.textContent = ""; box.classList.add("tf-map"); box.setAttribute("aria-label", "단계 바로 가기");
      var lastPhase = "";
      stepItems.forEach(function (i) {
        var ph = i.sec.getAttribute("data-phase") || "";
        if (ph && ph !== lastPhase) { box.appendChild(el("span", "tf-map__phase", ph)); lastPhase = ph; }
        var a = el("a", "", i.num); a.href = "#" + i.id; a.title = (i.sec.getAttribute("data-full") || i.num) + " " + i.label; a.setAttribute("data-id", i.id); box.appendChild(a);
      });
    });

    /* 단계 완료 단추 */
    stepItems.forEach(function (i) {
      var btn = i.sec.querySelector("button.tf-done");
      btn.addEventListener("click", function () { state.steps[i.id] = !state.steps[i.id]; save(state); render(); });
    });

    var current = null, followed = null, pageDay = dayOfPage();
    var checkTimes = $$(".tf-check time", content).map(function (t) { return t.textContent.trim(); }).filter(function (x) { return /^\d{1,2}:\d{2}$/.test(x); });
    function render() {
      var done = stepItems.filter(function (i) { return state.steps[i.id]; }).length, total = stepItems.length;
      var pct = total ? Math.round(done * 100 / total) : 0;
      stepItems.forEach(function (i) {
        var d = !!state.steps[i.id]; i.sec.classList.toggle("is-done", d); i.sec.classList.toggle("is-current", i.id === current);
        var btn = i.sec.querySelector("button.tf-done"); btn.setAttribute("aria-pressed", d ? "true" : "false"); btn.textContent = d ? "완료함" : "이 단계 완료";
      });
      $$(".tf-progress__item, .tf-map a").forEach(function (x) { var id = x.getAttribute("data-id"); x.classList.toggle("is-done", !!state.steps[id]); x.classList.toggle("is-current", id === current); });
      $$(".tf-progress__count").forEach(function (c) { c.textContent = done + " / " + total + " 단계"; });
      $$(".tf-progress__bar > span, .tf-mini__track > span").forEach(function (s) { s.style.width = pct + "%"; });
      var cur = stepItems.filter(function (i) { return i.id === current; })[0];
      $$(".tf-mini__label").forEach(function (l) { l.textContent = short + " · " + (cur ? cur.full + " " + cur.label : "단계 목록 보기"); });
      /* 목록이 길면 지금 단계가 보이게 목록만 굴린다(쪽은 움직이지 않는다) */
      if (current !== followed) {
        followed = current;
        $$(".tf-progress ol").forEach(function (ol) {
          var it = ol.querySelector(".tf-progress__item.is-current"); if (!it || ol.scrollHeight <= ol.clientHeight + 4) return;
          if (it.offsetTop < ol.scrollTop + 8) ol.scrollTop = Math.max(0, it.offsetTop - 40);
          else if (it.offsetTop + it.offsetHeight > ol.scrollTop + ol.clientHeight - 8) ol.scrollTop = it.offsetTop + it.offsetHeight - ol.clientHeight + 40;
        });
      }
      $$(".tf-mini__count").forEach(function (c) { c.textContent = done + "/" + total; });
      /* 그날 쪽이면 : 지금 시각의 권장 단계 + 다음 점검 */
      var t = now(), parts = [];
      if (pageDay && DAYS[pageDay] === t.date) {
        var m = toMin(t.hm);
        var hit = stepItems.filter(function (i) { return i.start && toMin(i.start) <= m && m < toMin(i.end); })[0];
        var nextCheck = checkTimes.filter(function (x) { return toMin(x) >= m; }).sort(function (a, b) { return toMin(a) - toMin(b); })[0];
        if (hit || nextCheck) parts.push(["지금 " + t.hm, true]);
        if (hit) { parts.push([" — 권장 단계 ", false]); parts.push([hit.full, true]); parts.push([" " + hit.label, false]); }
        if (nextCheck) { parts.push([" · 다음 점검 ", false]); parts.push([nextCheck, true]); }
      }
      $$(".tf-progress__now").forEach(function (p) {
        p.textContent = "";
        parts.forEach(function (x) { if (x[1]) p.appendChild(el("b", "tf-nowrap", x[0])); else p.appendChild(document.createTextNode(x[0])); });
        p.hidden = !parts.length;
      });
    }

    /* 지금 읽는 단계(스크롤 위치) */
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { current = e.target.getAttribute("data-step"); render(); } });
      }, { rootMargin: "-35% 0px -55% 0px" });
      stepItems.forEach(function (i) { io.observe(i.sec); });
      onCleanup(function () { io.disconnect(); });
    }
    /* 1분마다 '지금 권장 단계'를 새로 */
    var timer = window.setInterval(render, 60000); onCleanup(function () { window.clearInterval(timer); });
    render();
    return render;
  }

  /* ---------- 5) 열기 시각(open_at) 소프트 잠금 ----------
     생성기(tools/sync_site_assets.py)가 _index.json의 시각을 카드에 적는다:
       · 파일이 있는 카드  <a class="tf-dl__item is-timed" href … data-tf-open="2026-10-15T06:35:00Z" data-tf-open-label="10/15(목) 15:35">
       · 봉인 공개 카드    <span class="tf-dl__item is-locked is-sealed" data-tf-release="2026-10-21T00:28:00Z" …>
       · (별칭) 아무 링크  <a … data-open-at="…">
     JS가 없으면 링크는 그냥 살아 있고 카드의 '… 이후 열기' 글이 안내한다(소프트 잠금). */
  function lockLabel(ms, t) {
    var p = kstParts(ms);
    return (p.date === t.date ? p.hm : p.md + "(" + p.dow + ") " + p.hm) + " 공개";
  }
  function openAt(x) { return Date.parse(x.getAttribute("data-tf-open") || x.getAttribute("data-open-at") || x.getAttribute("data-tf-release") || ""); }
  function locks(content) {
    var items = $$("[data-tf-open], [data-open-at], [data-tf-release]", content).filter(function (x) { return !isNaN(openAt(x)); });
    if (!items.length) return;
    function apply() {
      var t = now(), soonest = Infinity;
      items.forEach(function (x) {
        var at = openAt(x);
        var isCard = x.classList.contains("tf-dl__item"), isLink = x.tagName === "A";
        x.classList.add("tf-js-timed");
        var chip = x.querySelector(".tf-chip--lock, .tf-chip--soon");
        if (!chip && !isCard && x.nextSibling && x.nextSibling.classList && x.nextSibling.classList.contains("tf-chip--lock")) chip = x.nextSibling;
        if (t.ms < at) {
          soonest = Math.min(soonest, at);
          if (isLink && x.hasAttribute("href")) {
            x.setAttribute("data-tf-href", x.getAttribute("href")); x.removeAttribute("href");
            if (x.hasAttribute("download")) { x.setAttribute("data-tf-download", x.getAttribute("download")); x.removeAttribute("download"); }
          }
          if (x.hasAttribute("title") && !x.hasAttribute("data-tf-title")) x.setAttribute("data-tf-title", x.getAttribute("title"));
          x.classList.add(isCard ? "is-locked" : "tf-locked-link"); x.classList.remove("is-open", "is-soon");
          x.setAttribute("aria-disabled", "true");
          x.title = lockLabel(at, t) + " — 그 전에는 받지 않습니다. 먼저 내 결과를 만든 뒤 비교용으로 엽니다";
          if (!chip) { chip = el("span"); var host = x.querySelector(".tf-dl__desc"); if (host) host.insertBefore(chip, host.firstChild); else x.parentNode.insertBefore(chip, x.nextSibling); }
          chip.className = "tf-chip tf-chip--lock"; chip.textContent = lockLabel(at, t);
        } else if (isLink) {
          if (x.hasAttribute("data-tf-href")) { x.setAttribute("href", x.getAttribute("data-tf-href")); x.removeAttribute("data-tf-href"); }
          if (x.hasAttribute("data-tf-download")) { x.setAttribute("download", x.getAttribute("data-tf-download")); x.removeAttribute("data-tf-download"); }
          x.classList.remove("is-locked", "tf-locked-link"); x.classList.add("is-open"); x.removeAttribute("aria-disabled");
          if (x.hasAttribute("data-tf-title")) x.setAttribute("title", x.getAttribute("data-tf-title")); else x.removeAttribute("title");
          if (chip) chip.remove();
        } else {
          /* 봉인 공개 카드(아직 링크가 없는 카드) : 시각이 지났으면 사이트가 다시 만들어지는 중이다 */
          x.classList.add("is-soon");
          if (!chip) { chip = el("span"); var h2 = x.querySelector(".tf-dl__desc"); if (h2) h2.insertBefore(chip, h2.firstChild); else x.appendChild(chip); }
          chip.className = "tf-chip tf-chip--soon"; chip.textContent = "곧 열림 · 1–3분 뒤 새로 고침";
        }
      });
      if (soonest < Infinity) {
        var wait = Math.max(1000, Math.min(soonest - now().ms + 500, 15 * 60 * 1000));
        var tm = window.setTimeout(apply, wait); onCleanup(function () { window.clearTimeout(tm); });
      }
    }
    apply();
  }

  /* ---------- 6) 그림 확대 ---------- */
  function lightbox(content) {
    var dlg = $("dialog.tf-lightbox");
    if (!dlg) {
      dlg = el("dialog", "tf-lightbox"); dlg.setAttribute("aria-label", "그림 크게 보기");
      dlg.appendChild(el("img")); dlg.appendChild(el("p"));
      dlg.addEventListener("click", function () { dlg.close(); }); document.body.appendChild(dlg);
    }
    $$("figure img, img.tf-zoom", content).forEach(function (im) {
      if (im.closest("a") || im.hasAttribute("data-tf-zoom")) return;
      im.setAttribute("data-tf-zoom", ""); im.setAttribute("tabindex", "0");
      function open() {
        if (typeof dlg.showModal !== "function") { window.open(im.currentSrc || im.src, "_blank"); return; }
        var img = dlg.querySelector("img"); img.src = im.currentSrc || im.src; img.alt = im.alt;
        var fc = im.closest("figure") && im.closest("figure").querySelector("figcaption");
        dlg.querySelector("p").textContent = fc ? norm(fc.textContent) : (im.alt || "");
        dlg.showModal();
      }
      im.addEventListener("click", open);
      im.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); } });
    });
  }

  /* ---------- 표 : 4열 이상(또는 .tf-stack 안)은 모바일에서 줄마다 카드 ---------- */
  function stack(t) {
    var heads = $$("thead th", t).map(function (th) { return norm(th.textContent); });
    t.setAttribute("data-tf-stack", "");
    $$("tbody tr", t).forEach(function (tr) { $$("td", tr).forEach(function (td, k) { td.setAttribute("data-label", heads[k] || ""); }); });
  }
  function tables(content) {
    $$("table:not([class])", content).forEach(function (t) {
      if (t.hasAttribute("data-tf-stack") || t.closest(".tf-scroll")) return;
      var n = $$("thead th", t).length;
      if (n >= 4 || (n >= 2 && t.closest(".tf-stack, .tf-gloss"))) stack(t);
    });
  }
  /* 2–3열 표도 휴대폰 폭에 안 들어가면(가로 스크롤이 생기면) 줄 카드로 — 줄 카드 모양은 CSS가 휴대폰 폭에서만 쓴다.
     <wbr>(긴 파일 이름의 끊을 자리)을 넣은 뒤에 잰다. 화면을 돌려 좁아지면 다시 잰다. */
  var NARROW = "(max-width: 44.9375em)";
  function fitTables(content) {
    function fit() {
      if (!window.matchMedia || !window.matchMedia(NARROW).matches) return;
      $$("table:not([class]):not([data-tf-stack])", content).forEach(function (t) {
        if (t.closest(".tf-scroll")) return;
        var wrap = t.closest(".md-typeset__scrollwrap") || t.parentElement;
        if (wrap && wrap.scrollWidth > wrap.clientWidth + 2) stack(t);
      });
    }
    fit();
    var tm = null, onResize = function () { window.clearTimeout(tm); tm = window.setTimeout(fit, 200); };
    window.addEventListener("resize", onResize);
    onCleanup(function () { window.removeEventListener("resize", onResize); window.clearTimeout(tm); });
  }

  /* ---------- 긴 경로 · 파일 이름(코드 · 내려받기 카드 이름) : _ / . 뒤에 줄 바꿈 자리(<wbr>) ----------
     좁은 칸(표 · 휴대폰)에서 'd3_start_fe/atures.csv'처럼 글자 중간이 아니라 마디(d3_start_ · features.csv)에서 끊기게. 복사되는 글자는 그대로. */
  function breaks(content) {
    var narrow = !!(window.matchMedia && window.matchMedia(NARROW).matches);
    $$("code, .tf-dl__name", content).forEach(function (c) {
      if (c.hasAttribute("data-tf-wbr") || c.children.length || c.closest("pre")) return;
      /* 넓은 화면에서 표 첫 칸의 이름 하나(CSS가 한 줄로 둔다)는 건드리지 않는다 — <wbr>은 nowrap 안에서도 줄을 바꾼다 */
      var td = c.parentElement;
      if (!narrow && td && td.tagName === "TD" && !td.previousElementSibling && td.children.length === 1) return;
      var s = c.textContent; c.setAttribute("data-tf-wbr", "");
      if (s.length < 14 || !/[_\/.]/.test(s)) return;
      var frag = document.createDocumentFragment(), last = 0;
      for (var i = 1; i < s.length - 1; i++) {
        if ("_/.".indexOf(s[i]) >= 0 && !/[\s_\/.]/.test(s[i + 1]) && i - last >= 2 && !(s[i] === "." && /^[A-Za-z0-9]{1,5}$/.test(s.slice(i + 1)))) {   /* 확장자(.md · .xlsx)는 이름에 붙여 둔다 */
          frag.appendChild(document.createTextNode(s.slice(last, i + 1))); frag.appendChild(document.createElement("wbr")); last = i + 1;
        }
      }
      if (!last) return;
      frag.appendChild(document.createTextNode(s.slice(last)));
      c.textContent = ""; c.appendChild(frag); c.setAttribute("data-tf-wbr", "br");   /* 끊을 자리가 생긴 코드 — 휴대폰 표 첫 칸에서도 줄을 바꿔도 된다(CSS) */
    });
    /* 프롬프트(본문 글꼴 · 어절 단위 줄바꿈) 안의 긴 경로 'workbench/day3/outputs/d3_scores.csv에'도 / _ 뒤에서 끊기게 — 복사 글자는 그대로 */
    $$(".prompt pre code, .tf-promptlib .language-text pre code", content).forEach(function (code) {
      if (code.hasAttribute("data-tf-wbr")) return; code.setAttribute("data-tf-wbr", "");
      var walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT, null), nodes = [], n;
      while ((n = walker.nextNode())) if (/\S{16,}/.test(n.nodeValue) && /[\/_]/.test(n.nodeValue)) nodes.push(n);
      nodes.forEach(function (tx) {
        var s = tx.nodeValue, frag = document.createDocumentFragment(), last = 0;
        s.replace(/\S{16,}/g, function (tok, at) {
          for (var i = 1; i < tok.length - 1; i++) {
            if ((tok[i] === "/" || tok[i] === "_") && !/[\s\/_]/.test(tok[i + 1]) && at + i + 1 - last >= 3) {
              frag.appendChild(document.createTextNode(s.slice(last, at + i + 1))); frag.appendChild(document.createElement("wbr")); last = at + i + 1;
            }
          }
          return tok;
        });
        if (!last) return;
        frag.appendChild(document.createTextNode(s.slice(last))); tx.parentNode.replaceChild(frag, tx);
      });
    });
  }

  /* ---------- 프롬프트의 {빈칸} 강조 (복사되는 글자는 그대로) ---------- */
  function fills(content) {
    $$(".prompt pre code, .tf-promptlib .language-text pre code", content).forEach(function (code) {
      if (code.hasAttribute("data-tf-fill")) return; code.setAttribute("data-tf-fill", "");
      var walker = document.createTreeWalker(code, NodeFilter.SHOW_TEXT, null), nodes = [], n;
      while ((n = walker.nextNode())) if (/\{[^{}\n]{1,30}\}/.test(n.nodeValue) && !(n.parentNode.closest && n.parentNode.closest("mark"))) nodes.push(n);
      nodes.forEach(function (tx) {
        var frag = document.createDocumentFragment(), s = tx.nodeValue, last = 0;
        s.replace(/\{[^{}\n]{1,30}\}/g, function (m, i) { frag.appendChild(document.createTextNode(s.slice(last, i))); frag.appendChild(el("mark", "tf-fill", m)); last = i + m.length; return m; });
        frag.appendChild(document.createTextNode(s.slice(last))); tx.parentNode.replaceChild(frag, tx);
      });
    });
  }

  /* ---------- 거르기 입력 : <div class="tf-filter" data-tf-filter=".tf-gloss"></div> ---------- */
  function filters(content) {
    $$("[data-tf-filter]", content).forEach(function (box) {
      if (box.querySelector("input")) return;
      var scope = box.getAttribute("data-tf-filter") || ".md-typeset";
      var ph = box.getAttribute("data-placeholder") || "용어 · 정의로 찾기 (예: 토큰, SHAP, 한도)";
      var icon = el("span", "tf-filter__icon"); icon.setAttribute("aria-hidden", "true");
      var input = el("input"); input.type = "search"; input.placeholder = ph; input.setAttribute("aria-label", ph);
      var count = el("span", "tf-filter__count", "");
      box.appendChild(icon); box.appendChild(input); box.appendChild(count);
      var rows = $$(scope + " tbody tr", content);
      input.addEventListener("input", function () {
        var q = norm(input.value).toLowerCase(), shown = 0;
        rows.forEach(function (tr) { var hit = !q || tr.textContent.toLowerCase().indexOf(q) >= 0; tr.classList.toggle("is-hidden", !hit); if (hit) shown++; });
        count.textContent = q ? shown + "개 찾음" : "";
      });
    });
  }

  /* ---------- 인쇄 : 접힌 상자 펼치기 ---------- */
  var opened = [];
  window.addEventListener("beforeprint", function () { opened = $$("details:not([open])"); opened.forEach(function (d) { d.setAttribute("open", ""); }); });
  window.addEventListener("afterprint", function () { opened.forEach(function (d) { d.removeAttribute("open"); }); opened = []; });

  /* ---------- 시작 ---------- */
  function init() {
    cleanup();
    document.body.classList.remove("tf-has-progress", "tf-is-home");
    $$(".tf-progress, .tf-mini").forEach(function (x) { x.remove(); });
    var content = $("article.md-content__inner"); if (!content) return;
    if (content.querySelector(".tf-home")) document.body.classList.add("tf-is-home");
    var state = load();
    today(content);
    cards(content);
    var secs = steps(content);
    var render = secs.length ? tracker(content, secs, state) : function () {};
    checkboxes(content, state, render);
    checklists(content);
    locks(content);
    lightbox(content); tables(content); fills(content); breaks(content); fitTables(content); filters(content);
  }
  var booted = false;
  function boot() { booted = true; init(); }
  if (window.document$ && typeof window.document$.subscribe === "function") window.document$.subscribe(function () { boot(); });
  // file://(USB 사본)처럼 document$가 오지 않는 경우 — 한 번은 직접 시작한다(두 번 불려도 init이 앞의 것을 지우고 다시 만든다)
  var fallback = function () { setTimeout(function () { if (!booted) boot(); }, 400); };
  if (document.readyState !== "loading") fallback();
  else document.addEventListener("DOMContentLoaded", fallback);
})();
