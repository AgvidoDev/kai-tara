// Kai Tara Mini App. Весь текст вставляется через textContent — без innerHTML.
(function () {
  "use strict";
  const tg = window.Telegram && window.Telegram.WebApp;
  const initData = tg ? tg.initData : "";
  const L = {
    ru: { today: "Сегодня", week: "Неделя", month: "Месяц", family: "Близкие", me: "Профиль",
          loading: "Считаю…", error: "Не удалось загрузить. Попробуйте ещё раз.", only_tg: "Откройте приложение из Telegram-бота @KaiTaraAstroBot.",
          need_birth: "Сначала укажите дату рождения в боте: /start", premium: "Доступно в Премиуме — откройте 💎 Премиум в боте.",
          good_for: "Хорошо для", avoid: "Лучше избегать", factors: "Ваши показатели", sky: "Небо дня",
          prev: "← Вчера", next: "Завтра →", events: "События неба", best: "Лучшие дни", hard: "Поберегите силы",
          for: "Для:", reset: "вернуться к себе", empty_family: "Близких пока нет. Добавить можно в боте: /family",
          family_hint: "Выберите человека — вкладки «Сегодня», «Неделя» и «Месяц» покажут его дни.",
          west: "Знак по западным датам", sid: "Сидерическое Солнце", moon: "Луна", nak: "Накшатра", lagna: "Лагна",
          dasha: "Махадаша", antar: "Антардаша", until: "до", place: "Город", transits: "Большие транзиты", since: "с",
          disclaimer: "Прогноз носит ознакомительный характер." },
    en: { today: "Today", week: "Week", month: "Month", family: "Family", me: "Profile",
          loading: "Calculating…", error: "Couldn't load. Please try again.", only_tg: "Open this app from the Telegram bot @KaiTaraAstroBot.",
          need_birth: "First enter your birth date in the bot: /start", premium: "Available in Premium — open 💎 Premium in the bot.",
          good_for: "Good for", avoid: "Better to avoid", factors: "Your factors", sky: "Sky of the day",
          prev: "← Yesterday", next: "Tomorrow →", events: "Sky events", best: "Best days", hard: "Take it easy",
          for: "For:", reset: "back to me", empty_family: "No profiles yet. Add them in the bot: /family",
          family_hint: "Choose a person — the Today, Week and Month tabs will show their days.",
          west: "Western sign", sid: "Sidereal Sun", moon: "Moon", nak: "Nakshatra", lagna: "Lagna",
          dasha: "Mahadasha", antar: "Antardasha", until: "until", place: "City", transits: "Major transits", since: "from",
          disclaimer: "This forecast is for information only." },
  };
  let lang = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && /^(ru|uk|be|kk)/.test(tg.initDataUnsafe.user.language_code || "")) ? "ru" : "en";
  const S = { tab: "today", rel: null, relName: null, day: null };
  const view = document.getElementById("view");
  const t = (k) => (L[lang] || L.en)[k] || k;

  function el(tag, props, ...kids) {
    const n = document.createElement(tag);
    if (props) for (const [k, v] of Object.entries(props)) {
      if (k === "text") n.textContent = v; else if (k === "on") n.addEventListener("click", v);
      else if (k === "cls") n.className = v; else n.setAttribute(k, v);
    }
    for (const k of kids) if (k != null) n.append(k);
    return n;
  }
  const list = (items) => el("ul", null, ...items.map((x) => el("li", { text: x })));
  const show = (...nodes) => { view.replaceChildren(...nodes); window.scrollTo(0, 0); };
  const msg = (text, cls) => show(el("p", { cls: cls || "muted", text }));

  async function api(path) {
    const r = await fetch(path, { headers: { Authorization: "tma " + initData } });
    let body = null;
    try { body = await r.json(); } catch (e) { /* пусто */ }
    if (!r.ok) throw Object.assign(new Error("api"), { status: r.status, body });
    return body;
  }
  const relQ = () => (S.rel ? "&rel=" + encodeURIComponent(S.rel) : "");

  function fail(e) {
    if (e.status === 409) return msg(t("need_birth"));
    if (e.status === 402) return msg(t("premium"));
    if (e.status === 404 && S.rel) { setSubject(null, null); return render(); }
    msg(t("error"), "err");
  }

  function applyLang() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = t(n.dataset.i18n); });
    document.getElementById("subject-reset").textContent = t("reset");
  }

  function setSubject(id, name) {
    S.rel = id; S.relName = name;
    const box = document.getElementById("subject");
    box.hidden = !id;
    document.getElementById("subject-name").textContent = id ? t("for") + " " + name : "";
  }

  // ---------------------------------------------------------------- экраны
  async function today() {
    msg(t("loading"));
    const d = await api("/api/day?date=" + encodeURIComponent(S.day || "") + relQ());
    S.day = d.date;
    const head = el("div", { cls: "card" }, el("div", { cls: "muted", text: d.label + " · " + d.place }));
    if (d.premium) head.append(el("div", { cls: "tone " + d.tone, text: d.icon + " " + d.tone_text }));
    const nodes = [head];
    const nav = el("div", { cls: "daynav" },
      el("button", { type: "button", text: t("prev"), on: () => shift(-1) }),
      el("button", { type: "button", text: t("next"), on: () => shift(1) }));
    if (d.premium) {
      if (d.reasons.length) nodes.push(el("h3", { text: t("factors") }), list(d.reasons));
      nodes.push(el("h3", { text: "✅ " + t("good_for") }), list(d.do));
      if (d.avoid.length) nodes.push(el("h3", { text: "⛔ " + t("avoid") }), list(d.avoid));
    }
    nodes.push(el("h3", { text: t("sky") }), list(d.sky.concat(d.special.map((x) => "✨ " + x))));
    if (!d.premium) nodes.push(el("p", { cls: "muted", text: t("premium") }));
    nodes.push(nav, el("p", { cls: "muted", text: t("disclaimer") }));
    show(...nodes);
  }
  function shift(n) {
    const d = new Date(S.day + "T12:00:00Z");
    d.setUTCDate(d.getUTCDate() + n);
    S.day = d.toISOString().slice(0, 10);
    today().catch(fail);
  }

  async function period(days) {
    msg(t("loading"));
    const p = await api("/api/period?days=" + days + relQ());
    const rows = p.days.map((x) => el("div", { cls: "row" },
      el("div", { cls: "d", text: x.label }),
      el("div", { cls: "t" }, el("div", { text: x.icon + " " + x.tone_text + " · " + x.nakshatra }),
        el("div", { cls: "muted", text: x.do + (x.special.length ? " · ✨ " + x.special.join(", ") : "") }))));
    const nodes = [];
    if (days === 30) {
      const best = p.days.filter((x) => x.score >= 2).map((x) => x.label);
      const hard = p.days.filter((x) => x.score <= -2).map((x) => x.label);
      const c = el("div", { cls: "card" });
      if (best.length) c.append(el("div", { text: "🟢 " + t("best") + ": " + best.join(", ") }));
      if (hard.length) c.append(el("div", { text: "🔴 " + t("hard") + ": " + hard.join(", ") }));
      if (c.childNodes.length) nodes.push(c);
    }
    nodes.push(el("div", { cls: "card" }, ...rows));
    if (p.events.length) nodes.push(el("h3", { text: "📅 " + t("events") }), list(p.events.map((e) => e.when + " — " + e.text)));
    nodes.push(el("p", { cls: "muted", text: t("disclaimer") }));
    show(...nodes);
  }

  async function family() {
    msg(t("loading"));
    const f = await api("/api/family");
    if (!f.items.length) return msg(t("empty_family"));
    show(el("p", { cls: "muted", text: t("family_hint") }),
      ...f.items.map((x) => el("button", { cls: "btn ghost", type: "button", text: "👤 " + x.name,
        on: () => { setSubject(x.id, x.name); S.day = null; go("today"); } })));
  }

  async function me() {
    msg(t("loading"));
    const [m, tr] = await Promise.all([api("/api/me"), api("/api/transits")]);
    if (!m.has_birth) return msg(t("need_birth"));
    const rows = [[t("place"), m.place], [t("west"), m.sun_west], [t("sid"), m.sun_sid], [t("moon"), m.moon],
      [t("nak"), m.nakshatra], [t("lagna"), m.lagna]].filter((r) => r[1]);
    const c = el("div", { cls: "card" }, ...rows.map((r) => el("div", { cls: "row" },
      el("div", { cls: "d", text: r[0] }), el("div", { cls: "t", text: r[1] }))));
    const nodes = [c];
    if (m.dasha) {
      let s = t("dasha") + ": " + m.dasha.maha;
      if (m.dasha.antar) s += " · " + t("antar") + ": " + m.dasha.antar + " (" + t("until") + " " + m.dasha.until + ")";
      nodes.push(el("div", { cls: "card", text: "⏳ " + s }));
    }
    if (tr.items.length) nodes.push(el("h3", { text: t("transits") }),
      list(tr.items.map((x) => x.title + " (" + t("since") + " " + x.since + ")")));
    show(...nodes);
  }

  const SCREENS = { today, week: () => period(7), month: () => period(30), family, me };
  function render() { return SCREENS[S.tab]().catch(fail); }
  function go(tab) {
    S.tab = tab;
    document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === tab));
    render();
  }

  applyLang();
  if (!initData) { msg(t("only_tg")); return; }
  document.querySelectorAll("#tabs button").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.tab === "today") S.day = null;
    go(b.dataset.tab);
  }));
  document.getElementById("subject-reset").addEventListener("click", () => { setSubject(null, null); S.day = null; render(); });

  tg.ready(); tg.expand();
  api("/api/me").then((m) => { if (m.lang && m.lang !== lang) { lang = m.lang; applyLang(); } go("today"); })
    .catch((e) => { if (e.status === 401) msg(t("only_tg")); else go("today"); });
})();
