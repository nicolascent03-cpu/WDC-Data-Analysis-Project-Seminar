// Chord ring of one year's arms flows plus a country card (Streamlit custom component v2).
// Port of chordView() in app/site/flows.js and flowCard() in app/site/adc.html. Python sends every number
// (data.ring, data.cards); this file only lays out the ring in real pixels, tweens between years, highlights on
// hover and swaps the ring for a country card while a country node is hovered or a card is pinned.
// Events back: setTriggerValue("pin", cardKey) on a click on a country node, setTriggerValue("close", true) on ×.

const NS = "http://www.w3.org/2000/svg";
const INST = new WeakMap();

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (v) => Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });
const pct = (x) => !(x > 0) ? "0%" : x < 0.005 ? "<1%" : Math.round(x * 100) + "%";
const trunc = (s, n) => s.length > n ? s.slice(0, n - 1) + "…" : s;
const lerp = (a, b, p) => a + (b - a) * p;
const ease = (p) => p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// ------------------------------------------------------------------ country card (flowCard in adc.html)
function cardHtml(f, closable) {
  const y = f.year;
  const bars = (p, kind) => {
    if (!p.total) return '<p class="fc-none">No ' + kind + " in " + y + "</p>";
    const row = (name, v, col) => '<li><span class="fc-n" title="' + esc(name) + '">' + esc(trunc(name, 26)) + '</span><span class="fc-bar"><i style="width: ' +
      Math.max(2, v / p.total * 100).toFixed(1) + "%; background: " + col + '"></i></span><span class="fc-v">' + fmt(v) + "</span></li>";
    return '<ul class="fc-list">' + p.top.map((x) => row(x.name, x.v, x.color)).join("") +
      (p.other > 0.5 ? row(p.n > 0 && !p.lumped ? "other (" + p.n + ")" : "other", p.other, "var(--s-oth)") : "") + "</ul>";
  };
  const sec = (lab, p, kind, note) => '<div class="fc-sec"><div class="fc-sh"><span>' + lab + '</span><b>' +
    (p.total > 0 ? fmt(p.total) + " TIV" : "none recorded") + "</b></div>" + (note ? '<p class="fc-note">' + note + "</p>" : "") + bars(p, kind) + "</div>";
  let h = '<div class="fc-h"><div><h4>' + esc(f.name) + " <span>" + y + "</span></h4><p>" + esc(f.regime) + "</p></div>" +
    (closable ? '<button class="fc-x" type="button" aria-label="Close country card" title="Close">×</button>' : "") + "</div>";
  if (!f.imp.total && !f.exp.total) h += '<p class="fc-empty">No major arms deliveries in ' + y + ".</p>";
  else h += sec("Imports", f.imp, "imports") + sec("Exports", f.exp, "exports");
  h += '<dl class="fc-foot">' + (f.main ? "<div><dt>Main supplier " + (y - 4) + "–" + y + '</dt><dd><i style="background: ' + f.mainColor + '"></i>' + esc(f.main) + "</dd></div>" : "") +
    "<div><dt>Share of world imports " + y + "</dt><dd>" + pct(f.worldShare) + "</dd></div></dl>";
  return h;
}

// ------------------------------------------------------------------ one instance
function create(parentElement) {
  const root = parentElement.querySelector(".chr-root");
  const svg = el("svg", { role: "img", "aria-label": "Chord ring of arms deliveries" }, root);
  const ribG = el("g", { class: "ch-ribs" }, svg), nodeG = el("g", { class: "ch-nodes" }, svg);
  const empty = el("text", { class: "ch-empty", "text-anchor": "middle" }, svg);
  const card = document.createElement("div");
  card.className = "chr-card"; card.hidden = true; card.setAttribute("aria-live", "polite");
  const tip = document.createElement("div");
  tip.className = "chr-tip"; tip.hidden = true;
  root.append(card, tip);

  const S = {
    G: null, ring: null, cards: {}, pinned: null, tweenMs: 800, height: 440, year: null,
    hoverCard: null, sel: null, tw: null, raf: 0, shown: "", W: 0,
    curN: new Map(), curL: new Map(), nodeEl: new Map(), ribEl: new Map(), info: new Map(),
    setTrigger: null,
  };

  function setup() {
    const W = Math.max(240, Math.round(root.clientWidth || 400)), H = S.height;
    // room for the labels: supplier "Soviet U. 36%" on the left, recipient names cut at 14 characters on the right
    const supW = 66, recW = 80, LG = 16;
    const R = Math.max(56, Math.min((W - supW - recW) / 2 - LG, H / 2 - 24));
    const cx = supW + LG + R + Math.max(0, (W - supW - recW - 2 * (R + LG)) / 2);
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("width", W); svg.setAttribute("height", H);
    const mx = S.ring.max, g0 = 0.07 * Math.PI, span = Math.PI - 2 * g0, pad = 0.03;
    const slots = (m) => {
      m = m.map((x) => Math.max(x, 0.02));
      const sum = m.reduce((a, b) => a + b, 0), k = (span - pad * m.length) / sum;
      let u = pad / 2;
      return { k: k, c: m.map((x) => { const c = u + x * k / 2; u += x * k + pad; return c; }) };
    };
    const Ls = slots(mx.s), Rs = slots(mx.r);
    S.G = { W: W, H: H, cx: cx, cy: H / 2, R: R, LG: LG, A: Math.min(Ls.k, Rs.k), sc: Ls.c, rc: Rs.c, g0: g0 };
    S.W = W;
    ribG.innerHTML = ""; nodeG.innerHTML = "";
    S.curN.clear(); S.curL.clear(); S.nodeEl.clear(); S.ribEl.clear(); S.info.clear(); S.tw = null;
    empty.setAttribute("x", cx); empty.setAttribute("y", H / 2);
  }

  const ang = (side, u) => side ? -Math.PI / 2 + S.G.g0 + u : 1.5 * Math.PI - S.G.g0 - u; // side 1 = right
  const pt = (side, u, rad) => { const a = ang(side, u); return [S.G.cx + rad * Math.cos(a), S.G.cy + rad * Math.sin(a)]; };
  const P = (p) => p[0].toFixed(1) + "," + p[1].toFixed(1);
  function segD(side, u0, u1, r0, r2) {
    const sw = side ? 1 : 0, bw = side ? 0 : 1;
    const a = pt(side, u0, r0), b = pt(side, u1, r0), c = pt(side, u1, r2), d = pt(side, u0, r2);
    return "M" + P(a) + "A" + r0 + "," + r0 + " 0 0 " + sw + " " + P(b) + "L" + P(c) + "A" + r2 + "," + r2 + " 0 0 " + bw + " " + P(d) + "Z";
  }
  function ribD(v) {
    const R = S.G.R, c = S.G.cx + "," + S.G.cy;
    const s0 = pt(0, v[0], R), s1 = pt(0, v[1], R), q0 = pt(1, v[2], R), q1 = pt(1, v[3], R);
    return "M" + P(s0) + "A" + R + "," + R + " 0 0 0 " + P(s1) + "Q" + c + " " + P(q1) + "A" + R + "," + R + " 0 0 0 " + P(q0) + "Q" + c + " " + P(s0) + "Z";
  }
  function nodeElement(id, side) {
    let e = S.nodeEl.get(id);
    if (e) return e;
    const g = el("g", { class: "ch-node" + (side ? " ch-rec" : " ch-sup"), "data-cid": id }, nodeG);
    e = { g: g, hit: el("path", { class: "ch-hit" }, g), seg: el("path", { class: "ch-seg" }, g),
      lab: el("text", { class: "ch-lab", dy: ".35em", "text-anchor": side ? "start" : "end" }, g), side: side };
    S.nodeEl.set(id, e);
    return e;
  }
  // push labels of one side apart vertically (min. 14 px) so neighbours never overlap
  function spread(a) {
    const gap = 14, live = a.filter((l) => l.e.textContent && !l.e.parentNode.classList.contains("out")).sort((u, v) => u.y - v.y);
    for (let i = 1; i < live.length; i++) if (live[i].y < live[i - 1].y + gap) live[i].y = live[i - 1].y + gap;
    for (let i = live.length - 1; i >= 0; i--) live[i].y = Math.min(live[i].y, i === live.length - 1 ? S.G.H - 8 : live[i + 1].y - gap);
    for (const l of live) l.e.setAttribute("y", l.y.toFixed(1));
  }
  function spreadAll() {
    const labs = [[], []];
    for (const ne of S.nodeEl.values()) if (ne.ly != null) labs[ne.side].push({ e: ne.lab, y: ne.ly });
    spread(labs[0]); spread(labs[1]);
  }
  function render(p) {
    const e = ease(p), tw = S.tw, G = S.G;
    for (const [id, t] of tw.N) {
      const v = [lerp(t.from[0], t.to[0], e), lerp(t.from[1], t.to[1], e)];
      S.curN.set(id, v);
      const ne = nodeElement(id, t.side);
      ne.seg.setAttribute("d", segD(t.side, v[0], v[1], G.R + 3, G.R + 13));
      ne.hit.setAttribute("d", segD(t.side, v[0] - 0.01, v[1] + 0.01, G.R - 4, G.R + 17));
      const mid = t.side || t.slot < 0 ? (v[0] + v[1]) / 2 : G.sc[t.slot];
      const lp = pt(t.side, mid, G.R + G.LG);
      ne.lab.setAttribute("x", lp[0].toFixed(1)); ne.lab.setAttribute("y", lp[1].toFixed(1));
      ne.ly = lp[1];
    }
    spreadAll();
    for (const [k, t] of tw.L) {
      const v = t.from.map((x, i) => lerp(x, t.to[i], e));
      S.curL.set(k, v);
      let r = S.ribEl.get(k);
      if (!r) { r = el("path", { class: "ch-rib", "data-cid": k }, ribG); S.ribEl.set(k, r); }
      r.setAttribute("d", ribD(v));
    }
    if (p >= 1) {
      for (const id of tw.deadN) { const ne = S.nodeEl.get(id); if (ne) ne.g.remove(); S.nodeEl.delete(id); S.curN.delete(id); }
      for (const k of tw.deadL) { const r = S.ribEl.get(k); if (r) r.remove(); S.ribEl.delete(k); S.curL.delete(k); }
      S.tw = null;
    }
  }
  function loop(t) {
    S.raf = 0;
    if (!S.tw) return;
    render(Math.max(0, Math.min(1, (t - S.tw.t0) / S.tweenMs)));
    if (S.tw) S.raf = requestAnimationFrame(loop);
  }

  // highlight: sel = {s: Set of supplier node ids, r: Set of recipient node ids}
  function apply() {
    const sel = S.sel, on = new Set(), ch = S.ring;
    if (sel && ch) {
      for (const l of ch.links) {
        const a = ch.S[l.si].id, b = ch.R[l.ri].id;
        if (sel.has(a) || sel.has(b)) { on.add(a + "|" + b); on.add(a); on.add(b); }
      }
      for (const id of sel) on.add(id);
    }
    for (const [id, ne] of S.nodeEl) ne.g.classList.toggle("dim", !!sel && !on.has(id));
    for (const [k, r] of S.ribEl) r.classList.toggle("dim", !!sel && !on.has(k));
  }

  function drawYear(instant) {
    const ch = S.ring, G = S.G, A = G.A;
    S.info.clear();
    const N = new Map(), Lk = new Map();
    ch.S.forEach((s) => { const c = G.sc[s.slot], h = s.share * A / 2; N.set(s.id, { side: 0, slot: s.slot, to: [c - h, c + h], n: s }); });
    ch.R.forEach((r) => { const c = G.rc[r.slot], h = r.share * A / 2; N.set(r.id, { side: 1, slot: r.slot, to: [c - h, c + h], n: r }); });
    // link endpoints: inside each supplier segment ordered by recipient slot, inside each recipient segment by supplier slot
    const byS = new Map(), byR = new Map();
    for (const l of ch.links) {
      const k = ch.S[l.si].id + "|" + ch.R[l.ri].id;
      Lk.set(k, { l: l, to: [0, 0, 0, 0] });
      (byS.get(l.si) || byS.set(l.si, []).get(l.si)).push(k);
      (byR.get(l.ri) || byR.set(l.ri, []).get(l.ri)).push(k);
    }
    for (const [si, ks] of byS) {
      ks.sort((a, b) => ch.R[Lk.get(a).l.ri].slot - ch.R[Lk.get(b).l.ri].slot);
      let u = N.get(ch.S[si].id).to[0];
      for (const k of ks) { const t = Lk.get(k), w = t.l.share * A; t.to[0] = u; t.to[1] = u + w; u += w; }
    }
    for (const [ri, ks] of byR) {
      ks.sort((a, b) => ch.S[Lk.get(a).l.si].slot - ch.S[Lk.get(b).l.si].slot);
      let u = N.get(ch.R[ri].id).to[0];
      for (const k of ks) { const t = Lk.get(k), w = t.l.share * A; t.to[2] = u; t.to[3] = u + w; u += w; }
    }
    // tween from where things are now; new ones grow from their centre, old ones shrink to theirs
    const TN = new Map(), TL = new Map(), deadN = [], deadL = [];
    for (const [id, t] of N) {
      const m = (t.to[0] + t.to[1]) / 2;
      TN.set(id, { side: t.side, slot: t.slot, from: S.curN.get(id) || [m, m], to: t.to });
    }
    for (const [id, v] of S.curN) if (!N.has(id)) {
      const m = (v[0] + v[1]) / 2;
      TN.set(id, { side: id[0] === "r" ? 1 : 0, slot: -1, from: v, to: [m, m] }); deadN.push(id);
      const ne = S.nodeEl.get(id); if (ne) ne.g.classList.add("out");
    }
    for (const [k, t] of Lk) {
      const ms = (t.to[0] + t.to[1]) / 2, mr = (t.to[2] + t.to[3]) / 2;
      TL.set(k, { from: S.curL.get(k) || [ms, ms, mr, mr], to: t.to });
    }
    for (const [k, v] of S.curL) if (!Lk.has(k)) {
      const ms = (v[0] + v[1]) / 2, mr = (v[2] + v[3]) / 2;
      TL.set(k, { from: v, to: [ms, ms, mr, mr] }); deadL.push(k);
    }
    S.tw = { t0: performance.now(), N: TN, L: TL, deadN: deadN, deadL: deadL };
    render(instant ? 1 : 0);
    // labels, colours, tooltips (once per year, not per frame)
    for (const [id, t] of N) {
      const ne = nodeElement(id, t.side), x = t.n;
      ne.g.classList.remove("out");
      ne.g.classList.toggle("country", !!x.card);
      S.info.set(id, { kind: t.side ? "r" : "s", n: x });
      ne.seg.style.fill = x.color;
      ne.lab.textContent = t.side ? (x.other ? "Others" : trunc(x.name, 14)) : x.label + " " + pct(x.share);
    }
    for (const [k, t] of Lk) {
      const l = t.l;
      S.info.set(k, { kind: "link", l: l });
      S.ribEl.get(k).style.fill = ch.S[l.si].color;
    }
    for (const id of deadN) S.info.delete(id);
    spreadAll();
    empty.textContent = ch.tot ? "" : "No deliveries in " + ch.year;
    apply();
    if (S.tw && !S.raf) S.raf = requestAnimationFrame(loop);
  }

  // card over the ring: the hovered country, else the pinned one
  function showCard() {
    const key = S.hoverCard || S.pinned, f = key ? S.cards[key] : null;
    const closable = !!f && !S.hoverCard && key === S.pinned;
    const sig = f ? key + "|" + f.year + "|" + closable : "";
    if (sig !== S.shown) {
      S.shown = sig;
      card.innerHTML = f ? cardHtml(f, closable) : "";
      const x = card.querySelector(".fc-x");
      if (x) x.onclick = (e) => { e.stopPropagation(); if (S.setTrigger) S.setTrigger("close", true); };
    }
    card.hidden = !f;
    root.classList.toggle("carding", !!f);
    if (f) tip.hidden = true;
  }

  function tipText(id) {
    const x = S.info.get(id), ch = S.ring, y = " · " + ch.year;
    if (!x) return null;
    if (x.kind === "link") {
      const a = ch.S[x.l.si], b = ch.R[x.l.ri];
      return "<b>" + esc(a.name) + " → " + esc(b.name) + "</b>" + y + "<span>" + fmt(x.l.v) + " TIV, " + pct(x.l.share) + " of the year</span>";
    }
    const n = x.n;
    return "<b>" + esc(n.name) + "</b>" + y + "<span>" + fmt(n.v) + " TIV, " + pct(n.share) + " of the year" +
      (n.note ? "<br>" + esc(n.note) : "") + (n.card ? "<br>Click to pin its card" : "") + "</span>";
  }
  function moveTip(ev) {
    const b = root.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = ev.clientX - b.left + 12, y = ev.clientY - b.top + 12;
    if (x + w > b.width) x = ev.clientX - b.left - w - 12;
    if (y + h > b.height) y = ev.clientY - b.top - h - 12;
    tip.style.left = Math.max(0, x) + "px"; tip.style.top = Math.max(0, y) + "px";
  }
  function hover(ev) {
    const t = ev.target.closest && ev.target.closest("[data-cid]"), id = t ? t.dataset.cid : null, x = id ? S.info.get(id) : null;
    let sel = null, hc = null;
    if (x) {
      if (x.kind === "link") sel = new Set([S.ring.S[x.l.si].id]);
      else { sel = new Set([id]); if (x.n.card && S.cards[x.n.card]) hc = x.n.card; }
    }
    S.sel = sel; apply();
    if (hc !== S.hoverCard) { S.hoverCard = hc; showCard(); }
    if (x && !hc && !(S.pinned && S.cards[S.pinned])) { tip.innerHTML = tipText(id); tip.hidden = false; moveTip(ev); }
    else tip.hidden = true;
  }
  svg.onpointermove = hover;
  svg.onpointerleave = () => { S.sel = null; apply(); tip.hidden = true; if (S.hoverCard) { S.hoverCard = null; showCard(); } };
  svg.onclick = (ev) => {
    const t = ev.target.closest && ev.target.closest("[data-cid]"), x = t ? S.info.get(t.dataset.cid) : null;
    if (x && x.kind !== "link" && x.n.card && S.setTrigger) S.setTrigger("pin", x.n.card);
  };

  const ro = new ResizeObserver(() => {
    if (!S.ring) return;
    const W = Math.round(root.clientWidth);
    if (!W || Math.abs(W - S.W) < 2) return;
    setup(); drawYear(true);
  });
  ro.observe(root);

  return {
    update(data, setTriggerValue) {
      S.setTrigger = setTriggerValue;
      S.tweenMs = Math.max(0, data.tween || 800);
      S.cards = data.cards || {};
      S.pinned = data.pinned && S.cards[data.pinned] ? data.pinned : null;
      const h = data.height || 440, sizeChanged = h !== S.height || !S.G;
      S.height = h; root.style.height = h + "px";
      const first = !S.ring, yearChanged = !S.ring || S.ring.year !== data.ring.year;
      S.ring = data.ring;
      if (sizeChanged || first) { setup(); drawYear(true); }
      else if (yearChanged) drawYear(false);
      if (S.hoverCard && !S.cards[S.hoverCard]) S.hoverCard = null;
      S.shown = ""; // year or card data may have changed
      showCard();
    },
    destroy() { ro.disconnect(); if (S.raf) cancelAnimationFrame(S.raf); root.innerHTML = ""; },
  };
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  if (!data || !data.ring) return;
  let inst = INST.get(parentElement);
  if (!inst) { inst = create(parentElement); INST.set(parentElement, inst); }
  inst.update(data, setTriggerValue);
  return () => { inst.destroy(); INST.delete(parentElement); };
}
