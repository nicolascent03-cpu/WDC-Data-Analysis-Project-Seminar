// Regimes world map (Streamlit custom component v2). Port of buildMap()/updateReg()/regTip() in app/site/adc.html.
// The shapes are built once per instance; a new year only changes fills (CSS transition) and the class of each
// country's stripe overlay (opacity transition), so Play never redraws the map and nothing flickers.
// Event back: setTriggerValue("select", iso3) on a click on a country.

const NS = "http://www.w3.org/2000/svg";
const INST = new WeakMap();
let UID = 0;

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fmt = (v, d) => Number(v).toLocaleString("en-US", { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
const CONFLICT = ["No armed conflict", "Minor armed conflict (25–999 deaths)", "War (1000+ deaths)"];
const NODATA = "#2a2a28";

function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}

// map anchor of a shape: centroid of its largest ring, plus its size (to decide on a hit circle)
function anchor(d) {
  let best = null, x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const sub of d.split("M").slice(1)) {
    const pts = [...sub.matchAll(/(-?[\d.]+),(-?[\d.]+)/g)].map((m) => [+m[1], +m[2]]);
    if (pts.length < 3) continue;
    let A = 0, cx = 0, cy = 0;
    pts.forEach(([xa, ya], i) => {
      const [xb, yb] = pts[(i + 1) % pts.length], c = xa * yb - xb * ya;
      A += c; cx += (xa + xb) * c; cy += (ya + yb) * c;
      x0 = Math.min(x0, xa); x1 = Math.max(x1, xa); y0 = Math.min(y0, ya); y1 = Math.max(y1, ya);
    });
    if (A && (!best || Math.abs(A) > Math.abs(best[0]))) best = [A, cx / (3 * A), cy / (3 * A)];
  }
  return { at: best ? [best[1], best[2]] : null, size: Math.max(x1 - x0, y1 - y0) };
}

function create(parentElement, data) {
  const root = parentElement.querySelector(".rm-root"), G = data.geo, uid = "rm" + (++UID);
  const svg = el("svg", { class: "rm-map", viewBox: "0 0 " + G.w + " " + G.h, role: "img", "aria-label": "World map of regime types" }, root);
  // stripes: the same rotated <pattern> as the HTML map, a denser and bolder one for war
  const defs = el("defs", {}, svg);
  const pat = (id, w, sw) => {
    const p = el("pattern", { id: id, width: w, height: w, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" }, defs);
    el("line", { x1: 0, y1: 0, x2: 0, y2: w, style: "stroke: var(--hatch); stroke-width: " + sw }, p);
  };
  pat(uid + "-minor", 6, 1.1);
  pat(uid + "-war", 3.4, 1.5);
  const shapesG = el("g", { class: "rm-shapes" }, svg), hatchG = el("g", { class: "rm-hatch" }, svg), dotsG = el("g", { class: "rm-dots" }, svg);
  const shapes = new Map(), hatch = new Map(), dots = new Map(), hits = [];
  for (const iso in G.p) {
    shapes.set(iso, el("path", { d: G.p[iso], "data-iso": iso }, shapesG));
    hatch.set(iso, el("path", { d: G.p[iso] }, hatchG));
    const a = anchor(G.p[iso]);
    if (a.at && a.size < 14) hits.push([iso, a.at, 7]);
  }
  for (const iso in G.pts) {
    if (G.p[iso]) continue;
    dots.set(iso, el("circle", { class: "pt", cx: G.pts[iso][0], cy: G.pts[iso][1], r: 3 }, dotsG));
    hits.push([iso, G.pts[iso], 8]);
  }
  for (const [iso, at, r] of hits) el("circle", { class: "hitc", "data-iso": iso, cx: at[0].toFixed(1), cy: at[1].toFixed(1), r: r }, dotsG);

  const legend = document.createElement("div");
  legend.className = "rm-legend";
  const tip = document.createElement("div");
  tip.className = "rm-tip"; tip.hidden = true;
  root.append(legend, tip);

  const S = { data: data, setTrigger: null, hover: null, lastEv: null, legendSig: "" };

  function tipHtml(iso) {
    const d = S.data, v = d.values[iso], y = d.year;
    if (!v) return "<b>No V-Dem data</b><div>No data for " + y + "</div>";
    const [r, idx, c, arms, name] = v;
    if (r == null) return "<b>" + esc(name) + " · " + y + "</b><div>No regime data for " + y + "</div>";
    return "<b>" + esc(name) + " · " + y + "</b><div>" + esc(d.regimes[r]) + (idx != null ? " · democracy index " + fmt(idx, 2) : "") + "</div>" +
      "<div>" + CONFLICT[c || 0] + "</div><div>Arms imports: " + fmt(arms || 0) + " TIV</div><div class=\"hint\">Click to show its details</div>";
  }
  function placeTip(ev) {
    const b = root.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
    let x = ev.clientX - b.left + 14, y = ev.clientY - b.top + 14;
    if (x + w > b.width) x = ev.clientX - b.left - w - 14;
    if (y + h > b.height) y = ev.clientY - b.top - h - 14;
    tip.style.left = Math.max(0, x) + "px"; tip.style.top = Math.max(0, y) + "px";
  }
  function showTip(ev) {
    const t = ev.target.closest && ev.target.closest("[data-iso]");
    S.hover = t ? t.dataset.iso : null; S.lastEv = ev;
    if (!S.hover) { tip.hidden = true; return; }
    tip.innerHTML = tipHtml(S.hover); tip.hidden = false; placeTip(ev);
  }
  svg.onpointermove = showTip;
  svg.onpointerleave = () => { S.hover = null; tip.hidden = true; };
  svg.onclick = (ev) => {
    const t = ev.target.closest && ev.target.closest("[data-iso]");
    if (t && S.data.values[t.dataset.iso] && S.setTrigger) S.setTrigger("select", t.dataset.iso);
  };

  function paint() {
    const d = S.data, cols = d.colours;
    const fillOf = (iso) => { const v = d.values[iso]; return v && v[0] != null ? cols[v[0]] : NODATA; };
    for (const [iso, p] of shapes) {
      p.style.fill = fillOf(iso);
      p.classList.toggle("sel", iso === d.selected);
      const v = d.values[iso], c = d.stripes && v && v[0] != null ? v[2] : 0;
      const h = hatch.get(iso), cls = c === 2 ? "war" : c === 1 ? "minor" : "";
      if (h.getAttribute("class") !== cls) {
        if (cls) h.setAttribute("fill", "url(#" + uid + "-" + cls + ")");
        h.setAttribute("class", cls);
      }
    }
    for (const [iso, c] of dots) c.style.fill = fillOf(iso);
    const sig = d.colours.join() + d.stripes;
    if (sig !== S.legendSig) {
      S.legendSig = sig;
      const sw = (cls) => '<svg viewBox="0 0 14 10"><rect width="14" height="10" fill="' + cols[3] + '"></rect><rect width="14" height="10" fill="url(#' + uid + "-" + cls + ')" opacity="' + (cls === "war" ? .95 : .6) + '"></rect></svg>';
      legend.innerHTML = d.regimes.map((r, i) => '<span><i style="background: ' + cols[i] + '"></i>' + esc(r) + "</span>").join("") +
        '<span><i style="background: ' + NODATA + '; outline: 1px solid #45443f"></i>No data</span>' +
        (d.stripes ? '<span class="note">' + sw("minor") + sw("war") + "striped = armed conflict (denser = war)</span>" : "");
    }
    // keep an open tooltip current when the year changes under a still pointer
    if (S.hover && !tip.hidden) tip.innerHTML = tipHtml(S.hover);
  }

  return {
    update(data, setTriggerValue) { S.data = data; S.setTrigger = setTriggerValue; paint(); },
    destroy() { root.innerHTML = ""; },
  };
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  if (!data || !data.geo) return;
  let inst = INST.get(parentElement);
  if (!inst) { inst = create(parentElement, data); INST.set(parentElement, inst); }
  inst.update(data, setTriggerValue);
  return () => { inst.destroy(); INST.delete(parentElement); };
}
