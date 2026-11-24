// Puranic deity iconography for the tall-tale toon characters.
//
// The toon renderer draws a plain round head + bean body. This module adds the features that make a deity
// instantly recognisable, in three layers around the head:
//   drawDeityBack  — behind the head  (Ganesha's ears, Shiva's jata bun + side locks, Hanuman's tail, extra arms)
//   drawDeityFront — over the face    (Ganesha's trunk + tusks, Shiva's third eye, jewellery, fangs, muzzle)
//   drawDeityTop   — above the head   (crowns, peacock feather, crescent moon)
//
// Usage:
//   import { deityLook } from './core/deity.js';
//   const ganesha = new Toon(deityLook('ganesha', { body: '#E8734A' }), { height: 1.75 });
//   look.deity = 'shiva'  // or set it directly on any look object
//
// Feature notes are in DEITIES.md next to this file. Everything is drawn from the canonical iconography
// (elephant head + broken tusk + modak for Ganesha; blue skin + third eye + crescent + snake + trishul for
// Shiva; chakra + conch + namam for Vishnu; peacock feather + flute for Krishna; muzzle + tail for Hanuman).
// Local copies so this module never participates in a circular import with toon.js.
const INK = '#1F1C33';
const TAU = Math.PI * 2;
function shadeOf(hex, k = 0.78) {
  const n = parseInt(hex.slice(1), 16), r = (n >> 16) & 255, gg = (n >> 8) & 255, b = n & 255;
  const f = (v) => Math.max(0, Math.min(255, Math.round(v * k)));
  return '#' + ((1 << 24) + (f(r) << 16) + (f(gg) << 8) + f(b)).toString(16).slice(1);
}

const LW = 9;

const ink = (g, w = LW) => { g.strokeStyle = INK; g.lineWidth = w; };

// ---------------------------------------------------------------- presets
// look = the ordinary toon look patch;  extra = deity-specific options.
export const DEITIES = {
  ganesha: {
    name: 'Ganesha / Ganapati / Vinayaka',
    look: { head: '#F6C79B', body: '#E8734A', pattern: 'plain', extra: [] },
    opts: { tilak: '#D8343F', crown: 'mukut', ears: true, trunk: true },
  },
  shiva: {
    name: 'Shiva / Mahadeva',
    look: { head: '#8FC7E8', body: '#8FC7E8', pattern: 'plain', extra: [] },
    opts: { thirdEye: true, jata: true, crescent: true, snake: true, tilak: '#FFFFFF', trishul: true },
  },
  vishnu: {
    name: 'Vishnu / Narayana',
    look: { head: '#7FA8DC', body: '#F2C230', pattern: 'plain', extra: [] },
    opts: { namam: true, crown: 'kirita', garland: true, arms4: true, props4: ['chakra', 'shankha'] },
  },
  krishna: {
    name: 'Krishna / Govinda',
    look: { head: '#7FB3E8', body: '#F2C230', pattern: 'plain', extra: [] },
    opts: { crown: 'kirita', feather: true, flute: true, necklace: true },
  },
  rama: {
    name: 'Rama',
    look: { head: '#7FB3E8', body: '#F2C230', pattern: 'plain', extra: [] },
    opts: { crown: 'kirita', tilak: '#D8343F', necklace: true, bow: true },
  },
  hanuman: {
    name: 'Hanuman',
    look: { head: '#F08A3C', body: '#E8734A', pattern: 'plain', extra: [] },
    opts: { muzzle: true, monkeyEars: true, tail: true, crown: 'simple', tilak: '#D8343F' },
  },
  parvati: {
    name: 'Parvati / Uma / Gauri',
    look: { head: '#F7D3B8', body: '#C8402F', pattern: 'plain', extra: [] },
    opts: { crown: 'devi', bindi: true, jewellery: true, noseRing: true },
  },
  lakshmi: {
    name: 'Lakshmi',
    look: { head: '#F8D9A8', body: '#C8402F', pattern: 'plain', extra: [] },
    opts: { crown: 'devi', bindi: true, jewellery: true, lotus: true },
  },
  saraswati: {
    name: 'Saraswati',
    look: { head: '#F8E2CC', body: '#F4F1E6', pattern: 'plain', extra: [] },
    opts: { crown: 'devi', bindi: true, jewellery: true },
  },
  durga: {
    name: 'Durga / Devi',
    look: { head: '#F7D3B8', body: '#B5372E', pattern: 'plain', extra: [] },
    opts: { crown: 'devi', bindi: true, jewellery: true, arms4: true, props4: ['trishul', 'chakra'] },
  },
  murugan: {
    name: 'Murugan / Kartikeya / Skanda',
    look: { head: '#F0B98A', body: '#D8343F', pattern: 'plain', extra: [] },
    opts: { crown: 'devi', vel: true, tilak: '#D8343F' },
  },
  asura: {
    name: 'Asura / Rakshasa / demon king',
    look: { head: '#C97B5A', body: '#8A4B33', pattern: 'plain', extra: ['mustache'] },
    opts: { fangs: true, crown: 'asura', angry: true },
  },
  rakshasa: {                       // alias, same look
    name: 'Rakshasa (alias of asura)',
    look: { head: '#C97B5A', body: '#8A4B33', pattern: 'plain', extra: ['mustache'] },
    opts: { fangs: true, crown: 'asura', angry: true },
  },
};

/** A ready-to-use toon look for a deity, with optional overrides (e.g. a different dhoti colour). */
export function deityLook(deity, patch = {}) {
  const D = DEITIES[deity];
  if (!D) return { ...patch };
  return { ...D.look, ...patch, deity, deityOpts: { ...D.opts, ...(patch.deityOpts || {}) } };
}

export const DEITY_NAMES = Object.keys(DEITIES);

// ---------------------------------------------------------------- helpers
function ellipse(g, x, y, rx, ry, rot = 0) { g.beginPath(); g.ellipse(x, y, rx, ry, rot, 0, TAU); }

function crownMukut(g, x, y, r) {                                 // Ganesha's three-pointed crown
  const w = r * 0.80, base = y - r * 0.86;
  g.fillStyle = '#F2C230'; ink(g);
  g.beginPath();
  g.moveTo(x - w, base);
  g.lineTo(x - w * 0.72, base - r * 0.34);
  g.lineTo(x - w * 0.40, base - r * 0.10);
  g.lineTo(x, base - r * 0.52);
  g.lineTo(x + w * 0.40, base - r * 0.10);
  g.lineTo(x + w * 0.72, base - r * 0.34);
  g.lineTo(x + w, base);
  g.closePath(); g.fill(); g.stroke();
  g.fillStyle = shadeOf('#F2C230', 0.78);
  g.beginPath(); g.roundRect(x - w, base - r * 0.04, w * 2, r * 0.20, 8); g.fill(); g.stroke();
  g.fillStyle = '#D8343F'; ellipse(g, x, base + r * 0.06, r * 0.10, r * 0.08); g.fill(); g.stroke();
  g.fillStyle = '#7FBF7A';                                        // little lotus buds on the points
  [[-w * 0.72, base - r * 0.40], [0, base - r * 0.58], [w * 0.72, base - r * 0.40]].forEach(([bx, by]) => {
    ellipse(g, x + bx, by, r * 0.08, r * 0.05); g.fill(); ink(g, 4); g.stroke();
  });
}

function crownKirita(g, x, y, r) {                                // tall Vishnu/Krishna crown
  const base = y - r * 0.78;
  g.fillStyle = '#F2C230'; ink(g);
  g.beginPath();
  g.moveTo(x - r * 0.52, base);
  g.quadraticCurveTo(x - r * 0.60, base - r * 0.46, x, base - r * 0.64);
  g.quadraticCurveTo(x + r * 0.60, base - r * 0.46, x + r * 0.52, base);
  g.closePath(); g.fill(); g.stroke();
  g.fillStyle = shadeOf('#F2C230', 0.8);
  g.fillRect(x - r * 0.52, base - r * 0.12, r * 1.04, r * 0.16); ink(g, 5); g.strokeRect(x - r * 0.52, base - r * 0.12, r * 1.04, r * 0.16);
  g.fillStyle = '#2E8B57'; ellipse(g, x, base - r * 0.26, r * 0.11, r * 0.13); g.fill(); ink(g, 4); g.stroke();
  g.fillStyle = '#D8343F'; ellipse(g, x, base - r * 0.50, r * 0.07, r * 0.07); g.fill(); ink(g, 4); g.stroke();
}

function crownDevi(g, x, y, r) {                                  // smaller jewelled crown
  const base = y - r * 0.84;
  g.fillStyle = '#F2C230'; ink(g, 7);
  g.beginPath();
  g.moveTo(x - r * 0.50, base);
  g.lineTo(x - r * 0.34, base - r * 0.26);
  g.lineTo(x - r * 0.12, base - r * 0.12);
  g.lineTo(x, base - r * 0.34);
  g.lineTo(x + r * 0.12, base - r * 0.12);
  g.lineTo(x + r * 0.34, base - r * 0.26);
  g.lineTo(x + r * 0.50, base);
  g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#D8343F'; ellipse(g, x, base - r * 0.04, r * 0.07, r * 0.06); g.fill(); ink(g, 3); g.stroke();
}

function crownAsura(g, x, y, r) {                                 // spiked demon crown
  const base = y - r * 0.78;
  g.fillStyle = '#3A2A22'; ink(g);
  g.beginPath();
  g.moveTo(x - r * 0.62, base);
  g.lineTo(x - r * 0.50, base - r * 0.30);
  g.lineTo(x - r * 0.34, base - r * 0.08);
  g.lineTo(x - r * 0.18, base - r * 0.40);
  g.lineTo(x, base - r * 0.12);
  g.lineTo(x + r * 0.18, base - r * 0.40);
  g.lineTo(x + r * 0.34, base - r * 0.08);
  g.lineTo(x + r * 0.50, base - r * 0.30);
  g.lineTo(x + r * 0.62, base);
  g.closePath(); g.fill(); g.stroke();
  g.fillStyle = '#C8402F'; ellipse(g, x, base - r * 0.01, r * 0.08, r * 0.06); g.fill(); ink(g, 4); g.stroke();
}

function featherPeacock(g, x, y, r) {                             // Krishna's peacock feather
  g.save(); g.translate(x + r * 0.44, y - r * 0.80); g.rotate(0.30);
  ink(g, 6);
  g.strokeStyle = '#2E8B57'; g.lineWidth = 7;
  g.beginPath(); g.moveTo(0, r * 0.52); g.quadraticCurveTo(-r * 0.06, r * 0.10, 0, -r * 0.22); g.stroke();
  const cols = ['#2E8B57', '#1F6F8B', '#2E5FA3', '#1B3B6F'];
  cols.forEach((c, i) => {
    g.fillStyle = c; g.strokeStyle = INK; g.lineWidth = 4;
    ellipse(g, 0, -r * 0.26 - i * 2, r * (0.18 - i * 0.032), r * (0.25 - i * 0.045)); g.fill(); g.stroke();
  });
  g.fillStyle = '#F2C230'; ellipse(g, 0, -r * 0.36, r * 0.06, r * 0.08); g.fill(); ink(g, 3); g.stroke();
  g.restore();
}

// ---------------------------------------------------------------- BACK layer
export function drawDeityBack(g, L, S, geo) {
  const { hx, hy, r, bx, top, bot, bw } = geo;
  const o = L.deityOpts || {};
  const head = L.head || '#F7F7FA';
  g.save();

  // --- Ganesha's ears (the single most recognisable feature) ---
  if (o.ears || L.deity === 'ganesha') {
    [-1, 1].forEach((s) => {
      const cx = hx + s * r * 1.00, cy = hy + r * 0.12;
      g.fillStyle = head; ink(g);
      ellipse(g, cx, cy, r * 0.62, r * 0.84, s * 0.10); g.fill(); g.stroke();
      g.fillStyle = shadeOf(head, 0.88);
      ellipse(g, cx + s * r * 0.08, cy + r * 0.08, r * 0.36, r * 0.56, s * 0.10); g.fill();
      g.strokeStyle = shadeOf(head, 0.62); g.lineWidth = 4; g.stroke();
      g.strokeStyle = INK; g.lineWidth = 5;
      g.beginPath(); g.moveTo(cx + s * r * 0.10, cy - r * 0.42);
      g.quadraticCurveTo(cx - s * r * 0.22, cy, cx + s * r * 0.06, cy + r * 0.40); g.stroke();
    });
  }

  // --- Hanuman's tail: a big curl behind the body ---
  if (o.tail) {
    ink(g, 22); g.strokeStyle = INK;
    g.beginPath(); g.moveTo(bx + bw * 0.85, bot - 60);
    g.bezierCurveTo(bx + bw + 150, bot - 30, bx + bw + 190, bot - 300, bx + bw + 80, bot - 360);
    g.stroke();
    g.strokeStyle = L.body; g.lineWidth = 13; g.stroke();
    g.fillStyle = L.body; ellipse(g, bx + bw + 74, bot - 368, 22, 22); g.fill(); ink(g, 6); g.stroke();
  }

  // --- Shiva's jata: matted bun + locks falling at the sides ---
  if (o.jata) {
    g.fillStyle = '#4E3E33'; ink(g);
    ellipse(g, hx, hy - r * 1.02, r * 0.60, r * 0.46, 0, TAU); g.fill(); g.stroke();
    for (let i = -2; i <= 2; i++) {                                // matted strands over the bun
      g.strokeStyle = shadeOf('#4E3E33', 1.35); g.lineWidth = 7;
      g.beginPath();
      g.moveTo(hx + i * r * 0.20, hy - r * 0.62);
      g.quadraticCurveTo(hx + i * r * 0.30 + r * 0.10, hy - r * 1.06, hx + i * r * 0.16, hy - r * 1.44);
      g.stroke();
    }
    [-1, 1].forEach((s) => {                                       // side locks
      g.fillStyle = '#4E3E33'; ink(g);
      g.beginPath();
      g.moveTo(hx + s * r * 0.86, hy - r * 0.40);
      g.quadraticCurveTo(hx + s * r * 1.22, hy + r * 0.30, hx + s * r * 1.10, hy + r * 0.74);
      g.quadraticCurveTo(hx + s * r * 0.98, hy + r * 0.40, hx + s * r * 0.80, hy + r * 0.10);
      g.closePath(); g.fill(); g.stroke();
    });
    // crescent moon nested in the locks
    g.fillStyle = '#F6F1E0'; ink(g, 6);
    g.beginPath();
    g.arc(hx + r * 0.30, hy - r * 1.20, r * 0.20, Math.PI * 0.55, Math.PI * 1.85);
    g.arc(hx + r * 0.36, hy - r * 1.16, r * 0.16, Math.PI * 1.80, Math.PI * 0.60, true);
    g.closePath(); g.fill(); g.stroke();
    // a thin Ganga stream
    g.strokeStyle = '#BFE6F5'; g.lineWidth = 6;
    g.beginPath(); g.moveTo(hx - r * 0.10, hy - r * 1.42);
    g.quadraticCurveTo(hx - r * 0.46, hy - r * 1.10, hx - r * 0.40, hy - r * 0.86); g.stroke();
  }

  // --- Shiva's serpent: coils around the neck, hood raised at the shoulder ---
  if (o.snake) {
    const ny = top + 44;
    // two coils around the neck
    [[0, 0], [0, 22]].forEach(([, dy]) => {
      ink(g, 24); ellipse(g, bx, ny + dy, 68, 14); g.stroke();
      g.strokeStyle = '#5F8F6A'; g.lineWidth = 15; g.stroke();
    });
    // body draping down over the chest
    ink(g, 20);
    g.beginPath(); g.moveTo(bx + 66, ny + 16);
    g.bezierCurveTo(bx + 100, top + 100, bx + 60, top + 150, bx + 104, top + 196); g.stroke();
    g.strokeStyle = '#5F8F6A'; g.lineWidth = 12; g.stroke();
    // raised hood + head, left side
    const cx = bx - 98, cy = top + 50;
    ink(g, 18);
    g.beginPath(); g.moveTo(bx - 40, ny + 10); g.quadraticCurveTo(cx + 44, cy + 30, cx + 12, cy - 8); g.stroke();
    g.strokeStyle = '#5F8F6A'; g.lineWidth = 11; g.stroke();
    g.fillStyle = '#4F7F5C'; ink(g);
    g.beginPath(); g.moveTo(cx, cy + 40);
    g.bezierCurveTo(cx - 58, cy + 26, cx - 50, cy - 40, cx, cy - 52);
    g.bezierCurveTo(cx + 50, cy - 40, cx + 58, cy + 26, cx, cy + 34);
    g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#8FC7A0'; ellipse(g, cx, cy - 14, 17, 20); g.fill(); ink(g, 5); g.stroke();
    g.fillStyle = '#F6E7A8'; ellipse(g, cx - 8, cy - 22, 5, 5); g.fill();
    ellipse(g, cx + 8, cy - 22, 5, 5); g.fill();
    g.strokeStyle = '#D8343F'; g.lineWidth = 4; g.lineCap = 'round';
    g.beginPath(); g.moveTo(cx, cy + 8); g.lineTo(cx - 12, cy + 26);
    g.moveTo(cx, cy + 8); g.lineTo(cx + 12, cy + 26); g.stroke();
  }

  // --- four arms (Vishnu, Durga): the upper pair holds the deity's attributes ---
  if (o.arms4) {
    const props = o.props4 || ['chakra', 'shankha'];
    [-1, 1].forEach((s, i) => {
      const shx = bx + s * 58, shy = top + 40;
      const ex = bx + s * 140, ey = top - 10;
      const hx2 = bx + s * 150, hy2 = top + 62;
      g.lineCap = 'round';
      g.strokeStyle = INK; g.lineWidth = 21;
      g.beginPath(); g.moveTo(shx, shy); g.quadraticCurveTo(ex, ey, hx2, hy2); g.stroke();
      g.strokeStyle = L.head; g.lineWidth = 13; g.stroke();
      g.fillStyle = INK; ellipse(g, hx2, hy2, 14, 16); g.fill();
      const prop = PROPS_DEITY[props[i]];
      if (prop) { g.save(); prop(g, hx2, hy2, 0, s); g.restore(); }
    });
  }
  g.restore();
}

// ---------------------------------------------------------------- FRONT layer (over the face)
export function drawDeityFront(g, L, S, geo) {
  const { hx, hy, r, top } = geo;
  const o = L.deityOpts || {};
  const head = L.head || '#F7F7FA';
  g.save();

  // --- Ganesha: trunk hanging from under the mouth + one whole and one broken tusk ---
  if (o.trunk || L.deity === 'ganesha') {
    const t = new Path2D();
    t.moveTo(hx - 4, hy + r * 0.30);
    t.quadraticCurveTo(hx - 20, hy + r * 0.86, hx - 34, hy + r * 1.14);
    t.quadraticCurveTo(hx - 48, hy + r * 1.46, hx - 86, hy + r * 1.50);
    t.quadraticCurveTo(hx - 118, hy + r * 1.52, hx - 116, hy + r * 1.28);
    g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = INK; g.lineWidth = 44; g.stroke(t);
    g.strokeStyle = head; g.lineWidth = 28; g.stroke(t);
    g.fillStyle = head; ellipse(g, hx - 116, hy + r * 1.28, 17, 17); g.fill();
    ink(g, 6); g.stroke();
    // nostril flare at the base
    g.fillStyle = shadeOf(head, 0.80);
    ellipse(g, hx - 12, hy + r * 0.40, 11, 8); g.fill();
    // trunk wrinkles
    g.strokeStyle = shadeOf(head, 0.74); g.lineWidth = 5;
    for (let i = 0; i < 3; i++) {
      const yy = hy + r * (0.74 + i * 0.14);
      g.beginPath(); g.moveTo(hx - 20 - i * 10, yy);
      g.quadraticCurveTo(hx - 32 - i * 10, yy + 7, hx - 44 - i * 10, yy - 1); g.stroke();
    }
    // tusks: the right one broken (the classic asymmetry)
    [-1, 1].forEach((s) => {
      const x0 = hx + s * r * 0.30, y0 = hy + r * 0.74, len = s < 0 ? 1 : 0.55;
      g.fillStyle = '#FFFDF2'; ink(g, 7);
      g.beginPath();
      g.moveTo(x0 - 16, y0 + 8);
      g.quadraticCurveTo(x0 + s * r * 0.30, y0 + r * 0.10, x0 + s * r * 0.40 * len, y0 + r * 0.52 * len);
      g.quadraticCurveTo(x0 + s * r * 0.24, y0 + r * 0.30, x0 + 4, y0 - 6);
      g.closePath(); g.fill(); g.stroke();
    });
  }

  // --- Shiva: vertical third eye on the forehead ---
  if (o.thirdEye) {
    const cy = hy - r * 0.42;
    g.fillStyle = '#FFFDF6'; ink(g, 6);
    g.beginPath();
    g.moveTo(hx, cy - r * 0.16);
    g.quadraticCurveTo(hx + r * 0.16, cy, hx, cy + r * 0.16);
    g.quadraticCurveTo(hx - r * 0.16, cy, hx, cy - r * 0.16);
    g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#E0812B'; ellipse(g, hx, cy, r * 0.055, r * 0.11); g.fill();
    g.fillStyle = INK; ellipse(g, hx, cy, r * 0.018, r * 0.085); g.fill();
    // two thin ash lines either side
    g.strokeStyle = '#FFFDF6'; g.lineWidth = 5;
    [-1, 1].forEach((s) => { g.beginPath(); g.moveTo(hx + s * r * 0.26, cy - 4); g.lineTo(hx + s * r * 0.44, cy - 8); g.stroke(); });
  }

  // --- forehead marks ---
  if (o.tilak) {
    g.fillStyle = o.tilak;
    if (L.deity === 'shiva') {                                     // Shiva: three ash lines (vibhuti)
      g.fillStyle = '#FFFDF6';
      for (let i = 0; i < 3; i++) {
        const y = hy - r * 0.78 + i * 11;
        g.beginPath(); g.roundRect(hx - r * 0.30, y, r * 0.60, 5, 3); g.fill();
      }
    } else if (L.deity === 'hanuman') {
      g.beginPath(); g.roundRect(hx - r * 0.10, hy - r * 0.86, r * 0.20, r * 0.34, 5); g.fill();
    } else {
      g.beginPath(); g.roundRect(hx - r * 0.055, hy - r * 0.80, r * 0.11, r * 0.26, 4); g.fill();
      ellipse(g, hx, hy - r * 0.50, r * 0.035, r * 0.035); g.fill();
    }
  }
  if (o.namam) {                                                   // Vishnu's U-shaped namam
    g.strokeStyle = '#FFFDF6'; g.lineWidth = 9;
    g.beginPath(); g.moveTo(hx - r * 0.10, hy - r * 0.92); g.lineTo(hx - r * 0.10, hy - r * 0.56);
    g.quadraticCurveTo(hx, hy - r * 0.42, hx + r * 0.10, hy - r * 0.56); g.lineTo(hx + r * 0.10, hy - r * 0.92); g.stroke();
    g.strokeStyle = '#D8343F'; g.lineWidth = 4;
    g.beginPath(); g.moveTo(hx, hy - r * 0.86); g.lineTo(hx, hy - r * 0.50); g.stroke();
  }
  if (o.bindi) { g.fillStyle = '#C8202F'; ellipse(g, hx, hy - r * 0.56, r * 0.05, r * 0.06); g.fill(); }

  // --- Hanuman's muzzle ---
  if (o.muzzle) {
    g.fillStyle = shadeOf(head, 1.28); ink(g, 7);
    ellipse(g, hx, hy + r * 0.50, r * 0.46, r * 0.34); g.fill(); g.stroke();
    g.fillStyle = INK;
    ellipse(g, hx - r * 0.11, hy + r * 0.40, 5, 7); g.fill();
    ellipse(g, hx + r * 0.11, hy + r * 0.40, 5, 7); g.fill();
    g.strokeStyle = INK; g.lineWidth = 6;
    g.beginPath(); g.moveTo(hx - r * 0.16, hy + r * 0.58); g.quadraticCurveTo(hx, hy + r * 0.64, hx + r * 0.16, hy + r * 0.58); g.stroke();
  }
  if (o.monkeyEars) {
    [-1, 1].forEach((s) => {
      g.fillStyle = head; ink(g);
      ellipse(g, hx + s * r * 0.98, hy + r * 0.02, r * 0.22, r * 0.26); g.fill(); g.stroke();
      g.fillStyle = shadeOf(head, 1.25); ellipse(g, hx + s * r * 0.98, hy + r * 0.02, r * 0.12, r * 0.15); g.fill();
    });
  }

  // --- demon fangs ---
  if (o.fangs) {
    g.fillStyle = '#FFFDF2'; ink(g, 5);
    [-1, 1].forEach((s) => {
      const x = hx + s * r * 0.22, y = hy + r * 0.52;
      g.beginPath(); g.moveTo(x - r * 0.045, y); g.lineTo(x + r * 0.045, y); g.lineTo(x, y + r * 0.20); g.closePath();
      g.fill(); g.stroke();
    });
  }

  // --- jewellery (devis) ---
  if (o.jewellery) {
    const ny = top + 34;                                           // sits at the neck, never on the chin
    g.strokeStyle = '#F2C230'; g.lineWidth = 11; g.lineCap = 'round';
    g.beginPath(); g.arc(hx, ny - 34, 62, 0.30, Math.PI - 0.30); g.stroke();
    g.fillStyle = '#F2C230'; ink(g, 4);
    for (let i = -3; i <= 3; i++) {
      const a = Math.PI / 2 + i * 0.24;
      ellipse(g, hx + Math.cos(a) * 62, ny - 34 + Math.sin(a) * 62, r * 0.045, r * 0.045); g.fill(); g.stroke();
    }
    g.fillStyle = '#D8343F'; ellipse(g, hx, ny + 40, r * 0.07, r * 0.09); g.fill(); ink(g, 4); g.stroke();
    [-1, 1].forEach((s) => {                                      // earrings
      g.fillStyle = '#F2C230'; ellipse(g, hx + s * r * 0.96, hy + r * 0.46, r * 0.10, r * 0.16); g.fill(); ink(g, 5); g.stroke();
      g.fillStyle = '#D8343F'; ellipse(g, hx + s * r * 0.96, hy + r * 0.60, r * 0.055, r * 0.055); g.fill(); ink(g, 4); g.stroke();
    });
  }
  if (o.noseRing) {
    g.strokeStyle = '#F2C230'; g.lineWidth = 5;
    g.beginPath(); g.arc(hx - r * 0.16, hy + r * 0.30, r * 0.09, -0.3, Math.PI + 0.3); g.stroke();
  }
  if (o.necklace && !o.jewellery) {
    const ny2 = top + 30;
    g.strokeStyle = '#F2C230'; g.lineWidth = 9; g.lineCap = 'round';
    g.beginPath(); g.arc(hx, ny2 - 30, 56, 0.30, Math.PI - 0.30); g.stroke();
    g.fillStyle = '#F2C230'; ink(g, 4);
    ellipse(g, hx, ny2 + 26, r * 0.06, r * 0.07); g.fill(); g.stroke();
  }
  g.restore();
}

// ---------------------------------------------------------------- TOP layer (crowns / feathers)
export function drawDeityTop(g, L, S, geo) {
  const { hx, hy, r } = geo;
  const o = L.deityOpts || {};
  g.save();
  if (o.crown === 'mukut') crownMukut(g, hx, hy, r);
  else if (o.crown === 'kirita') crownKirita(g, hx, hy, r);
  else if (o.crown === 'devi') crownDevi(g, hx, hy, r);
  else if (o.crown === 'asura') crownAsura(g, hx, hy, r);
  else if (o.crown === 'simple') {
    g.fillStyle = '#F2C230'; ink(g, 7);
    g.beginPath(); g.roundRect(hx - r * 0.42, hy - r * 0.96, r * 0.84, r * 0.16, 6); g.fill(); g.stroke();
  }
  if (o.feather) featherPeacock(g, hx, hy, r);
  g.restore();
}

// ---------------------------------------------------------------- hand props
const PROPS_DEITY = {
  trishul: (g, x, y) => {                                          // three-pronged trident
    g.save(); g.translate(x - 26, y);
    ink(g, 14); g.strokeStyle = INK;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -268); g.stroke();
    g.strokeStyle = '#C9CFD8'; g.lineWidth = 8; g.stroke();
    const prong = (dx, bend) => {
      ink(g, 18); g.beginPath(); g.moveTo(0, -196);
      g.quadraticCurveTo(bend, -246, dx, -322); g.stroke();
      g.strokeStyle = '#C9CFD8'; g.lineWidth = 10; g.stroke();
      ink(g, 6); g.fillStyle = '#C9CFD8';
      g.beginPath(); g.moveTo(dx, -322); g.lineTo(dx - 9, -346); g.lineTo(dx + 9, -346); g.closePath(); g.fill(); g.stroke();
    };
    prong(-62, -70); prong(62, 70); prong(0, 0);
    g.fillStyle = '#F2C230'; ink(g, 5); ellipse(g, 0, -196, 18, 12); g.fill(); g.stroke();
    g.restore();
  },
  chakra: (g, x, y) => {                                           // Sudarshana discus
    g.save(); g.translate(x, y - 40);
    ink(g, 7); g.fillStyle = '#F2C230';
    g.beginPath(); g.arc(0, 0, 52, 0, TAU); g.fill(); g.stroke();
    g.fillStyle = '#E08A2B'; g.beginPath(); g.arc(0, 0, 38, 0, TAU); g.fill(); g.stroke();
    ink(g, 5); g.strokeStyle = '#FFF3C4';
    for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; g.beginPath(); g.moveTo(Math.cos(a) * 16, Math.sin(a) * 16); g.lineTo(Math.cos(a) * 48, Math.sin(a) * 48); g.stroke(); }
    g.fillStyle = '#F2C230'; ink(g, 4); g.beginPath(); g.arc(0, 0, 14, 0, TAU); g.fill(); g.stroke();
    g.restore();
  },
  shankha: (g, x, y) => {                                          // conch
    g.save(); g.translate(x, y - 34); g.rotate(-0.2);
    g.fillStyle = '#F6F1E0'; ink(g, 7);
    g.beginPath(); g.moveTo(0, -62); g.bezierCurveTo(46, -34, 40, 34, 0, 62); g.bezierCurveTo(-40, 34, -46, -34, 0, -62);
    g.closePath(); g.fill(); g.stroke();
    g.strokeStyle = '#C9B48A'; g.lineWidth = 5;
    g.beginPath(); g.moveTo(0, -40); g.quadraticCurveTo(22, 0, 0, 38); g.stroke();
    g.strokeStyle = INK; g.lineWidth = 6;
    g.beginPath(); g.moveTo(0, -62); g.lineTo(0, -84); g.stroke();
    g.restore();
  },
  gada: (g, x, y) => {                                             // mace
    g.save(); g.translate(x - 14, y);
    ink(g, 12); g.strokeStyle = INK;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -150); g.stroke();
    g.strokeStyle = '#B8862F'; g.lineWidth = 7; g.stroke();
    g.fillStyle = '#F2C230'; ink(g, 7);
    g.beginPath(); g.arc(0, -196, 42, 0, TAU); g.fill(); g.stroke();
    g.fillStyle = '#E08A2B'; g.beginPath(); g.arc(-11, -207, 14, 0, TAU); g.fill();
    g.restore();
  },
  vel: (g, x, y) => {                                              // Murugan's spear
    g.save(); g.translate(x - 26, y);
    ink(g, 12); g.strokeStyle = INK;
    g.beginPath(); g.moveTo(0, 0); g.lineTo(0, -300); g.stroke();
    g.strokeStyle = '#C9CFD8'; g.lineWidth = 7; g.stroke();
    g.fillStyle = '#EAF4FF'; ink(g, 7);
    g.beginPath(); g.moveTo(0, -420); g.quadraticCurveTo(30, -350, 0, -290); g.quadraticCurveTo(-30, -350, 0, -420);
    g.closePath(); g.fill(); g.stroke();
    g.fillStyle = '#F2C230'; ellipse(g, 0, -292, 16, 9); g.fill(); ink(g, 4); g.stroke();
    g.restore();
  },
  flute: (g, x, y) => {                                            // Krishna's bansuri
    g.save(); g.translate(x, y - 60); g.rotate(-0.35);
    ink(g, 8); g.fillStyle = '#C8935A';
    g.beginPath(); g.roundRect(-96, -10, 192, 20, 8); g.fill(); g.stroke();
    g.fillStyle = INK;
    [-52, -18, 16, 50].forEach((dx) => { g.beginPath(); g.arc(dx, 0, 5, 0, TAU); g.fill(); });
    g.fillStyle = '#F2C230'; g.fillRect(64, -12, 10, 24);
    g.restore();
  },
  lotus: (g, x, y) => {                                            // lotus bloom
    g.save(); g.translate(x, y - 50);
    ink(g, 6);
    for (let i = 0; i < 7; i++) {
      const a = -Math.PI * 0.9 + i * Math.PI * 0.30;
      g.fillStyle = i % 2 ? '#F29BB5' : '#F6B7C9';
      ellipse(g, Math.cos(a) * 30, Math.sin(a) * 30, 24, 34, a + Math.PI / 2); g.fill(); g.stroke();
    }
    g.fillStyle = '#F6C945'; ellipse(g, 0, 0, 18, 16); g.fill(); g.stroke();
    g.restore();
  },
  damaru: (g, x, y) => {                                           // hourglass drum
    g.save(); g.translate(x, y - 40);
    g.fillStyle = '#B5372E'; ink(g, 6);
    g.beginPath(); g.moveTo(-34, -46); g.lineTo(34, -46); g.lineTo(14, 0); g.lineTo(34, 46); g.lineTo(-34, 46); g.lineTo(-14, 0); g.closePath();
    g.fill(); g.stroke();
    g.fillStyle = '#F2E6CF'; ellipse(g, 0, -46, 34, 10); g.fill(); g.stroke();
    ellipse(g, 0, 46, 34, 10); g.fill(); g.stroke();
    g.restore();
  },
  modak: (g, x, y) => {                                            // sweet
    g.save(); g.translate(x, y - 30);
    g.fillStyle = '#F6E3A8'; ink(g, 5);
    g.beginPath(); g.moveTo(0, -34); g.quadraticCurveTo(34, -6, 22, 26); g.lineTo(-22, 26);
    g.quadraticCurveTo(-34, -6, 0, -34); g.closePath(); g.fill(); g.stroke();
    g.restore();
  },
  bow: (g, x, y) => {                                              // Rama's bow
    g.save(); g.translate(x, y - 120);
    g.strokeStyle = '#8A5A22'; g.lineWidth = 13; g.lineCap = 'round';
    g.beginPath(); g.arc(0, 0, 110, -1.15, 1.15); g.stroke();
    g.strokeStyle = '#F6F1E0'; g.lineWidth = 3;
    g.beginPath(); g.moveTo(Math.cos(-1.15) * 110, Math.sin(-1.15) * 110); g.lineTo(Math.cos(1.15) * 110, Math.sin(1.15) * 110); g.stroke();
    g.restore();
  },
};

// expose for holdL/holdR:  holdR: PROPS_DEITY.trishul
export { PROPS_DEITY };
