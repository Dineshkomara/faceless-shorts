// Inside Out engine: canvas, palette, math and drawing primitives.
// Every drawing function in the kit uses the shared `ctx` exported here (set once by main.js).
export const W = 1080, H = 1920, FPS = 30;
export let ctx = null;
export function setCtx(c) { ctx = c; }

// The style sheet palette. Only these (plus the derived shades) appear on screen.
export const C = {
  skin: '#E8B89A', pink: '#E57A8A', red: '#D62839', cyan: '#4FD1E8', yellow: '#FFD43B', bg: '#F4F1EA',
  // derived shades (darker / lighter tones of the palette, used for flat shading)
  pinkLight: '#F29AA7', pinkDark: '#C9566E', skinShade: '#D49C7E', navy: '#0E1A2B', xnavy: '#0B2238',
  hair: '#3B2A20', hairHi: '#5A4030', shirt: '#3A7BD5', shirtShade: '#2F67BE', pants: '#1F2A44', pantsShade: '#18213A',
  ink: '#1A1A1E', mouth: '#6B2A2A', gum: '#F7F4EE', gumEdge: '#C9C2B5', white: '#FFFFFF',
  stomachBg: '#B83A55', stomachBgDark: '#A3304A', stomachFold: '#D4637C', floor: '#E4DCCB', sky: '#BFE3F2',
  leaf: '#5BAE6A', pot: '#C8734A', watch: '#1E2A44',
};

// ---------- math ----------
export const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const seg = (t, a, b) => clamp((t - a) / ((b - a) || 1e-6));
export const eo = (t) => 1 - Math.pow(1 - t, 3);
export const eio = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const eob = (t) => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); };
export const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
export const TAU = Math.PI * 2;

// ---------- primitives ----------
export function rr(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

/** engagement CTA chip — the retention-safe ask: on-screen text (no voice) in the last ~3 s,
 *  above the caption zone and clear of the right rail. a = 0..1 presence, e.g.
 *  cta('Red or yellow?', eob(seg(lt, 0, 0.3))) in the final shot. Keep visible ≥ 1 s. */
export function cta(text, a, y = 330) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = Math.min(1, a); ctx.letterSpacing = '0px';
  ctx.font = '800 56px Inter'; ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
  const w = ctx.measureText(text).width + 76, h = 100;
  rr(540 - w / 2, y - h / 2, w, h, h / 2);
  ctx.fillStyle = 'rgba(12,12,18,0.68)'; ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.32)'; ctx.lineWidth = 4; ctx.stroke();
  ctx.fillStyle = '#FFFFFF'; ctx.fillText(text, 540, y + 2); ctx.restore();
}

export function circle(x, y, r, fill) { ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fillStyle = fill; ctx.fill(); }
export function ell(x, y, rx, ry, fill, rot = 0) { ctx.beginPath(); ctx.ellipse(x, y, rx, ry, rot, 0, TAU); ctx.fillStyle = fill; ctx.fill(); }
export function line(pts, color, w) {
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
}
export function fillAll(color) { ctx.fillStyle = color; ctx.fillRect(-300, -300, W + 600, H + 600); }
/** outlined bold text (the caption look), centred at x, y */
export function bigText(text, x, y, size, fill = C.white, rot = 0, sc = 1) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc);
  ctx.font = `900 ${size}px Inter`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  ctx.lineWidth = size * 0.2; ctx.strokeStyle = C.ink; ctx.strokeText(text, 0, 0); ctx.fillStyle = fill; ctx.fillText(text, 0, 0);
  ctx.restore();
}

/** Draws B-roll media (image or canvas) with subtle Ken Burns zoom */
export function drawBroll(media, tProgress, zoom = 0.08, alpha = 1.0) {
  if (!media || !(media instanceof HTMLImageElement) || !media.complete || media.naturalWidth === 0) return;
  try {
    ctx.save(); ctx.globalAlpha = alpha;
    const sc = 1.0 + zoom * tProgress;
    ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.translate(-W / 2, -H / 2);
    ctx.drawImage(media, 0, 0, W, H);
    ctx.fillStyle = 'rgba(10, 15, 25, 0.35)';
    ctx.fillRect(0, 0, W, H);
    ctx.restore();
  } catch (_) {}
}

/** High-retention bottom progress bar (YouTube Shorts / TikTok retention booster) */
export function drawProgressBar(t, totalDur, color = C.yellow) {
  if (!totalDur || totalDur <= 0) return;
  const prog = clamp(t / totalDur);
  ctx.save();
  ctx.fillStyle = 'rgba(255, 255, 255, 0.16)';
  ctx.fillRect(0, H - 8, W, 8);
  const grad = ctx.createLinearGradient(0, 0, W * prog, 0);
  grad.addColorStop(0, color);
  grad.addColorStop(1, '#FFFFFF');
  ctx.fillStyle = grad;
  ctx.fillRect(0, H - 8, W * prog, 8);
  ctx.restore();
}

/** Atmospheric cinematic vignette and gentle floating particles (OpenMontage style) */
export function drawAtmosphere(t, count = 16, color = 'rgba(255, 212, 59, ') {
  ctx.save();
  // Cinematic Vignette
  const vig = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.75);
  vig.addColorStop(0, 'rgba(0,0,0,0)');
  vig.addColorStop(1, 'rgba(0,0,0,0.36)');
  ctx.fillStyle = vig; ctx.fillRect(0, 0, W, H);
  // Floating Particles
  for (let i = 0; i < count; i++) {
    const baseX = (rnd(i * 7 + 1) * 0.9 + 0.05) * W;
    const baseY = (rnd(i * 13 + 2) * 0.8 + 0.1) * H;
    const speed = 0.3 + rnd(i * 3 + 5) * 0.8;
    const phase = rnd(i * 11 + 3) * TAU;
    const sz = 2.5 + rnd(i * 17 + 4) * 4.5;
    const xOff = Math.sin(t * speed + phase) * 22;
    const yOff = Math.cos(t * speed * 0.7 + phase) * 16 - (t * 12) % (H * 0.8);
    const y = ((baseY + yOff) % H + H) % H, x = baseX + xOff;
    const pulse = 0.3 + 0.7 * Math.sin(t * 2.0 + phase) ** 2;
    ctx.beginPath(); ctx.arc(x, y, sz, 0, TAU);
    ctx.fillStyle = `${color}${0.45 * pulse})`;
    ctx.shadowColor = `${color}0.8)`; ctx.shadowBlur = sz * 2.5; ctx.fill();
  }
  ctx.restore();
}
