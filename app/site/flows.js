/* ADC arms flows: data and drawing for the three linked "Arms flows" views
   (map ribbons with direction dots, chord ring, river of time).
   Plain script, no libraries. window.ADCFlows.build(D, M) returns the model and the view factories;
   adc.html owns the markup, the CSS and the shared state {year, focus} that links the views.
   Colours are the site's CSS tokens only, so light and dark themes both work. */
(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  // SIPRI supplier names that differ from the V-Dem country names in D.countries (map position only).
  const SUP_ISO = {
    "United States": "USA", "Soviet Union": "RUS", "Czechoslovakia": "CZE", "Turkiye": "TUR",
    "Yugoslavia": "SRB", "East Germany (GDR)": "DEU", "Viet Nam": "VNM", "South Vietnam": "VNM",
    "Bosnia-Herzegovina": "BIH", "DR Congo": "COD", "North Yemen": "YEM", "South Yemen": "YEM",
    "Cote d'Ivoire": "CIV", "Brunei": "BRN", "Aruba": "ABW", "Bahamas": "BHS",
  };
  // Historical recipient codes drawn at today's country.
  const REC_ISO = { DDR: "DEU", VDR: "VNM", YMD: "YEM", SML: "SOM", ZZB: "TZA", PSG: "PSE" };
  // Small states with no shape on this map: hand-placed points in map coordinates (Equal Earth, 960 x 423).
  const EXTRA_PT = { SGP: [758.5, 229.2], BHR: [607.9, 139.1] };
  // Supplier colours (same tokens as the country page); everyone else is --s-x1.
  const COL = { "United States": "--s-usa", "Soviet Union": "--s-sov", "Russia": "--s-rus", "United Kingdom": "--s-uk", "France": "--s-fra", "Germany": "--s-ger", "China": "--s-chn" };
  // Fixed supplier order: legend, river bands (bottom up). Soviet Union and Russia stay separate.
  const LEGEND = ["United States", "Soviet Union", "Russia", "United Kingdom", "France", "Germany", "China"];
  const ORDER = LEGEND.concat(["Other"]);
  const SHORT = { "United States": "USA", "Soviet Union": "Soviet U.", "United Kingdom": "UK" };
  // Animation pace. ADCFlows.pace is the time factor set by the page: 1 = normal (1.5 s per year in Play),
  // 0.5 at 2x speed, 2 at 0.5x speed. Every duration below scales with it, so animations always fit inside a year.
  const pace = () => (window.ADCFlows && window.ADCFlows.pace) || 1;
  const YEAR_MS = 1500;                                   // one year in Play at 1x
  const tween = () => 1000 * pace();                      // chord tween
  const ringMs = () => 1500 * pace();                     // impact ring at the recipient
  // draw-on of a new arc: one speed for every arc, set so that the longest possible arc (about the map width)
  // finishes within 85% of a year at the current pace
  const drawSpeed = (W) => (W * 1.1) / (0.85 * YEAR_MS * pace());

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmt = (v) => Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });
  const r1 = (v) => Math.round(v * 10) / 10;
  const pct = (x) => !(x > 0) ? "0%" : x < 0.005 ? "<1%" : Math.round(x * 100) + "%";
  const trunc = (s, n) => s.length > n ? s.slice(0, n - 1) + "…" : s;
  const lerp = (a, b, p) => a + (b - a) * p;
  const ease = (p) => p < 0.5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
  const hash = (s) => { let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return (h % 1000) / 1000; };
  const colOf = (n) => "var(" + (COL[n] || "--s-x1") + ")";
  // Non-state suppliers: unknown, rebel groups (*), international organisations (**).
  const nonState = (n) => /\*$/.test(n) || /^unknown/i.test(n);
  // Point on a quadratic Bézier q = [x0, y0, cx, cy, x1, y1] at parameter t (analytic, no getPointAtLength).
  const qpt = (q, t) => { const u = 1 - t; return [u * u * q[0] + 2 * u * t * q[2] + t * t * q[4], u * u * q[1] + 2 * u * t * q[3] + t * t * q[5]]; };
  function el(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  const anyIn = (set, test) => { for (const x of set) if (test(x)) return true; return false; };

  // Map point of a country: bbox centre of its largest ring (by area).
  function centroid(d) {
    let best = null, bestA = -1;
    for (const ring of d.split("M")) {
      const nums = ring.match(/-?\d+(?:\.\d+)?/g);
      if (!nums || nums.length < 6) continue;
      let a = 0, x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
      const n = nums.length >> 1;
      for (let i = 0; i < n; i++) {
        const x = +nums[2 * i], y = +nums[2 * i + 1];
        const j = (i + 1) % n, xn = +nums[2 * j], yn = +nums[2 * j + 1];
        a += x * yn - xn * y;
        if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      }
      a = Math.abs(a);
      if (a > bestA) { bestA = a; best = [(x0 + x1) / 2, (y0 + y1) / 2]; }
    }
    return best;
  }

  // A river <svg> with data-h="110" is drawn in pixels: viewBox = its rendered width x data-h, so text keeps its size
  // and the strip keeps one height at any width. Without data-h the fixed viewBoxes below are used.
  function pxSize(svg) {
    const h = +svg.getAttribute("data-h");
    if (!h) return null;
    const w = Math.round((svg.parentNode && svg.parentNode.clientWidth) || 0);
    return { W: w > 200 ? w : 960, H: h };
  }
  // Redraw a pixel-sized river when its width changes (also when it first becomes visible).
  function fitWidth(svg, redraw) {
    if (!svg.getAttribute("data-h") || !("ResizeObserver" in window)) return;
    let w = 0;
    new ResizeObserver(() => {
      const nw = Math.round(svg.parentNode.clientWidth || 0);
      if (nw > 200 && Math.abs(nw - w) > 2) { w = nw; redraw(); }
    }).observe(svg.parentNode);
  }

  // Click, drag and keyboard on a river <svg> set the year (shared by riverView and stackView).
  // geom() -> {W, L, Rm, n} in viewBox units (null before the first draw); cur() -> the year shown.
  // onYear(y, scrubbing); onTap(target) after a click without dragging.
  function yearScrub(svg, y0, y1, geom, cur, onYear, onTap) {
    let drag = null;
    const noSel = (e) => e.preventDefault();
    const yearAt = (cx) => {
      const G = geom(), r = svg.getBoundingClientRect(), vx = (cx - r.left) / (r.width || 1) * G.W;
      return y0 + Math.max(0, Math.min(G.n - 1, Math.round((vx - G.L) / (G.W - G.L - G.Rm) * (G.n - 1))));
    };
    svg.addEventListener("pointerdown", (e) => {
      if (e.button || !geom()) return;
      // no text selection anywhere on the page while scrubbing; this also skips the default focus, so focus by hand
      e.preventDefault();
      try { svg.focus({ preventScroll: true }); } catch (err) { /* ignore */ }
      drag = { x: e.clientX, t: e.target, moved: false };
      document.addEventListener("selectstart", noSel);
      try { svg.setPointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      const y = yearAt(e.clientX); if (y !== cur()) onYear(y, false);
    });
    svg.addEventListener("pointermove", (e) => {
      if (!drag) return;
      if (Math.abs(e.clientX - drag.x) > 4) drag.moved = true;
      const y = yearAt(e.clientX); if (y !== cur()) onYear(y, true);
    });
    const end = (e, cancel) => {
      if (!drag) return;
      const d = drag; drag = null;
      document.removeEventListener("selectstart", noSel);
      try { svg.releasePointerCapture(e.pointerId); } catch (err) { /* ignore */ }
      if (!cancel && !d.moved && onTap) onTap(d.t);
    };
    svg.addEventListener("pointerup", (e) => end(e, false));
    svg.addEventListener("pointercancel", (e) => end(e, true));
    svg.addEventListener("keydown", (e) => {
      const step = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -10, PageUp: 10 }[e.key];
      let y = null;
      if (step) y = Math.max(y0, Math.min(y1, cur() + step));
      else if (e.key === "Home") y = y0;
      else if (e.key === "End") y = y1;
      if (y == null) return;
      e.preventDefault();
      onYear(y, false);
    });
    return { dragging: () => !!drag, yearAt: yearAt };
  }

  // ---------------------------------------------------------------- stacked area over the years (river look)
  // Any yearly series on the river's frame: zero baseline, same size, axis, 1991 marker, playhead and scrubbing.
  // opts: {y0, y1, mode, onYear(y, scrubbing)}. Data via setData({keys: [{name, short, color}], rows: [[v per key] per year],
  //   yTitle, tick(v, compact), label(y, total, row, compact) -> playhead text, tip(j, y, v, total) -> tooltip lines}).
  function stackView(svg, opts) {
    const Y0 = opts.y0, Y1 = opts.y1;
    let mode = opts.mode || "wide", G = null, yr = Y0, dat = null;
    svg.textContent = "";
    const bandsG = el("g", { class: "rv-bands" }, svg), axG = el("g", { class: "rv-axis" }, svg), phG = el("g", { class: "rv-ph" }, svg);
    svg.setAttribute("tabindex", "0"); svg.setAttribute("role", "slider");
    svg.setAttribute("aria-valuemin", Y0); svg.setAttribute("aria-valuemax", Y1);
    const nice = (v) => {
      if (!(v > 0)) return 1;
      const m = Math.pow(10, Math.floor(Math.log10(v)));
      for (const f of [1, 2, 2.5, 5, 10]) if (f * m >= v * 0.999) return f * m;
      return 10 * m;
    };
    function draw() {
      if (!dat) return;
      const cmp = mode === "compact", px = pxSize(svg), W = px ? px.W : cmp ? 400 : 960, H = px ? px.H : cmp ? 170 : 160;
      const L = cmp ? 42 : 64, Rm = 12, T = H < 140 ? 22 : 26, B = H < 140 ? 18 : 20;
      svg.setAttribute("viewBox", "0 0 " + W + " " + H);
      const rows = dat.rows, n = rows.length, K = dat.keys;
      const tots = rows.map((r) => r.reduce((a, b) => a + b, 0));
      const max = nice(Math.max.apply(null, tots));
      const X = (i) => L + (W - L - Rm) * i / (n - 1), Yv = (v) => H - B - v / max * (H - B - T);
      G = { W: W, H: H, L: L, Rm: Rm, T: T, B: B, X: X, n: n, tots: tots };
      let ax = "";
      for (const v of [0, max / 2, max]) {
        const y = Yv(v).toFixed(1);
        ax += '<line class="grid" x1="' + L + '" x2="' + (W - Rm) + '" y1="' + y + '" y2="' + y + '"></line>' +
          '<text class="tick" x="' + (L - 5) + '" y="' + (+y + 4) + '" text-anchor="end">' + esc(dat.tick(v, cmp)) + "</text>";
      }
      ax += '<text class="tick rv-ytitle" transform="translate(11 ' + ((T + H - B) / 2) + ') rotate(-90)" text-anchor="middle">' + esc(dat.yTitle) + "</text>";
      const ticks = cmp ? [1950, 1991, 2025] : [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2025];
      for (const t of ticks) ax += '<text class="tick" x="' + X(t - Y0).toFixed(1) + '" y="' + (H - 5) + '" text-anchor="' + (t === Y0 ? "start" : t === Y1 ? "end" : "middle") + '">' + t + "</text>";
      let base = rows.map(() => 0), bands = "", labs = "";
      const placed = [];
      K.forEach((k, j) => {
        const upper = base.map((b, i) => b + (rows[i][j] || 0));
        let d = "M" + upper.map((v, i) => X(i).toFixed(1) + "," + Yv(v).toFixed(1)).join("L");
        for (let i = n - 1; i >= 0; i--) d += "L" + X(i).toFixed(1) + "," + Yv(base[i]).toFixed(1);
        bands += '<path class="rv-band" data-band="' + j + '" d="' + d + 'Z" style="fill: ' + k.color + '"></path>';
        // direct label at the band's thickest year, if it is thick enough
        let bi = 0, bt = 0;
        for (let i = 0; i < n; i++) { const th = (rows[i][j] || 0) / max * (H - B - T); if (th > bt) { bt = th; bi = i; } }
        if (bt >= (cmp ? 13 : 12)) {
          const name = cmp ? (k.short || k.name) : k.name, hw = name.length * 3.2 + 4;
          const x = Math.max(L + hw, Math.min(W - Rm - hw, X(bi))), ly = Yv(base[bi] + rows[bi][j] / 2);
          // skip a label that would collide with one already placed (thin bands stacked at the same year)
          if (!placed.some((p) => Math.abs(p.x - x) < p.hw + hw && Math.abs(p.y - ly) < 13)) {
            placed.push({ x: x, y: ly, hw: hw });
            labs += '<text class="rv-lab" x="' + x.toFixed(1) + '" y="' + ly.toFixed(1) + '" dy=".35em" text-anchor="middle">' + esc(name) + "</text>";
          }
        }
        base = upper;
      });
      bandsG.innerHTML = bands + labs;
      const x91 = X(1991 - Y0).toFixed(1);
      ax += '<line class="rv-1991" x1="' + x91 + '" x2="' + x91 + '" y1="' + (T - 2) + '" y2="' + (H - B) + '"></line>' +
        '<text class="rv-note" x="' + (+x91 + 4) + '" y="' + (T + 9) + '">Soviet Union ends (1991)</text>';
      axG.innerHTML = ax;
      phG.innerHTML = '<line class="rv-phl" x1="0" x2="0" y1="' + (T - 4) + '" y2="' + (H - B) + '"></line><text class="rv-pht" x="0" y="' + (T - 9) + '"></text>';
      api.year(yr);
    }
    const api = {
      year(y) {
        yr = y;
        if (!G) return;
        const i = y - Y0, x = G.X(i), t = G.tots[i] || 0, tx = phG.lastChild;
        phG.style.transform = "translate(" + x.toFixed(1) + "px, 0px)";
        tx.setAttribute("text-anchor", x < G.L + 90 ? "start" : x > G.W - G.Rm - 90 ? "end" : "middle");
        const tl = dat.label(y, t, dat.rows[i], mode === "compact");
        tx.textContent = tl;
        svg.setAttribute("aria-valuenow", y);
        svg.setAttribute("aria-valuetext", tl);
      },
      frame() { return false; },
      setMode(m) { if (m !== mode) { mode = m; draw(); } },
      setData(d) { dat = d; draw(); },
      // playhead glide, matched to the Play pace of the mode
      setPace(ms) { phG.style.transitionDuration = ms + "ms"; },
    };
    const bandOf = (t) => { const b = t && t.closest && t.closest("[data-band]"); return b ? +b.dataset.band : null; };
    const scr = yearScrub(svg, Y0, Y1, () => G, () => yr, (y, s) => { if (opts.onYear) opts.onYear(y, s); }, null);
    // tooltip of the band under the pointer, for the year under the pointer (set before the page's tooltip reads it)
    svg.addEventListener("pointermove", (e) => {
      const j = bandOf(e.target);
      if (j == null || !G || !dat) return;
      const y = scr.yearAt(e.clientX), i = y - Y0;
      e.target.closest("[data-band]").setAttribute("data-tip", dat.tip(j, y, dat.rows[i][j] || 0, G.tots[i] || 0).join("|"));
    });
    fitWidth(svg, () => draw());
    return api;
  }

  function build(D, M) {
    const C = D.countries, Y0 = D.y0, Y1 = D.y1;
    const byName = {};
    for (const iso in C) byName[C[iso].n] = iso;
    const ptCache = {};
    const point = (iso) => {
      if (!iso) return null;
      if (!(iso in ptCache)) ptCache[iso] = M.p[iso] ? centroid(M.p[iso]) : ((M.pts && M.pts[iso]) || EXTRA_PT[iso] || null);
      return ptCache[iso];
    };
    const supIso = (name) => nonState(name) ? null : (SUP_ISO[name] || byName[name] || null);
    const recMap = (r) => REC_ISO[r] || r;
    const rName = (iso) => (C[iso] ? C[iso].n : iso);

    // Per year: every delivery (supplier -> recipient), largest first, plus totals.
    const years = {};
    const names = new Set();
    let vmax = 0, tivAll = 0, tivDrawn = 0;
    for (const r in D.suppliers) {
      const rMap = recMap(r), to = point(rMap);
      for (const s of D.suppliers[r]) {
        names.add(s.s);
        const fromIso = supIso(s.s), from = point(fromIso);
        const drawable = !!(from && to && fromIso !== rMap);
        for (const [y, v] of s.y) {
          if (!(v > 0)) continue;
          const t = years[y] || (years[y] = { all: [], total: 0, sup: {}, rec: {}, imp: {}, impBy: {}, exp: {}, expBy: {} });
          t.all.push({ key: s.s + ">" + r, s: s.s, r: r, rMap: rMap, from: fromIso, v: v, y: +y, drawable: drawable, p0: from, p1: to });
          t.total += v; tivAll += v;
          t.rec[r] = (t.rec[r] || 0) + v;
          t.imp[rMap] = (t.imp[rMap] || 0) + v;
          if (!nonState(s.s)) { const ib = t.impBy[rMap] || (t.impBy[rMap] = {}); ib[s.s] = (ib[s.s] || 0) + v; }
          if (!nonState(s.s)) {
            t.sup[s.s] = (t.sup[s.s] || 0) + v;
            if (fromIso) {
              t.exp[fromIso] = (t.exp[fromIso] || 0) + v;
              const eb = t.expBy[fromIso] || (t.expBy[fromIso] = {});
              eb[s.s] = (eb[s.s] || 0) + v;
            }
          }
          if (drawable) { tivDrawn += v; if (v > vmax) vmax = v; }
        }
      }
    }
    for (const y in years) years[y].all.sort((a, b) => b.v - a.v);
    const OTHER_NAMES = [...names].filter((n) => !COL[n]);
    // Ribbon width: LINEAR in TIV against one fixed maximum over all years, 1-12 px.
    const width = (v) => 1 + 11 * Math.min(1, v / vmax);
    const top = (o) => { let k = null, m = 0; for (const x in o) if (o[x] > m) { m = o[x]; k = x; } return k ? [k, m] : null; };
    // Impact ring: AREA linear in TIV (radius on a sqrt scale), 3-24 px.
    const ringR = (v) => Math.max(3, 24 * Math.sqrt(Math.min(1, v / vmax)));
    // Country tint: main supplier of each map country over the 5 years up to y (state suppliers only).
    const tintCache = {};
    function tints(y) {
      if (tintCache[y]) return tintCache[y];
      const sum = {}, out = {};
      for (let k = y - 4; k <= y; k++) {
        const t = years[k]; if (!t) continue;
        for (const iso in t.impBy) { const o = sum[iso] || (sum[iso] = {}); for (const n in t.impBy[iso]) o[n] = (o[n] || 0) + t.impBy[iso][n]; }
      }
      for (const iso in sum) { const b = top(sum[iso]); if (b) out[iso] = b[0]; }
      return (tintCache[y] = out);
    }
    const catIdx = (n) => { const i = LEGEND.indexOf(n); return i < 0 ? LEGEND.length : i; };

    // Selections shared by all views: {key, label, sup(name) -> bool, rec(iso) -> bool}.
    const selSup = (members, label) => { const set = new Set(members); return { key: "s:" + label, label: label, sup: (n) => set.has(n) }; };
    const selRec = (members, label) => { const set = new Set(members); return { key: "r:" + label, label: label, rec: (r) => set.has(r) || set.has(recMap(r)) }; };
    const selIso = (iso) => ({ key: "c:" + iso, label: rName(iso), sup: (n) => supIso(n) === iso, rec: (r) => r === iso || recMap(r) === iso });
    const legendItems = () => LEGEND.map((n) => ({ name: n, color: colOf(n), sel: selSup([n], n) }))
      .concat([{ name: "Other suppliers", color: "var(--s-x1)", sel: selSup(OTHER_NAMES, "Other suppliers") }]);

    // Geometry of one arc (fixed for a pair): quadratic curve bending left of the travel direction,
    // plus a 24-segment arc-length table so the dots can move at one speed in px.
    const GEO = {};
    function geo(d) {
      let g = GEO[d.key];
      if (g) return g;
      const [x0, y0] = d.p0, [x1, y1] = d.p1;
      const dx = x1 - x0, dy = y1 - y0, dist = Math.hypot(dx, dy) || 1, h = 0.22 * dist;
      const cx = (x0 + x1) / 2 + (dy / dist) * h, cy = (y0 + y1) / 2 - (dx / dist) * h;
      const q = [x0, y0, cx, cy, x1, y1], cum = [0];
      let px = x0, py = y0;
      for (let i = 1; i <= 24; i++) { const [x, y] = qpt(q, i / 24); cum.push(cum[i - 1] + Math.hypot(x - px, y - py)); px = x; py = y; }
      g = { d: "M" + r1(x0) + "," + r1(y0) + "Q" + r1(cx) + "," + r1(cy) + " " + r1(x1) + "," + r1(y1), q: q, cum: cum, len: cum[24] || 1 };
      return (GEO[d.key] = g);
    }
    function tAt(g, dist) {
      const c = g.cum; let k = 0;
      while (k < 23 && c[k + 1] < dist) k++;
      return (k + (dist - c[k]) / ((c[k + 1] - c[k]) || 1)) / 24;
    }

    // ---------------------------------------------------------------- data scopes
    // scope(null): the whole world. scope(Set of ISO codes): deliveries where the recipient OR the supplier
    // is one of them (historical states count as their map country, e.g. Soviet Union as RUS).
    const scopes = {};
    function scope(filter) {
      const set = filter && filter.size ? filter : null;
      const id = set ? [...set].sort().join(" ") : "*";
      if (scopes[id]) return scopes[id];
      const inSet = (d) => !set || set.has(d.r) || set.has(d.rMap) || (d.from && set.has(d.from));
      const Ys = {}, supTot = new Map();
      for (let y = Y0; y <= Y1; y++) {
        const all = years[y] ? years[y].all.filter(inSet) : [];
        let tot = 0;
        for (const d of all) { tot += d.v; supTot.set(d.s, (supTot.get(d.s) || 0) + d.v); }
        Ys[y] = { all: all, tot: tot };
      }
      const topSup = [...supTot.keys()].filter((n) => !nonState(n)).sort((a, b) => supTot.get(b) - supTot.get(a));
      const chordMaxCache = {};
      const sc = {
        filter: set, y0: Y0, y1: Y1,
        deliveries: (y) => (Ys[y] ? Ys[y].all : []),
        total: (y) => (Ys[y] ? Ys[y].tot : 0),
        // the n largest deliveries of the year that can be drawn on the map
        pairs(y, n) {
          const out = [];
          for (const d of sc.deliveries(y)) if (d.drawable) { out.push(d); if (out.length >= n) break; }
          return out;
        },
        topSuppliers: (k) => topSup.slice(0, k),
        // Chord data of one year from ALL deliveries: ns fixed suppliers (top over the whole period) + Other,
        // the year's nr largest recipients + Other. Shares are of the year's total.
        chord(y, ns, nr) {
          const list = sc.deliveries(y), tot = sc.total(y);
          const sups = topSup.slice(0, ns), sI = new Map(sups.map((n, i) => [n, i]));
          const rt = new Map();
          for (const d of list) rt.set(d.r, (rt.get(d.r) || 0) + d.v);
          const recs = [...rt.keys()].sort((a, b) => rt.get(b) - rt.get(a) || (a < b ? -1 : 1)).slice(0, nr);
          const rI = new Map(recs.map((r, i) => [r, i]));
          const S = sups.map((n, i) => ({ id: "s:" + n, name: n, label: SHORT[n] || n, color: COL[n] ? colOf(n) : "var(--s-x2)", slot: i, members: new Set([n]), v: 0 }));
          S.push({ id: "s:~", name: "Other suppliers", label: "Other", other: true, color: "var(--s-x1)", slot: sups.length, members: new Set(), v: 0 });
          const R = recs.map((r, i) => ({ id: "r:" + r, iso: r, name: rName(r), slot: i, members: new Set([r]), v: 0 }));
          R.push({ id: "r:~", name: "Other recipients", other: true, slot: nr, members: new Set(), v: 0 });
          const L = new Map();
          for (const d of list) {
            const si = sI.has(d.s) ? sI.get(d.s) : S.length - 1, ri = rI.has(d.r) ? rI.get(d.r) : R.length - 1;
            S[si].v += d.v; R[ri].v += d.v; S[si].members.add(d.s); R[ri].members.add(d.r);
            const k = si + "|" + ri;
            if (!L.has(k)) L.set(k, { si: si, ri: ri, v: 0 });
            L.get(k).v += d.v;
          }
          const links = [...L.values()];
          for (const x of S.concat(R, links)) x.share = tot ? x.v / tot : 0;
          return { year: y, tot: tot, S: S, R: R, links: links };
        },
        // Largest share each chord slot ever reaches, so the ring can keep fixed slots for all years.
        chordMax(ns, nr) {
          const k = ns + "|" + nr;
          if (chordMaxCache[k]) return chordMaxCache[k];
          const s = new Array(Math.min(ns, topSup.length) + 1).fill(0), r = new Array(nr + 1).fill(0);
          for (let y = Y0; y <= Y1; y++) {
            const ch = sc.chord(y, ns, nr);
            ch.S.forEach((x) => { s[x.slot] = Math.max(s[x.slot], x.share); });
            ch.R.forEach((x) => { r[x.slot] = Math.max(r[x.slot], x.share); });
          }
          return (chordMaxCache[k] = { s: s, r: r });
        },
        // River data: yearly TIV per supplier band (ORDER), Y0..Y1. dir "imp": recipient in the filter,
        // "exp": supplier in the filter (ignored for the world). world: the world total of each year.
        stream(dir) {
          const rows = [], world = [];
          for (let y = Y0; y <= Y1; y++) {
            const row = new Array(ORDER.length).fill(0);
            for (const d of (years[y] ? years[y].all : [])) {
              if (set && (dir === "exp" ? !(d.from && set.has(d.from)) : !(set.has(d.r) || set.has(d.rMap)))) continue;
              row[catIdx(d.s)] += d.v;
            }
            rows.push(row); world.push(years[y] ? years[y].total : 0);
          }
          return { keys: ORDER, rows: rows, world: world };
        },
      };
      return (scopes[id] = sc);
    }

    // ---------------------------------------------------------------- view 1: map ribbons (calm)
    // g: an SVG <g> inside a map in M's coordinates. Every pair keeps one <path>; width and opacity change by a
    // slow CSS transition. A pair that appears (or comes back after a gap) draws itself from supplier to recipient
    // at one on-screen speed, then its recipient sends out ONE soft ring. Nothing loops.
    // opts: {onHover(sel), onPick(sel)}.
    function mapAnim(g, sc, opts) {
      opts = opts || {};
      const arcsG = el("g", { class: "flx-arcs" }, g), ringsG = el("g", { class: "flx-rings" }, g);
      const items = new Map();
      let n = 25, sel = null;
      function apply() {
        for (const it of items.values()) {
          if (!it.on) continue;
          const d = it.d;
          it.p.classList.toggle("dim", !!sel && !((sel.sup && sel.sup(d.s)) || (sel.rec && sel.rec(d.r))));
        }
      }
      function clearDraw(it) {
        clearTimeout(it.tm);
        const st = it.p.style;
        st.transition = ""; st.strokeDasharray = ""; st.strokeDashoffset = "";
      }
      function ring(d, delay) {
        const c = el("circle", { class: "flx-ring", cx: r1(d.p1[0]), cy: r1(d.p1[1]), r: ringR(d.v).toFixed(1) }, ringsG);
        c.style.stroke = colOf(d.s); c.style.fill = colOf(d.s); c.style.animationDelay = delay + "ms";
        c.style.animationDuration = ringMs() + "ms";
        setTimeout(() => c.remove(), delay + ringMs() + 100);
      }
      const api = {
        year(y, instant) {
          const list = sc.pairs(y, n), tot = sc.total(y), now = new Set(), draw = [];
          for (const d of list) {
            now.add(d.key);
            let it = items.get(d.key);
            if (!it) {
              const G = geo(d), p = el("path", { d: G.d, class: "flx-arc off" }, arcsG);
              p.style.stroke = colOf(d.s); p.style.strokeWidth = "0"; p.style.opacity = "0";
              p.dataset.s = d.s;
              it = { p: p, G: G, on: false, tm: 0 };
              items.set(d.key, it);
            }
            it.d = d;
            if (!it.on && !instant) draw.push(it);
          }
          if (instant) {
            g.classList.add("flx-snap");
            ringsG.textContent = "";
          }
          // arcs that appear: start fully hidden by the dash, at their final width
          for (const it of draw) {
            const L = (it.G.len * 1.03 + 2).toFixed(1), st = it.p.style;
            clearDraw(it);
            st.transition = "none"; st.strokeDasharray = L + " " + L; st.strokeDashoffset = L;
            st.strokeWidth = width(it.d.v).toFixed(2); st.opacity = ".55";
          }
          if (draw.length) g.getBoundingClientRect();
          for (const it of draw) {
            const ms = Math.round(it.G.len / drawSpeed(M.w)), st = it.p.style, tr = Math.round(1200 * pace()) + "ms ease-in-out";
            st.transition = "stroke-dashoffset " + ms + "ms linear, stroke-width " + tr + ", opacity " + tr;
            st.strokeDashoffset = "0";
            it.tm = setTimeout(() => clearDraw(it), ms + 60);
            ring(it.d, ms);
          }
          for (const [k, it] of items) {
            const on = now.has(k);
            if (on) {
              const d = it.d;
              it.p.style.strokeWidth = width(d.v).toFixed(2);
              it.p.style.opacity = ".55";
              it.p.classList.remove("off");
              it.p.setAttribute("data-tip", d.s + " → " + rName(d.r) + "|" + y + "|" + fmt(d.v) + " TIV (" + pct(tot ? d.v / tot : 0) + " of the year)");
            } else if (it.on) {
              clearDraw(it);
              it.p.style.strokeWidth = "0"; it.p.style.opacity = "0";
              it.p.classList.add("off"); it.p.classList.remove("dim");
              it.p.removeAttribute("data-tip");
            }
            it.on = on;
          }
          if (instant) { g.getBoundingClientRect(); g.classList.remove("flx-snap"); }
          apply();
          const drawn = list.reduce((a, d) => a + d.v, 0);
          return { shown: list.length, count: sc.deliveries(y).length, share: tot ? drawn / tot : 0 };
        },
        setN(k) { n = k; }, // takes effect with the next year() call
        highlight(s) { sel = s; apply(); },
        frame() { return false; }, // nothing loops on the map
      };
      arcsG.addEventListener("pointerover", (e) => { const p = e.target.closest(".flx-arc"); if (p && opts.onHover) opts.onHover(selSup([p.dataset.s], p.dataset.s)); });
      arcsG.addEventListener("pointerout", (e) => { if (opts.onHover && !(e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest(".flx-arc"))) opts.onHover(null); });
      arcsG.addEventListener("click", (e) => { const p = e.target.closest(".flx-arc"); if (p && opts.onPick) { e.stopPropagation(); opts.onPick(selSup([p.dataset.s], p.dataset.s)); } });
      return api;
    }

    // ---------------------------------------------------------------- view 2: chord ring
    // Suppliers on the left half in FIXED slots, the year's top recipients on the right half (rank order).
    // Node size and ribbon width are linear in the share of the year's TIV; endpoints are tweened in JS.
    // opts: {mode: "wide" | "square" | "compact", onHover(sel), onPick(sel)}.
    function chordView(svg, sc, opts) {
      opts = opts || {};
      const ribG = el("g", { class: "ch-ribs" }, svg), nodeG = el("g", { class: "ch-nodes" }, svg);
      const empty = el("text", { class: "ch-empty", "text-anchor": "middle" }, svg);
      let mode = opts.mode || "wide", G = null, data = null, sel = null, tw = null, yr = null;
      const curN = new Map(), curL = new Map(), nodeEl = new Map(), ribEl = new Map(), info = new Map();

      function setup() {
        let W = mode === "wide" ? 500 : mode === "square" ? 440 : 340, H = mode === "wide" ? 400 : W;
        const ns = mode === "compact" ? 5 : 6, nr = mode === "compact" ? 6 : 8;
        let R = mode === "wide" ? 128 : mode === "square" ? 124 : 104, cx = W / 2;
        // data-px: drawn in pixels (viewBox = rendered size) so the 11 px labels are not scaled down; the ring sits
        // left of centre because recipient names (right) are longer than supplier labels (left).
        const pw = svg.hasAttribute("data-px") && svg.parentNode ? Math.round(svg.parentNode.clientWidth) : 0;
        if (pw > 200) {
          const ph = Math.round(svg.parentNode.clientHeight), supW = 70, recW = mode === "wide" ? 104 : 84;
          W = pw; H = ph > 160 ? ph : Math.round(Math.min(420, W * 0.8));
          R = Math.max(56, Math.min((W - supW - recW) / 2 - 19, H / 2 - 28));
          cx = supW + 19 + R + Math.max(0, (W - supW - recW - 2 * (R + 19)) / 2);
        }
        svg.setAttribute("viewBox", "0 0 " + W + " " + H);
        const mx = sc.chordMax(ns, nr), g0 = 0.07 * Math.PI, span = Math.PI - 2 * g0, pad = 0.03;
        const slots = (m) => {
          m = m.map((x) => Math.max(x, 0.02));
          const sum = m.reduce((a, b) => a + b, 0), k = (span - pad * m.length) / sum;
          let u = pad / 2;
          return { k: k, c: m.map((x) => { const c = u + x * k / 2; u += x * k + pad; return c; }) };
        };
        const Ls = slots(mx.s), Rs = slots(mx.r);
        G = { W: W, H: H, cx: cx, cy: H / 2, R: R, ns: ns, nr: nr, A: Math.min(Ls.k, Rs.k), sc: Ls.c, rc: Rs.c, g0: g0 };
        ribG.innerHTML = ""; nodeG.innerHTML = "";
        curN.clear(); curL.clear(); nodeEl.clear(); ribEl.clear(); info.clear(); tw = null;
        empty.setAttribute("x", G.cx); empty.setAttribute("y", G.cy);
      }
      const ang = (side, u) => side ? -Math.PI / 2 + G.g0 + u : 1.5 * Math.PI - G.g0 - u; // side 1 = right
      const pt = (side, u, rad) => { const a = ang(side, u); return [G.cx + rad * Math.cos(a), G.cy + rad * Math.sin(a)]; };
      const P = (p) => p[0].toFixed(1) + "," + p[1].toFixed(1);
      // Ring segment (annulus sector) of a node.
      function segD(side, u0, u1) {
        const r0 = G.R + 3, r2 = G.R + 13, sw = side ? 1 : 0, bw = side ? 0 : 1;
        const a = pt(side, u0, r0), b = pt(side, u1, r0), c = pt(side, u1, r2), d = pt(side, u0, r2);
        return "M" + P(a) + "A" + r0 + "," + r0 + " 0 0 " + sw + " " + P(b) + "L" + P(c) + "A" + r2 + "," + r2 + " 0 0 " + bw + " " + P(d) + "Z";
      }
      // Ribbon between a supplier sub-arc [s0, s1] (left) and a recipient sub-arc [r0, r1] (right).
      function ribD(v) {
        const R = G.R, c = G.cx + "," + G.cy;
        const s0 = pt(0, v[0], R), s1 = pt(0, v[1], R), q0 = pt(1, v[2], R), q1 = pt(1, v[3], R);
        return "M" + P(s0) + "A" + R + "," + R + " 0 0 0 " + P(s1) + "Q" + c + " " + P(q1) + "A" + R + "," + R + " 0 0 0 " + P(q0) + "Q" + c + " " + P(s0) + "Z";
      }
      function nodeElement(id, side) {
        let e = nodeEl.get(id);
        if (e) return e;
        const g = el("g", { class: "ch-node" + (side ? " ch-rec" : " ch-sup"), "data-cid": id }, nodeG);
        e = { g: g, seg: el("path", { class: "ch-seg" }, g), lab: el("text", { class: "ch-lab", dy: ".35em", "text-anchor": side ? "start" : "end" }, g), side: side };
        nodeEl.set(id, e);
        return e;
      }
      // Push labels of one side apart vertically (min. 14 px) so neighbours never overlap.
      function spread(a) {
        const gap = 14, live = a.filter((l) => l.e.textContent && !l.e.parentNode.classList.contains("out")).sort((u, v) => u.y - v.y);
        for (let i = 1; i < live.length; i++) if (live[i].y < live[i - 1].y + gap) live[i].y = live[i - 1].y + gap;
        for (let i = live.length - 1; i >= 0; i--) live[i].y = Math.min(live[i].y, i === live.length - 1 ? G.H - 8 : live[i + 1].y - gap);
        for (const l of live) l.e.setAttribute("y", l.y.toFixed(1));
      }
      function spreadAll() {
        const labs = [[], []];
        for (const ne of nodeEl.values()) if (ne.ly != null) labs[ne.side].push({ e: ne.lab, y: ne.ly });
        spread(labs[0]); spread(labs[1]);
      }
      function render(p) {
        const e = ease(p);
        for (const [id, t] of tw.N) {
          const v = [lerp(t.from[0], t.to[0], e), lerp(t.from[1], t.to[1], e)];
          curN.set(id, v);
          const ne = nodeElement(id, t.side);
          ne.seg.setAttribute("d", segD(t.side, v[0], v[1]));
          const mid = t.side || t.slot < 0 ? (v[0] + v[1]) / 2 : G.sc[t.slot];
          const lp = pt(t.side, mid, G.R + 19);
          ne.lab.setAttribute("x", lp[0].toFixed(1)); ne.lab.setAttribute("y", lp[1].toFixed(1));
          ne.ly = lp[1];
        }
        spreadAll();
        for (const [k, t] of tw.L) {
          const v = t.from.map((x, i) => lerp(x, t.to[i], e));
          curL.set(k, v);
          let r = ribEl.get(k);
          if (!r) { r = el("path", { class: "ch-rib", "data-cid": k }, ribG); ribEl.set(k, r); }
          r.setAttribute("d", ribD(v));
        }
        if (p >= 1) {
          for (const id of tw.deadN) { const ne = nodeEl.get(id); if (ne) ne.g.remove(); nodeEl.delete(id); curN.delete(id); }
          for (const k of tw.deadL) { const r = ribEl.get(k); if (r) r.remove(); ribEl.delete(k); curL.delete(k); }
          tw = null;
        }
      }
      function apply() {
        const sup = sel && sel.sup, rec = sel && sel.rec, on = new Set();
        if (data && sel) {
          for (const l of data.links) {
            const S = data.S[l.si], R = data.R[l.ri];
            if ((sup && anyIn(S.members, sup)) || (rec && anyIn(R.members, rec))) { on.add(S.id + "|" + R.id); on.add(S.id); on.add(R.id); }
          }
          for (const S of data.S) if (sup && anyIn(S.members, sup)) on.add(S.id);
          for (const R of data.R) if (rec && anyIn(R.members, rec)) on.add(R.id);
        }
        for (const [id, ne] of nodeEl) ne.g.classList.toggle("dim", !!sel && !on.has(id));
        for (const [k, r] of ribEl) r.classList.toggle("dim", !!sel && !on.has(k));
      }
      function selOf(id) {
        const x = info.get(id);
        if (!x) return null;
        if (x.kind === "link") return selOf(x.sup);
        return x.kind === "s" ? selSup([...x.n.members], x.n.name) : selRec([...x.n.members], x.n.name);
      }
      const api = {
        year(y, instant) {
          yr = y;
          const ch = sc.chord(y, G.ns, G.nr), A = G.A;
          data = ch; info.clear();
          const N = new Map(), Lk = new Map();
          // node targets
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
            ks.sort((a, b) => Lk.get(a).l.ri - Lk.get(b).l.ri);
            let u = N.get(ch.S[si].id).to[0];
            for (const k of ks) { const t = Lk.get(k), w = t.l.share * A; t.to[0] = u; t.to[1] = u + w; u += w; }
          }
          for (const [ri, ks] of byR) {
            ks.sort((a, b) => Lk.get(a).l.si - Lk.get(b).l.si);
            let u = N.get(ch.R[ri].id).to[0];
            for (const k of ks) { const t = Lk.get(k), w = t.l.share * A; t.to[2] = u; t.to[3] = u + w; u += w; }
          }
          // tween from where things are now; new ones grow from their centre, old ones shrink to theirs
          const TN = new Map(), TL = new Map(), deadN = [], deadL = [];
          for (const [id, t] of N) {
            const m = (t.to[0] + t.to[1]) / 2;
            TN.set(id, { side: t.side, slot: t.slot, from: curN.get(id) || [m, m], to: t.to });
          }
          for (const [id, v] of curN) if (!N.has(id)) {
            const m = (v[0] + v[1]) / 2;
            TN.set(id, { side: id[0] === "r" ? 1 : 0, slot: -1, from: v, to: [m, m] }); deadN.push(id);
            const ne = nodeEl.get(id); if (ne) { ne.g.classList.add("out"); ne.g.removeAttribute("data-tip"); }
          }
          for (const [k, t] of Lk) {
            const ms = (t.to[0] + t.to[1]) / 2, mr = (t.to[2] + t.to[3]) / 2;
            TL.set(k, { from: curL.get(k) || [ms, ms, mr, mr], to: t.to });
          }
          for (const [k, v] of curL) if (!Lk.has(k)) {
            const ms = (v[0] + v[1]) / 2, mr = (v[2] + v[3]) / 2;
            TL.set(k, { from: v, to: [ms, ms, mr, mr] }); deadL.push(k);
            const r = ribEl.get(k); if (r) r.removeAttribute("data-tip");
          }
          tw = { t0: performance.now(), N: TN, L: TL, deadN: deadN, deadL: deadL };
          render(instant ? 1 : 0);
          // labels, colours, tooltips (once per year, not per frame)
          const yy = " · " + y + "|";
          for (const [id, t] of N) {
            const ne = nodeElement(id, t.side), x = t.n;
            ne.g.classList.remove("out");
            info.set(id, { kind: t.side ? "r" : "s", n: x });
            ne.seg.style.fill = t.side ? (x.other ? "var(--s-oth)" : "var(--muted)") : x.color;
            ne.lab.textContent = t.side ? trunc(x.name, mode === "wide" ? 18 : 14) : x.label + " " + pct(x.share);
            const tip = x.name + yy + fmt(x.v) + " TIV, " + pct(x.share) + " of the year" +
              (x.other && x.members.size ? "|" + x.members.size + (t.side ? " countries" : " suppliers") : "");
            ne.g.setAttribute("data-tip", tip);
          }
          for (const [k, t] of Lk) {
            const l = t.l, S = ch.S[l.si], R = ch.R[l.ri], r = ribEl.get(k);
            info.set(k, { kind: "link", sup: S.id });
            r.style.fill = S.color;
            r.setAttribute("data-tip", S.name + " → " + R.name + yy + fmt(l.v) + " TIV, " + pct(l.share) + " of the year");
          }
          spreadAll(); // new labels got their text only now
          empty.textContent = ch.tot ? "" : "No deliveries in " + y;
          apply();
        },
        frame(t) { if (tw) render(Math.max(0, Math.min(1, (t - tw.t0) / tween()))); return !!tw; }, // true while tweening
        highlight(s) { sel = s; apply(); },
        setMode(m) { if (m === mode && G) return; mode = m; setup(); svg.classList.toggle("ch-compact", m === "compact"); if (yr != null) api.year(yr, true); },
      };
      setup(); svg.classList.toggle("ch-compact", mode === "compact");
      if (svg.hasAttribute("data-px") && "ResizeObserver" in window) {
        let sz = "";
        new ResizeObserver(() => {
          const p = svg.parentNode, k = p.clientWidth + "x" + p.clientHeight;
          if (k === sz || !p.clientWidth) return;
          sz = k; setup(); if (yr != null) api.year(yr, true);
        }).observe(svg.parentNode);
      }
      svg.addEventListener("pointerover", (e) => { const x = e.target.closest("[data-cid]"); if (x && opts.onHover) opts.onHover(selOf(x.dataset.cid)); });
      svg.addEventListener("pointerleave", () => { if (opts.onHover) opts.onHover(null); });
      svg.addEventListener("click", (e) => {
        const x = e.target.closest("[data-cid]");
        if (x && mode === "compact") { const n = x.closest(".ch-node"); if (n) n.classList.toggle("show"); }
        if (opts.onPick) opts.onPick(x ? selOf(x.dataset.cid) : null);
      });
      return api;
    }

    // ---------------------------------------------------------------- view 3: river of time
    // Stacked area of yearly TIV per supplier (fixed order, zero baseline), playhead synced to the year.
    // opts: {mode, dir, onYear(y, scrubbing), onHover(sel), onPick(sel)}.
    function riverView(svg, sc, opts) {
      opts = opts || {};
      let mode = opts.mode || "wide", share = false, dir = opts.dir || "imp", G = null, yr = Y0, sel = null;
      const bandsG = el("g", { class: "rv-bands" }, svg), axG = el("g", { class: "rv-axis" }, svg), phG = el("g", { class: "rv-ph" }, svg);
      svg.setAttribute("tabindex", "0"); svg.setAttribute("role", "slider");
      svg.setAttribute("aria-valuemin", Y0); svg.setAttribute("aria-valuemax", Y1);
      const bandSel = (k) => k < LEGEND.length ? selSup([LEGEND[k]], LEGEND[k]) : selSup(OTHER_NAMES, "Other suppliers");
      const nice = (v) => {
        if (!(v > 0)) return 1;
        if (share && v > 0.5) return 1;
        const m = Math.pow(10, Math.floor(Math.log10(v)));
        for (const f of [1, 2, 2.5, 5, 10]) if (f * m >= v * 0.999) return f * m;
        return 10 * m;
      };
      const tickLab = (v) => share ? Math.round(v * 100) + "%" : mode === "compact" && v >= 1000 ? fmt(v / 1000) + "k" : fmt(v);
      function draw() {
        const cmp = mode === "compact", px = pxSize(svg), W = px ? px.W : cmp ? 400 : 960, H = px ? px.H : cmp ? 170 : 160;
        const L = cmp ? 42 : 64, Rm = 12, T = H < 140 ? 22 : 26, B = H < 140 ? 18 : 20;
        svg.setAttribute("viewBox", "0 0 " + W + " " + H);
        const st = sc.stream(dir), n = st.rows.length;
        const vals = st.rows.map((row, i) => share ? row.map((v) => (st.world[i] ? v / st.world[i] : 0)) : row);
        const tots = vals.map((r) => r.reduce((a, b) => a + b, 0));
        const max = nice(Math.max.apply(null, tots));
        const X = (i) => L + (W - L - Rm) * i / (n - 1), Yv = (v) => H - B - v / max * (H - B - T);
        G = { W: W, H: H, L: L, Rm: Rm, T: T, B: B, X: X, n: n, tots: tots };
        let ax = "";
        for (const v of [0, max / 2, max]) {
          const y = Yv(v).toFixed(1);
          ax += '<line class="grid" x1="' + L + '" x2="' + (W - Rm) + '" y1="' + y + '" y2="' + y + '"></line>' +
            '<text class="tick" x="' + (L - 5) + '" y="' + (+y + 4) + '" text-anchor="end">' + tickLab(v) + "</text>";
        }
        ax += '<text class="tick rv-ytitle" transform="translate(11 ' + ((T + H - B) / 2) + ') rotate(-90)" text-anchor="middle">' + (share ? "Share of world" : "TIV (millions)") + "</text>";
        const ticks = cmp ? [1950, 1991, 2025] : [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2025];
        for (const t of ticks) ax += '<text class="tick" x="' + X(t - Y0).toFixed(1) + '" y="' + (H - 5) + '" text-anchor="' + (t === Y0 ? "start" : t === Y1 ? "end" : "middle") + '">' + t + "</text>";
        // bands, bottom up
        let base = vals.map(() => 0), bands = "", labs = "";
        ORDER.forEach((k, j) => {
          const upper = base.map((b, i) => b + vals[i][j]);
          let d = "M" + upper.map((v, i) => X(i).toFixed(1) + "," + Yv(v).toFixed(1)).join("L");
          for (let i = n - 1; i >= 0; i--) d += "L" + X(i).toFixed(1) + "," + Yv(base[i]).toFixed(1);
          const lb = k === "Other" ? "Other suppliers" : k;
          bands += '<path class="rv-band" data-band="' + j + '" d="' + d + 'Z" style="fill: ' + (k === "Other" ? "var(--s-x1)" : colOf(k)) + '" data-tip="' + esc(lb + "|Click to highlight it in all views|Click or drag to change the year") + '"></path>';
          // direct label at the band's thickest year, if it is wide enough
          let bi = 0, bt = 0;
          for (let i = 0; i < n; i++) { const th = (vals[i][j]) / max * (H - B - T); if (th > bt) { bt = th; bi = i; } }
          if (bt >= (cmp ? 13 : 12)) {
            const name = cmp || k === "Other" ? (k === "Other" ? "Other" : SHORT[k] || k) : k;
            const x = Math.max(L + 34, Math.min(W - Rm - 34, X(bi)));
            labs += '<text class="rv-lab" x="' + x.toFixed(1) + '" y="' + Yv(base[bi] + vals[bi][j] / 2).toFixed(1) + '" dy=".35em" text-anchor="middle">' + esc(name) + "</text>";
          }
          base = upper;
        });
        bandsG.innerHTML = bands + labs;
        const x91 = X(1991 - Y0).toFixed(1);
        ax += '<line class="rv-1991" x1="' + x91 + '" x2="' + x91 + '" y1="' + (T - 2) + '" y2="' + (H - B) + '"></line>' +
          '<text class="rv-note" x="' + (+x91 + 4) + '" y="' + (T + 9) + '">Soviet Union ends (1991)</text>';
        axG.innerHTML = ax;
        phG.innerHTML = '<line class="rv-phl" x1="0" x2="0" y1="' + (T - 4) + '" y2="' + (H - B) + '"></line><text class="rv-pht" x="0" y="' + (T - 9) + '"></text>';
        apply(); api.year(yr);
      }
      function apply() {
        bandsG.querySelectorAll(".rv-band").forEach((p) => {
          const k = +p.dataset.band, mem = k < LEGEND.length ? [LEGEND[k]] : OTHER_NAMES;
          p.classList.toggle("dim", !!(sel && sel.sup) && !mem.some(sel.sup));
        });
      }
      const api = {
        year(y) {
          yr = y;
          if (!G) return;
          const i = y - Y0, x = G.X(i), t = G.tots[i] || 0;
          const tx = phG.lastChild;
          phG.style.transform = "translate(" + x.toFixed(1) + "px, 0px)";
          tx.setAttribute("text-anchor", x < G.L + 70 ? "start" : x > G.W - G.Rm - 70 ? "end" : "middle");
          const tl = share ? pct(t) + " of world" : fmt(t) + " TIV";
          tx.textContent = y + " · " + tl;
          svg.setAttribute("aria-valuenow", y);
          svg.setAttribute("aria-valuetext", y + ", " + tl);
        },
        frame() { return false; },
        highlight(s) { sel = s; apply(); },
        setMode(m) { if (m !== mode) { mode = m; draw(); } },
        setShare(b) { share = !!b; draw(); },
        setDir(d) { dir = d; draw(); },
      };
      // click or drag sets the year; a click without dragging also locks (band) or clears (empty) the focus
      const bandOf = (t) => { const b = t && t.closest && t.closest("[data-band]"); return b ? +b.dataset.band : null; };
      const scr = yearScrub(svg, Y0, Y1, () => G, () => yr, (y, s) => { if (opts.onYear) opts.onYear(y, s); },
        (t) => { if (opts.onPick) { const b = bandOf(t); opts.onPick(b == null ? null : bandSel(b)); } });
      svg.addEventListener("pointerover", (e) => { if (scr.dragging()) return; const b = bandOf(e.target); if (opts.onHover) opts.onHover(b == null ? null : bandSel(b)); });
      svg.addEventListener("pointerleave", () => { if (!scr.dragging() && opts.onHover) opts.onHover(null); });
      fitWidth(svg, () => draw());
      draw();
      return api;
    }

    const world = scope(null);
    return {
      y0: Y0, y1: Y1, LEGEND: LEGEND, ORDER: ORDER,
      scope: scope, pairs: world.pairs, chord: world.chord, stream: world.stream,
      mapAnim: mapAnim, chordView: chordView, riverView: riverView,
      selSup: selSup, selRec: selRec, selIso: selIso, legendItems: legendItems,
      color: colOf, supIso: supIso, rName: rName, pct: pct, tints: tints,
      stats(year) {
        const t = years[year];
        if (!t) return { total: 0, transfers: 0, topSupplier: null, topRecipient: null };
        return { total: t.total, transfers: t.all.length, topSupplier: top(t.sup), topRecipient: top(t.rec) };
      },
      // Imports and exports of the country at map position iso (historical states folded in).
      country(year, iso) {
        const t = years[year];
        if (!t) return { imp: 0, exp: 0, as: [] };
        const eb = t.expBy[iso] || {};
        return { imp: t.imp[iso] || 0, exp: t.exp[iso] || 0, as: Object.keys(eb) };
      },
      share: tivAll ? tivDrawn / tivAll : 0, // part of all TIV that can be drawn on this map
    };
  }

  window.ADCFlows = { build: build, stackView: stackView, pace: 1 };
})();
