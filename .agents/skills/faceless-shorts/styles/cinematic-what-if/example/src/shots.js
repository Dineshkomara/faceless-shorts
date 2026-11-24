// Native 2D Canvas starter for Cinematic What If. Visible art is drawn with ctx;
// the shared WebGL bootstrap remains only to preserve the capture project's contract.
import { W, H, ctx, clamp, lerp, rnd } from './core/lib.js';
import { T, L } from './core/timing.js';

const ink = '#0e0b12', cream = '#f4efe6', rim = '#ffc68a';
const TAU = Math.PI * 2;
const V = (x, y) => ({ x, y });

function gradient(y0, y1, stops) {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  stops.forEach(([p, c]) => g.addColorStop(p, c));
  return g;
}
function fillRound(x, y, w, h, r, color) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fillStyle = color; ctx.fill();
}
function strokeLine(x1, y1, x2, y2, color, width) {
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
  ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.stroke();
}

function room(t, mode = 'home') {
  const warm = mode === 'home';
  const glowX = warm ? 795 : 480;
  ctx.fillStyle = gradient(0, H, warm
    ? [[0, '#241c29'], [0.58, '#332731'], [1, '#16131d']]
    : [[0, '#171b2b'], [0.58, '#242433'], [1, '#12131d']]);
  ctx.fillRect(0, 0, W, H);

  // Large, softly lit window with mullions: the recurring signature environment.
  const win = ctx.createRadialGradient(glowX, 580, 15, glowX, 580, 650);
  win.addColorStop(0, warm ? 'rgba(255,205,145,.86)' : 'rgba(193,207,255,.44)');
  win.addColorStop(1, warm ? 'rgba(226,153,112,.02)' : 'rgba(120,145,220,.01)');
  ctx.fillStyle = win; ctx.fillRect(250, 70, 830, 1050);
  fillRound(530, 165, 430, 680, 8, warm ? '#f4bb8b' : '#9aa9ce');
  ctx.fillStyle = warm ? '#f6c79b' : '#aebad5'; ctx.globalAlpha = 0.66;
  ctx.fillRect(546, 180, 398, 648); ctx.globalAlpha = 1;
  ctx.fillStyle = warm ? '#69515a' : '#31354c';
  for (let i = 0; i < 5; i++) {
    const x = 555 + i * 84;
    fillRound(x, 586 - (i % 2) * 25, 45, 244, 3, warm ? '#493947' : '#272b40');
  }
  ctx.fillStyle = 'rgba(37,29,42,.75)'; ctx.fillRect(530, 490, 430, 10); ctx.fillRect(530, 672, 430, 9);

  // Background shapes are broad and quiet; only a few kitchen props support the action.
  fillRound(35, 260, 280, 670, 12, '#211d2a');
  for (let i = 0; i < 3; i++) {
    fillRound(55, 390 + i * 154, 236, 12, 4, '#55414a');
    fillRound(84 + i * 65, 300 + i * 153, 48, 84, 10, i % 2 ? '#855b43' : '#524651');
  }
  const floor = gradient(1120, H, [[0, '#29232d'], [1, '#14131b']]);
  ctx.fillStyle = floor; ctx.fillRect(0, 1120, W, H - 1120);
  ctx.fillStyle = 'rgba(19,17,24,.86)'; ctx.fillRect(0, 1115, W, 18);
  // Countertop and bowl are flat graphic forms, not shaded 3D props.
  fillRound(110, 1030, 850, 130, 18, '#3b2c31');
  fillRound(0, 1155, W, 30, 0, '#795646');
  ctx.beginPath(); ctx.ellipse(665, 1038, 120, 32, 0, 0, TAU); ctx.fillStyle = '#a37051'; ctx.fill();
  ctx.beginPath(); ctx.ellipse(665, 1027, 110, 25, 0, 0, TAU); ctx.fillStyle = '#241e27'; ctx.fill();

  // A restrained practical light, never a broad floating-particle overlay.
  ctx.fillStyle = warm ? '#ffbf75' : '#cbd4ff';
  ctx.beginPath(); ctx.arc(190, 165, 28, 0, TAU); ctx.fill();
  const lamp = ctx.createRadialGradient(190, 165, 5, 190, 165, 270);
  lamp.addColorStop(0, warm ? 'rgba(255,191,117,.26)' : 'rgba(203,212,255,.18)');
  lamp.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = lamp; ctx.fillRect(0, 0, 480, 500);
  for (let i = 0; i < 6; i++) {
    const x = (rnd(i + 9) * 0.84 + 0.08) * W;
    const y = (rnd(i + 23) * 0.55 + 0.12) * H;
    const pulse = 0.28 + 0.24 * Math.sin(t * 0.7 + i);
    ctx.fillStyle = `rgba(255,214,169,${pulse})`;
    ctx.beginPath(); ctx.arc(x + Math.sin(t * 0.22 + i) * 5, y, 2, 0, TAU); ctx.fill();
  }
}

function face(headY, r, exp, t) {
  ctx.fillStyle = ink; ctx.beginPath(); ctx.arc(0, headY, r, 0, TAU); ctx.fill();
  // Lit-side crescent is always present, warm and narrow.
  ctx.beginPath(); ctx.arc(0, headY, r - 2, -1.18, 1.04);
  ctx.strokeStyle = rim; ctx.lineWidth = 5; ctx.globalAlpha = 0.93; ctx.stroke(); ctx.globalAlpha = 1;
  const eyeY = headY - 7;
  ctx.fillStyle = cream;
  const eyeScale = exp === 'surprised' ? 1.22 : 1;
  for (const ex of [-0.30, 0.30]) {
    ctx.beginPath(); ctx.arc(ex * r, eyeY, 8 * eyeScale, 0, TAU); ctx.fill();
  }
  if (exp === 'worried' || exp === 'surprised') {
    strokeLine(-0.45 * r, headY - 29, -0.16 * r, headY - 34, cream, 4);
    strokeLine(0.16 * r, headY - 34, 0.45 * r, headY - 29, cream, 4);
  }
  ctx.beginPath();
  if (exp === 'surprised') ctx.ellipse(0, headY + 27, 10, 15, 0, 0, TAU);
  else if (exp === 'smile') ctx.arc(0, headY + 10, 25, 0.16, Math.PI - 0.16);
  else if (exp === 'thinking') ctx.moveTo(-14, headY + 24), ctx.quadraticCurveTo(0, headY + 16, 14, headY + 22);
  else strokeLine(-13, headY + 24, 13, headY + 24, cream, 4);
  if (exp !== 'surprised') { ctx.strokeStyle = cream; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.stroke(); }
  // Deterministic blink at natural intervals.
  const blink = (t % 3.3) > 3.18;
  if (blink) for (const ex of [-0.30, 0.30]) strokeLine(ex * r - 6, eyeY, ex * r + 6, eyeY, ink, 4);
}

function character(x, floorY, scale, opts = {}, t = 0) {
  const jacket = opts.jacket || '#1e56a0', expression = opts.expression || 'neutral';
  const phase = t * (opts.running ? 8 : 2.4) + (opts.phase || 0);
  const sway = Math.sin(phase) * (opts.running ? 22 : 5) * scale;
  const headY = -278 * scale, headR = 66 * scale;
  ctx.save(); ctx.translate(x, floorY); ctx.scale(scale, scale);
  // Soft contact shadow grounds the feet.
  ctx.fillStyle = 'rgba(4,3,8,.48)'; ctx.beginPath(); ctx.ellipse(0, -3, 88, 17, 0, 0, TAU); ctx.fill();
  // Far-side limbs are subtly lighter for depth.
  strokeLine(-17, -102, -46 + sway, -8, '#2b2333', 13);
  strokeLine(17, -102, 45 - sway, -8, '#2b2333', 13);
  strokeLine(-31, -209, -72, -165 + Math.sin(phase) * 12, '#2b2333', 13);
  // Torso and the single signature garment.
  ctx.fillStyle = jacket;
  ctx.beginPath(); ctx.moveTo(-36, -223); ctx.quadraticCurveTo(0, -242, 36, -223);
  ctx.lineTo(48, -108); ctx.quadraticCurveTo(0, -88, -48, -108); ctx.closePath(); ctx.fill();
  // Near-side limbs: thick round caps, simple hand endpoints, no fingers.
  strokeLine(-8, -104, -41 + sway, -8, ink, 13);
  strokeLine(8, -104, 38 - sway, -8, ink, 13);
  strokeLine(31, -209, 77, -167 + Math.cos(phase) * 16, ink, 13);
  // Rounded arm ends read as hands without fingers.
  ctx.fillStyle = ink; for (const [hx, hy] of [[-41 + sway, -8], [38 - sway, -8], [77, -167 + Math.cos(phase) * 16]]) {
    ctx.beginPath(); ctx.arc(hx, hy, 8, 0, TAU); ctx.fill();
  }
  ctx.fillStyle = ink; ctx.beginPath(); ctx.ellipse(0, -239, 25, 18, 0, 0, TAU); ctx.fill();
  face(headY, headR, expression, t);
  if (opts.cap) {
    fillRound(-55, headY - headR + 4, 110, 18, 8, opts.cap);
    ctx.beginPath(); ctx.ellipse(16, headY - headR + 14, 44, 10, 0, 0, TAU); ctx.fillStyle = opts.cap; ctx.fill();
  }
  ctx.restore();
}

function cinematicFrame(t, scene, action) {
  ctx.save();
  const driftX = Math.sin(t * 0.11) * 8;
  const driftY = Math.cos(t * 0.09) * 5;
  const push = 1 + 0.012 * Math.sin(t * 0.13);
  ctx.translate(W / 2 + driftX, H / 2 + driftY); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
  room(t, scene);
  action();
  // Fine deterministic grain: subtle enough to disappear at normal phone size.
  for (let i = 0; i < 130; i++) {
    const x = rnd(i * 3 + 1) * W, y = rnd(i * 5 + 4) * H;
    ctx.fillStyle = i % 2 ? 'rgba(255,239,218,.022)' : 'rgba(4,3,10,.025)';
    ctx.fillRect(x, y, 2, 2);
  }
  ctx.restore();
  // Persistent restrained scope bars; captions remain clear inside the lower safe area.
  ctx.fillStyle = '#09080e'; ctx.fillRect(0, 0, W, 82); ctx.fillRect(0, H - 82, W, 82);
  const vignette = ctx.createRadialGradient(W / 2, H / 2, H * .28, W / 2, H / 2, H * .73);
  vignette.addColorStop(0, 'rgba(0,0,0,0)'); vignette.addColorStop(1, 'rgba(0,0,0,.29)');
  ctx.fillStyle = vignette; ctx.fillRect(0, 0, W, H);
}

export function buildShots() {
  const lines = T.lines || [];
  const at = (i) => lines[i] ? L(i) : (i * (T.dur || 18) / 4);
  const S = [];
  S.push({ id: 'W01_HOOK', at: 0, note: 'Wide hook: recognizable home, changing intention', draw(lt, d, t) {
    cinematicFrame(t, 'home', () => {
      character(525, 1230, 1.17, { jacket: '#1e56a0', expression: 'surprised' }, t);
      character(815, 1240, .80, { jacket: '#27ae60', cap: '#27ae60', expression: 'thinking', phase: 1 }, t);
      if (lt < 2.4) {
        ctx.textAlign = 'center'; ctx.font = '900 58px Fredoka, sans-serif'; ctx.fillStyle = cream;
        ctx.fillText('WHAT IF EVERY DOORWAY', W / 2, 224);
        ctx.fillText('MADE YOU FORGET?', W / 2, 294);
      }
    });
  }});
  S.push({ id: 'W02_CROSSING', at: at(1), note: 'Medium interaction: cross the threshold and lose the task', draw(lt, d, t) {
    cinematicFrame(t, 'home', () => {
      // The doorway is a large value-shape, not a stroked 3D frame.
      fillRound(365, 250, 410, 920, 16, '#17151f');
      fillRound(400, 286, 340, 835, 8, gradient(286, 1121, [[0, '#e8ae81'], [1, '#42313b']]));
      character(330 + Math.sin(lt * 1.1) * 30, 1240, 1.02, { jacket: '#1e56a0', expression: lt < d * .4 ? 'thinking' : 'confused', phase: 2 }, t);
      character(820, 1240, .77, { jacket: '#27ae60', cap: '#27ae60', expression: 'surprised', phase: 1 }, t);
      // A small amber intention-card fades as the lead crosses the threshold.
      const a = 1 - clamp(lt / Math.max(1, d)); ctx.globalAlpha = a;
      fillRound(600, 545, 140, 90, 18, '#e3ad6c');
      ctx.fillStyle = '#352633'; ctx.font = '900 26px Nunito, sans-serif'; ctx.textAlign = 'center'; ctx.fillText('KEYS', 670, 600);
      ctx.globalAlpha = 1;
    });
  }});
  S.push({ id: 'W03_BOUNDARY', at: at(2), note: 'Close detail: the room changes, intention loses priority', draw(lt, d, t) {
    cinematicFrame(t, 'mind', () => {
      // Blueprint-like event boundary links the physical doorway to a memory scene.
      ctx.strokeStyle = 'rgba(146,190,235,.72)'; ctx.lineWidth = 4; ctx.setLineDash([11, 15]);
      ctx.beginPath(); ctx.moveTo(540, 250); ctx.lineTo(540, 1210); ctx.stroke(); ctx.setLineDash([]);
      character(375, 1238, 1.05, { jacket: '#1e56a0', expression: 'thinking' }, t);
      character(750, 1238, .83, { jacket: '#27ae60', cap: '#27ae60', expression: 'smile', phase: 1 }, t);
      const pulse = .55 + .35 * Math.sin(lt * 2.2);
      ctx.globalAlpha = pulse; ctx.fillStyle = '#e9b872';
      ctx.beginPath(); ctx.arc(548, 590, 38 + 8 * Math.sin(lt * 2), 0, TAU); ctx.fill(); ctx.globalAlpha = 1;
      ctx.textAlign = 'center'; ctx.font = '900 30px Nunito, sans-serif'; ctx.fillStyle = cream;
      ctx.fillText('NEW SCENE', 540, 500);
    });
  }});
  S.push({ id: 'W04_PAYOFF', at: at(3), note: 'Payoff: a friend helps the intention return', draw(lt, d, t) {
    cinematicFrame(t, 'home', () => {
      character(435, 1235, 1.07, { jacket: '#1e56a0', expression: 'smile' }, t);
      character(730, 1235, .92, { jacket: '#27ae60', cap: '#27ae60', expression: 'smile', phase: 1 }, t);
      ctx.fillStyle = '#e3ad6c'; ctx.beginPath(); ctx.arc(580 + Math.sin(lt * 1.5) * 9, 995, 28, 0, TAU); ctx.fill();
      ctx.textAlign = 'center'; ctx.font = '900 30px Nunito, sans-serif'; ctx.fillStyle = cream;
      ctx.fillText('THE GOAL CAN RETURN', 540, 370);
    });
  }});
  return { shots: S, cues: [] };
}
