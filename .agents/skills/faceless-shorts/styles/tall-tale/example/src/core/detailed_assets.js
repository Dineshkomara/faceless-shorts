// High-Detail 3D Assets for Zack D. Films Benchmark Quality
// Provides realistic 3D vehicles, horseshoe marquee sign, agricultural wheat highway, and cockpit POV.
import * as THREE from 'three';
import { T, mat, canvasTex } from './world.js';
import { INK } from './toon.js';

const box = (w, h, d, m, x = 0, y = 0, z = 0, parent) => {
  const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  b.position.set(x, y, z);
  b.castShadow = b.receiveShadow = true;
  if (parent) parent.add(b);
  return b;
};

const cyl = (r1, r2, h, m, x, y, z, parent, seg = 20) => {
  const c = new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, seg), m);
  c.position.set(x, y, z);
  c.castShadow = c.receiveShadow = true;
  if (parent) parent.add(c);
  return c;
};

// ── Realistic Wheel with Rubber Tread & Chrome Dish Hubcap ──────────────────
export function buildRealisticWheel(radius = 0.42, width = 0.28, chrome = true) {
  const wg = new THREE.Group();
  const tireMat = new THREE.MeshStandardMaterial({ color: '#111317', roughness: 0.9, metalness: 0.1 });
  const rimMat = new THREE.MeshStandardMaterial({ color: chrome ? '#F8FAFC' : '#94A3B8', metalness: 0.85, roughness: 0.15 });
  const dishMat = new THREE.MeshStandardMaterial({ color: '#E2E8F0', metalness: 0.95, roughness: 0.1 });

  // Rubber Outer Tire with rounded shoulder
  const tire = cyl(radius, radius, width, tireMat, 0, 0, 0, wg, 24);
  tire.rotation.z = Math.PI / 2;

  // Steel Rim Hub
  const rim = cyl(radius * 0.68, radius * 0.68, width + 0.02, rimMat, 0, 0, 0, wg, 20);
  rim.rotation.z = Math.PI / 2;

  // Chrome Center Dish / Bullet Hubcap
  const dish = new THREE.Mesh(new THREE.SphereGeometry(radius * 0.38, 16, 12), dishMat);
  dish.scale.set(0.4, 1, 1);
  dish.rotation.z = Math.PI / 2;
  dish.position.x = width * 0.52;
  wg.add(dish);

  return wg;
}

// ── 1. Realistic Station Wagon / SUV (The Crashed Car) ───────────────────────
export function buildDetailedSUV({
  color = '#CBD5E1', // Silver/Grey as in reference frame_002
  damaged = false,
  headlights = true,
  taillights = true
} = {}) {
  const g = new THREE.Group();
  const W = 2.05, L = 4.8, H = 1.45;

  const bodyMat = new THREE.MeshStandardMaterial({ color, metalness: 0.65, roughness: 0.25 });
  const trimMat = new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.8 });
  const chromeMat = new THREE.MeshStandardMaterial({ color: '#F1F5F9', metalness: 0.95, roughness: 0.1 });
  const glassMat = new THREE.MeshStandardMaterial({
    color: '#0F172A',
    roughness: 0.05,
    metalness: 0.2,
    transparent: true,
    opacity: 0.85
  });

  // Lower Main Body / Fenders
  const lowerBody = box(W, 0.52, L * 0.96, bodyMat, 0, 0.52, 0, g);

  // Curved Wheel Wells (cutout appearance via dark trim arches)
  [-1, 1].forEach((s) => {
    [-L * 0.32, L * 0.32].forEach((wz) => {
      box(0.08, 0.56, 1.1, trimMat, s * (W * 0.5 + 0.02), 0.48, wz, g);
    });
  });

  // Hood (sloping slightly forward)
  const hood = new THREE.Group();
  hood.position.set(0, 0.76, L * 0.24);
  g.add(hood);
  const hoodMesh = box(W * 0.96, 0.08, L * 0.38, bodyMat, 0, 0, 0, hood);

  // Front Grill & Bumper
  const grillTex = canvasTex('suv_grill', 256, 128, (c) => {
    c.fillStyle = '#0F172A';
    c.fillRect(0, 0, 256, 128);
    c.strokeStyle = '#E2E8F0';
    c.lineWidth = 4;
    for (let y = 16; y < 128; y += 18) {
      c.beginPath(); c.moveTo(20, y); c.lineTo(236, y); c.stroke();
    }
  });
  box(W * 0.78, 0.28, 0.08, [trimMat, trimMat, trimMat, trimMat, mat({ map: grillTex }), trimMat], 0, 0.52, L * 0.49, g);
  box(W * 1.02, 0.22, 0.24, chromeMat, 0, 0.32, L * 0.48, g); // Front Bumper
  box(W * 1.02, 0.22, 0.24, chromeMat, 0, 0.32, -L * 0.48, g); // Rear Bumper

  // Greenhouse / Cabin (Wagon Profile with Roof Rails)
  const cabin = new THREE.Group();
  cabin.position.set(0, 0.76, -L * 0.08);
  g.add(cabin);

  // Roof
  box(W * 0.88, 0.07, L * 0.62, bodyMat, 0, 0.74, 0, cabin);

  // Roof Rails (Left & Right luggage bars)
  [-1, 1].forEach((s) => {
    cyl(0.025, 0.025, L * 0.58, chromeMat, s * (W * 0.40), 0.82, 0, cabin, 8).rotation.x = Math.PI / 2;
    box(0.04, 0.08, 0.06, trimMat, s * (W * 0.40), 0.78, L * 0.25, cabin);
    box(0.04, 0.08, 0.06, trimMat, s * (W * 0.40), 0.78, -L * 0.25, cabin);
  });

  // Windshield (sloped front glass)
  const ws = box(W * 0.86, 0.72, 0.06, glassMat, 0, 0.40, L * 0.30, cabin);
  ws.rotation.x = 0.52;

  // Rear Windshield (sloped back glass)
  const rws = box(W * 0.86, 0.65, 0.06, glassMat, 0, 0.40, -L * 0.30, cabin);
  rws.rotation.x = -0.45;

  // Side Glass & Pillars (A, B, C, D pillars)
  [-1, 1].forEach((s) => {
    box(0.05, 0.52, L * 0.56, glassMat, s * (W * 0.435), 0.40, 0, cabin);
    // B-Pillar & C-Pillar
    box(0.06, 0.54, 0.12, trimMat, s * (W * 0.44), 0.40, L * 0.05, cabin);
    box(0.06, 0.54, 0.12, trimMat, s * (W * 0.44), 0.40, -L * 0.14, cabin);
    // Side Mirrors
    box(0.24, 0.14, 0.16, bodyMat, s * (W * 0.48 + 0.1), 0.64, L * 0.18, g);
  });

  // Headlights & Taillights
  const headMat = new THREE.MeshStandardMaterial({
    color: '#FFFDF0',
    emissive: '#FFF9D2',
    emissiveIntensity: headlights ? 3.5 : 0.4
  });
  const tailMat = new THREE.MeshStandardMaterial({
    color: '#EF4444',
    emissive: '#DC2626',
    emissiveIntensity: taillights ? 2.8 : 0.4
  });

  [-1, 1].forEach((s) => {
    box(0.38, 0.18, 0.08, headMat, s * (W * 0.36), 0.58, L * 0.49, g);
    box(0.34, 0.18, 0.08, tailMat, s * (W * 0.36), 0.58, -L * 0.49, g);
  });

  // 4 Wheels
  const wheels = [];
  [
    [-W * 0.52, L * 0.32],
    [W * 0.52, L * 0.32],
    [-W * 0.52, -L * 0.32],
    [W * 0.52, -L * 0.32]
  ].forEach(([wx, wz]) => {
    const w = buildRealisticWheel(0.38, 0.26, true);
    w.position.set(wx, 0.38, wz);
    g.add(w);
    wheels.push(w);
  });

  // Damage Deformation (crumpled hood & cracked angle)
  if (damaged) {
    hood.rotation.x = -0.55;
    hood.position.y += 0.28;
    hood.position.z -= 0.22;
    ws.rotation.z = 0.18;
    wheels[0].rotation.y = 0.5;
    wheels[1].rotation.y = -0.3;
  }

  g.wheels = wheels;
  g.hood = hood;
  g.update = (t, steer = 0) => {
    wheels.forEach((w) => {
      w.children.forEach((c) => (c.rotation.x += 0.2));
    });
    wheels[0].rotation.y = steer;
    wheels[1].rotation.y = steer;
  };

  return g;
}

// ── 2. Detailed Police SUV (Sheriff Cruiser with Openable Door) ──────────────
export function buildDetailedPoliceCruiser({ headlights = true, openDoor = false } = {}) {
  const g = new THREE.Group();
  const W = 2.15, L = 5.0, H = 1.65;

  const whiteMat = new THREE.MeshStandardMaterial({ color: '#F8FAFC', metalness: 0.6, roughness: 0.25 });
  const greenMat = new THREE.MeshStandardMaterial({ color: '#166534', metalness: 0.6, roughness: 0.25 }); // Forest green stripe as in frame_015 & 020
  const trimMat = new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.8 });
  const chromeMat = new THREE.MeshStandardMaterial({ color: '#F1F5F9', metalness: 0.95, roughness: 0.1 });
  const glassMat = new THREE.MeshStandardMaterial({
    color: '#0F172A',
    roughness: 0.05,
    metalness: 0.2,
    transparent: true,
    opacity: 0.85
  });

  // Lower Body: Dark Green Lower Quarter Panel (matching frame_015 & frame_020)
  box(W, 0.32, L * 0.96, greenMat, 0, 0.38, 0, g);
  // Upper Body: Clean White Upper Doors & Fenders
  box(W * 0.98, 0.36, L * 0.95, whiteMat, 0, 0.68, 0, g);

  // Push Bumper / Bullbar on Front
  const bullbar = new THREE.Group();
  bullbar.position.set(0, 0.45, L * 0.50);
  g.add(bullbar);
  box(W * 0.65, 0.45, 0.08, trimMat, 0, 0, 0, bullbar);
  [-0.28, 0.28].forEach((bx) => cyl(0.04, 0.04, 0.55, chromeMat, bx, 0, 0.06, bullbar, 8));

  // Front Hood & Grill
  box(W * 0.94, 0.08, L * 0.36, whiteMat, 0, 0.88, L * 0.24, g);
  box(W * 0.78, 0.26, 0.08, trimMat, 0, 0.64, L * 0.49, g);

  // Cabin
  const cabin = new THREE.Group();
  cabin.position.set(0, 0.88, -L * 0.06);
  g.add(cabin);

  // White Roof with Unit "12" Painted on Top (matching frame_020)
  const roofTex = canvasTex('police_roof_12', 256, 256, (c) => {
    c.fillStyle = '#F8FAFC';
    c.fillRect(0, 0, 256, 256);
    c.fillStyle = '#0F172A';
    c.font = '900 120px Inter, sans-serif';
    c.textAlign = 'center';
    c.fillText('12', 128, 170);
  });
  box(W * 0.88, 0.07, L * 0.62, mat({ map: roofTex }), 0, 0.85, 0, cabin);

  // Roof Siren Lightbar (Red, Blue, Amber)
  const lightbar = new THREE.Group();
  lightbar.position.set(0, 0.95, L * 0.02);
  cabin.add(lightbar);
  box(W * 0.65, 0.06, 0.16, chromeMat, 0, 0, 0, lightbar);

  const redMat = new THREE.MeshStandardMaterial({ color: '#EF4444', emissive: '#EF4444', emissiveIntensity: 4.0 });
  const blueMat = new THREE.MeshStandardMaterial({ color: '#3B82F6', emissive: '#3B82F6', emissiveIntensity: 4.0 });
  const redB = box(0.25, 0.12, 0.14, redMat, -W * 0.18, 0.08, 0, lightbar);
  const blueB = box(0.25, 0.12, 0.14, blueMat, W * 0.18, 0.08, 0, lightbar);

  // Windshields
  const fws = box(W * 0.86, 0.78, 0.06, glassMat, 0, 0.45, L * 0.30, cabin);
  fws.rotation.x = 0.50;
  const rws = box(W * 0.86, 0.68, 0.06, glassMat, 0, 0.45, -L * 0.30, cabin);
  rws.rotation.x = -0.40;

  // Passenger Side Door with Gold Star & "SHERIFF" Text
  const doorTex = canvasTex('sheriff_door', 256, 128, (c) => {
    c.fillStyle = '#F8FAFC';
    c.fillRect(0, 0, 256, 128);
    // Gold Star Shield
    c.fillStyle = '#EAB308';
    c.beginPath();
    const cx = 90, cy = 64, r = 38;
    for (let i = 0; i < 5; i++) {
      const a1 = (i * 72 - 90) * Math.PI / 180;
      const a2 = (i * 72 + 36 - 90) * Math.PI / 180;
      c.lineTo(cx + Math.cos(a1) * r, cy + Math.sin(a1) * r);
      c.lineTo(cx + Math.cos(a2) * (r * 0.42), cy + Math.sin(a2) * (r * 0.42));
    }
    c.closePath();
    c.fill();
    // Inner badge circle
    c.fillStyle = '#B45309';
    c.beginPath(); c.arc(cx, cy, 12, 0, Math.PI * 2); c.fill();
    // "SHERIFF" text
    c.fillStyle = '#166534';
    c.font = '900 32px Inter, sans-serif';
    c.fillText('SHERIFF', 145, 75);
  });

  const starDoorMat = mat({ map: doorTex });

  // Passenger Right Side Door (fixed)
  box(0.06, 0.48, L * 0.38, starDoorMat, W * 0.495, 0.68, 0, g);
  box(0.05, 0.52, L * 0.56, glassMat, W * 0.435, 0.45, 0, cabin);

  // Driver Left Side Door (Openable on a hinge for Sheriff stepping out!)
  const doorHinge = new THREE.Group();
  doorHinge.position.set(-W * 0.49, 0.45, L * 0.18);
  g.add(doorHinge);

  const driverDoor = new THREE.Group();
  driverDoor.position.set(0, 0, 0);
  doorHinge.add(driverDoor);

  // Door panel + window frame
  box(0.06, 0.48, L * 0.38, starDoorMat, 0, 0.23, -L * 0.19, driverDoor);
  box(0.04, 0.54, L * 0.36, glassMat, 0, 0.70, -L * 0.19, driverDoor);
  // Window frame border
  box(0.06, 0.56, 0.05, whiteMat, 0, 0.70, -0.02, driverDoor);
  box(0.06, 0.56, 0.05, whiteMat, 0, 0.70, -L * 0.36, driverDoor);
  box(0.06, 0.05, L * 0.36, whiteMat, 0, 0.98, -L * 0.19, driverDoor);

  if (openDoor) {
    doorHinge.rotation.y = -1.15; // wide open 65 degrees!
  }

  // 4 Black Police Steel Wheels with Chrome Center Cap
  const wheels = [];
  [
    [-W * 0.52, L * 0.32],
    [W * 0.52, L * 0.32],
    [-W * 0.52, -L * 0.32],
    [W * 0.52, -L * 0.32]
  ].forEach(([wx, wz]) => {
    const w = buildRealisticWheel(0.40, 0.28, false);
    w.position.set(wx, 0.40, wz);
    g.add(w);
    wheels.push(w);
  });

  g.wheels = wheels;
  g.doorHinge = doorHinge;
  g.redB = redB;
  g.blueB = blueB;

  g.update = (t, steer = 0) => {
    wheels.forEach((w) => {
      w.children.forEach((c) => (c.rotation.x += 0.2));
    });
    wheels[0].rotation.y = steer;
    wheels[1].rotation.y = steer;

    // Siren strobe
    const strobe = Math.sin(t * 20);
    redB.material.emissiveIntensity = strobe > 0 ? 5.5 : 0.3;
    blueB.material.emissiveIntensity = strobe < 0 ? 5.5 : 0.3;
  };

  return g;
}

// ── 3. Retro Heavy Tow Truck with Beach Umbrella & Sign ──────────────────────
export function buildDetailedRetroTowTruck() {
  const g = new THREE.Group();
  const W = 2.4, L = 6.4;

  const redMat = new THREE.MeshStandardMaterial({ color: '#DC2626', metalness: 0.5, roughness: 0.3 });
  const whiteMat = new THREE.MeshStandardMaterial({ color: '#F8FAFC', metalness: 0.5, roughness: 0.3 });
  const darkMat = new THREE.MeshStandardMaterial({ color: '#1E293B', roughness: 0.8 });
  const chromeMat = new THREE.MeshStandardMaterial({ color: '#F1F5F9', metalness: 0.95, roughness: 0.1 });
  const glassMat = new THREE.MeshStandardMaterial({
    color: '#0F172A',
    roughness: 0.1,
    transparent: true,
    opacity: 0.8
  });

  // Heavy Chassis
  box(W * 0.85, 0.45, L, darkMat, 0, 0.45, 0, g);

  // Red Truck Cab (Front) with White Roof
  const cab = new THREE.Group();
  cab.position.set(0, 0.65, L * 0.26);
  g.add(cab);

  box(W, 1.15, L * 0.30, redMat, 0, 0.60, 0, cab);
  box(W * 0.96, 0.10, L * 0.32, whiteMat, 0, 1.20, 0, cab); // White Cab Roof
  box(W * 0.92, 0.70, L * 0.22, redMat, 0, 0.38, L * 0.24, cab); // Front Hood
  box(W * 0.82, 0.60, 0.10, chromeMat, 0, 0.35, L * 0.34, cab); // Big Chrome Grill

  // Sloped Windshield
  const ws = box(W * 0.88, 0.55, 0.08, glassMat, 0, 0.92, L * 0.15, cab);
  ws.rotation.x = 0.25;

  // Vertical Exhaust Smokestack
  cyl(0.08, 0.08, 2.6, chromeMat, W * 0.52, 1.6, -L * 0.12, cab, 16);

  // White Utility Bed with Louvered Tool Compartments
  const bed = new THREE.Group();
  bed.position.set(0, 0.65, -L * 0.18);
  g.add(bed);

  box(W * 0.98, 0.90, L * 0.56, whiteMat, 0, 0.45, 0, bed);

  // Heavy A-Frame Crane Boom
  const boom = new THREE.Group();
  boom.position.set(0, 0.95, -L * 0.12);
  g.add(boom);
  const armL = cyl(0.08, 0.08, 3.6, redMat, -0.65, 1.4, -0.9, boom, 12);
  armL.rotation.x = -0.7;
  const armR = cyl(0.08, 0.08, 3.6, redMat, 0.65, 1.4, -0.9, boom, 12);
  armR.rotation.x = -0.7;

  // Tow Cable & Hook
  cyl(0.02, 0.02, 2.2, darkMat, 0, 1.3, -2.2, boom, 6);
  box(0.24, 0.32, 0.12, chromeMat, 0, 0.3, -2.2, boom);

  // Striped Beach Umbrella standing in truck bed (matching frame_010!)
  const umbrella = new THREE.Group();
  umbrella.position.set(W * 0.32, 1.1, -L * 0.25);
  g.add(umbrella);
  cyl(0.03, 0.03, 2.2, chromeMat, 0, 1.1, 0, umbrella, 8); // Pole

  // Folded / Half-open Beach Umbrella Cone (Orange & White alternating wedges)
  const umbCone = new THREE.Mesh(
    new THREE.ConeGeometry(0.35, 1.4, 8),
    new THREE.MeshStandardMaterial({ color: '#F97316', roughness: 0.6 })
  );
  umbCone.position.set(0, 1.8, 0);
  umbrella.add(umbCone);

  // Marquee Roof Sign: "TREE TOWING $ CASH ONLY $" (matching frame_010!)
  const signTex = canvasTex('tree_towing_cash_sign', 512, 160, (c) => {
    c.fillStyle = '#FEF3C7';
    c.fillRect(0, 0, 512, 160);
    c.strokeStyle = '#B45309';
    c.lineWidth = 10;
    c.strokeRect(6, 6, 500, 148);

    c.fillStyle = '#DC2626';
    c.font = '900 44px Inter, sans-serif';
    c.textAlign = 'center';
    c.fillText('TREE TOWING', 256, 62);

    c.fillStyle = '#16A34A';
    c.font = '900 38px Inter, sans-serif';
    c.fillText('$ CASH ONLY $', 256, 124);
  });

  const signMesh = box(2.2, 0.75, 0.10, [chromeMat, chromeMat, chromeMat, chromeMat, mat({ map: signTex }), mat({ map: signTex })], 0, 2.35, L * 0.26, g);

  // 6 Heavy Wheels with Chrome Dish Center Caps
  const wheels = [];
  [
    [-W * 0.54, L * 0.32],
    [W * 0.54, L * 0.32],
    [-W * 0.54, -L * 0.18],
    [W * 0.54, -L * 0.18],
    [-W * 0.54, -L * 0.38],
    [W * 0.54, -L * 0.38]
  ].forEach(([wx, wz]) => {
    const w = buildRealisticWheel(0.46, 0.32, true);
    w.position.set(wx, 0.46, wz);
    g.add(w);
    wheels.push(w);
  });

  g.wheels = wheels;
  return g;
}

// ── 4. Detailed 3D Oak Tree & Curved Horseshoe Marquee Sign ──────────────────
export function buildDetailedOakTree({ chopped = false, hasSign = true } = {}) {
  const g = new THREE.Group();

  // Bark Texture with Vertical Striations (matching frame_006, 008, 015)
  const barkTex = canvasTex('oak_bark_texture', 512, 512, (c) => {
    c.fillStyle = '#5A3D28';
    c.fillRect(0, 0, 512, 512);
    // Vertical bark fissures & furrows
    for (let x = 0; x < 512; x += 6) {
      const shadeVal = (Math.sin(x * 0.2) + Math.random() * 0.4);
      c.fillStyle = shadeVal > 0.2 ? '#3E2718' : '#6F4E37';
      c.fillRect(x, 0, 4, 512);
    }
  });

  const barkMat = new THREE.MeshStandardMaterial({
    map: barkTex,
    roughness: 0.95,
    metalness: 0.05
  });

  const leafMat1 = new THREE.MeshStandardMaterial({ color: '#4D7C0F', roughness: 0.75 }); // Olive/Lush green
  const leafMat2 = new THREE.MeshStandardMaterial({ color: '#65A30D', roughness: 0.70 }); // Sunlit lime highlight
  const leafMat3 = new THREE.MeshStandardMaterial({ color: '#365314', roughness: 0.85 }); // Deep shadow leaf

  // Trunk Base / Stump
  const trunkBase = cyl(0.68, 0.88, 1.4, barkMat, 0, 0.7, 0, g, 20);

  // Tree Rings on Stump Top (visible when chopped)
  const ringsTex = canvasTex('stump_rings', 256, 256, (c) => {
    c.fillStyle = '#D9A362';
    c.fillRect(0, 0, 256, 256);
    c.strokeStyle = '#78350F';
    c.lineWidth = 4;
    for (let r = 12; r < 120; r += 10) {
      c.beginPath();
      c.arc(128 + Math.sin(r) * 4, 128 + Math.cos(r) * 4, r, 0, Math.PI * 2);
      c.stroke();
    }
  });
  const stumpTop = new THREE.Mesh(new THREE.CircleGeometry(0.68, 20), mat({ map: ringsTex }));
  stumpTop.rotation.x = -Math.PI / 2;
  stumpTop.position.set(0, 1.405, 0);
  g.add(stumpTop);

  // Upper Tree & Canopy (if not chopped)
  const upperTree = new THREE.Group();
  g.add(upperTree);

  if (!chopped) {
    // Upper Main Trunk
    cyl(0.52, 0.68, 3.4, barkMat, 0, 3.0, 0, upperTree, 18);

    // Thick Forking Secondary Branches (matching frame_006 & 008)
    const b1 = cyl(0.28, 0.42, 3.2, barkMat, 1.0, 4.6, 0.4, upperTree, 14);
    b1.rotation.z = -0.55;
    b1.rotation.x = 0.25;

    const b2 = cyl(0.26, 0.38, 2.8, barkMat, -0.9, 4.5, -0.3, upperTree, 14);
    b2.rotation.z = 0.50;
    b2.rotation.x = -0.30;

    // Rich Layered Foliage Canopy Clumps
    const clumps = [
      [0, 5.8, 0, 2.4, leafMat1],
      [1.6, 5.2, 0.8, 1.9, leafMat2],
      [-1.5, 5.1, -0.6, 1.8, leafMat3],
      [0.6, 6.8, -0.5, 2.0, leafMat2],
      [-0.7, 6.5, 0.7, 1.9, leafMat1],
      [0, 7.6, 0, 1.6, leafMat3],
      [2.2, 4.4, 0.4, 1.4, leafMat2],
      [-2.0, 4.3, -0.2, 1.4, leafMat1]
    ];
    clumps.forEach(([cx, cy, cz, cr, cm]) => {
      const leaf = new THREE.Mesh(new THREE.DodecahedronGeometry(cr, 1), cm);
      leaf.position.set(cx, cy, cz);
      leaf.castShadow = leaf.receiveShadow = true;
      upperTree.add(leaf);
    });
  }

  // Giant Curved Horseshoe Marquee Sign ("DON'T HIT THIS TREE")
  const bulbs = [];
  let marqueeSign = null;

  if (hasSign) {
    marqueeSign = new THREE.Group();
    // Mounted at driver eye-level (y: 2.3m on trunk, or on post when chopped)
    marqueeSign.position.set(0, chopped ? 1.7 : 2.5, 0.85);
    g.add(marqueeSign);

    if (chopped) {
      cyl(0.08, 0.08, 1.6, barkMat, 0, -0.8, -0.05, marqueeSign, 8); // Wooden post
    }

    // A. Center Board with Warning Text
    const boardTex = canvasTex('dont_hit_board_tex', 256, 320, (c) => {
      c.fillStyle = '#FFFDF5';
      c.fillRect(0, 0, 256, 320);
      c.strokeStyle = '#B91C1C';
      c.lineWidth = 14;
      c.strokeRect(8, 8, 240, 304);
      c.fillStyle = '#B91C1C';
      c.font = '900 54px Inter, sans-serif';
      c.textAlign = 'center';
      c.fillText("DON'T", 128, 80);
      c.fillText("HIT", 128, 150);
      c.fillText("THIS", 128, 220);
      c.fillText("TREE", 128, 290);
    });
    box(1.35, 1.65, 0.10, mat({ map: boardTex }), 0, 0, 0, marqueeSign);

    // B. Curved Horseshoe Arch Frame (Red Marquee Metal)
    const redMat = new THREE.MeshStandardMaterial({ color: '#DC2626', roughness: 0.35, metalness: 0.2 });
    box(1.8, 0.22, 0.18, redMat, 0, 0.94, 0, marqueeSign); // Top arch
    box(0.22, 1.9, 0.18, redMat, -0.8, 0.0, 0, marqueeSign); // Left
    box(0.22, 1.9, 0.18, redMat, 0.8, 0.0, 0, marqueeSign); // Right
    box(1.8, 0.22, 0.18, redMat, 0, -0.94, 0, marqueeSign); // Bottom

    // Giant Arrow Pointer at Bottom-Right pointing down at tree trunk
    const arrow = box(0.55, 0.55, 0.18, redMat, 0.95, -0.95, 0, marqueeSign);
    arrow.rotation.z = -0.78;

    // C. 20 Glowing Incandescent Lightbulbs along the Horseshoe Perimeter
    const bulbPts = [
      [-0.7, 0.94], [-0.35, 0.94], [0, 0.94], [0.35, 0.94], [0.7, 0.94],
      [-0.7, -0.94], [-0.35, -0.94], [0, -0.94], [0.35, -0.94], [0.7, -0.94],
      [-0.8, 0.65], [-0.8, 0.30], [-0.8, -0.05], [-0.8, -0.40], [-0.8, -0.75],
      [0.8, 0.65], [0.8, 0.30], [0.8, -0.05], [0.8, -0.40], [0.8, -0.75]
    ];

    bulbPts.forEach(([bx, by]) => {
      const bMat = new THREE.MeshStandardMaterial({
        color: '#FFFBEB',
        emissive: '#FDE047',
        emissiveIntensity: 4.5
      });
      const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 10), bMat);
      bulb.position.set(bx, by, 0.13);
      marqueeSign.add(bulb);
      bulbs.push(bulb);
    });
  }

  // Roadside "DAYS SINCE LAST CRASH: 7" Sign (matching frame_006!)
  const daysSignTex = canvasTex('days_since_crash', 256, 320, (c) => {
    c.fillStyle = '#F8FAFC';
    c.fillRect(0, 0, 256, 320);
    c.fillStyle = '#DC2626';
    c.fillRect(10, 10, 236, 75);
    c.fillStyle = '#FFFFFF';
    c.font = '900 24px Inter, sans-serif';
    c.textAlign = 'center';
    c.fillText('DAYS SINCE', 128, 42);
    c.fillText('LAST CRASH', 128, 70);

    c.fillStyle = '#0F172A';
    c.font = '900 130px Inter, sans-serif';
    c.fillText('7', 128, 240);
  });
  const daysSign = new THREE.Group();
  daysSign.position.set(-1.8, 0, 0);
  g.add(daysSign);
  cyl(0.04, 0.04, 1.8, barkMat, 0, 0.9, 0, daysSign, 8); // Post
  box(0.75, 0.95, 0.04, mat({ map: daysSignTex }), 0, 1.45, 0, daysSign); // Sign board

  g.upperTree = upperTree;
  g.marqueeSign = marqueeSign;
  g.daysSign = daysSign;
  g.bulbs = bulbs;

  g.update = (t) => {
    // Sequential chasing / flashing lights
    bulbs.forEach((b, i) => {
      const phase = (i + Math.floor(t * 12)) % 3 === 0;
      b.material.emissiveIntensity = phase ? 6.5 : 0.3;
    });
  };

  return g;
}

// ── 5. Agricultural Highway World (Sunny Wheat Fields & Vanishing Road) ─────
export function buildAgriculturalHighway({ len = 200, night = false } = {}) {
  const scene = new THREE.Scene();

  if (night) {
    scene.background = new THREE.Color('#060913');
    scene.fog = new THREE.FogExp2('#080D1A', 0.02);
  } else {
    // Radiant Sunny Midday Sky (matching frame_002, 004, 006)
    scene.background = new THREE.Color('#38BDF8');
    scene.fog = new THREE.FogExp2('#BAE6FD', 0.005);
  }

  // 1. Smooth Dark Asphalt Road
  const roadTex = canvasTex('asphalt_highway_' + night, 512, 1024, (c) => {
    c.fillStyle = night ? '#181C24' : '#2A2E39';
    c.fillRect(0, 0, 512, 1024);
    // Double Solid Yellow Lines
    c.fillStyle = '#EAB308';
    c.fillRect(251, 0, 4, 1024);
    c.fillRect(257, 0, 4, 1024);
    // Crisp Solid White Shoulder Lines
    c.fillStyle = '#F8FAFC';
    c.fillRect(35, 0, 7, 1024);
    c.fillRect(470, 0, 7, 1024);
  });

  const road = new THREE.Mesh(
    new THREE.PlaneGeometry(9.2, len),
    new THREE.MeshStandardMaterial({
      map: roadTex,
      roughness: night ? 0.12 : 0.75,
      metalness: night ? 0.25 : 0.05
    })
  );
  road.rotation.x = -Math.PI / 2;
  road.position.set(0, 0.01, -len / 2 + 20);
  road.receiveShadow = true;
  scene.add(road);

  // 2. Gravel Shoulder Strip (between asphalt and grass)
  [-1, 1].forEach((s) => {
    const gravel = box(1.2, 0.02, len, mat({ color: '#A8A29E', roughness: 0.95 }), s * 5.2, 0.005, -len / 2 + 20, scene);
  });

  // 3. Bright Green Roadside Grass Strip (matching frame_002)
  [-1, 1].forEach((s) => {
    const grassStrip = box(2.6, 0.03, len, mat({ color: night ? '#0F1E13' : '#65A30D', roughness: 0.85 }), s * 7.0, 0.008, -len / 2 + 20, scene);
  });

  // 4. Agricultural Wheat / Crop Furrow Fields (stretching wide to horizon!)
  const fieldTex = canvasTex('wheat_field_rows', 512, 512, (c) => {
    c.fillStyle = night ? '#141E15' : '#CA8A04'; // Golden wheat yellow
    c.fillRect(0, 0, 512, 512);
    // Furrow stripes
    for (let y = 0; y < 512; y += 16) {
      c.fillStyle = night ? '#0E150F' : '#A16207';
      c.fillRect(0, y, 512, 6);
    }
  });

  const fieldMat = new THREE.MeshStandardMaterial({ map: fieldTex, roughness: 0.95 });
  const leftField = new THREE.Mesh(new THREE.PlaneGeometry(160, len + 60), fieldMat);
  leftField.rotation.x = -Math.PI / 2;
  leftField.position.set(-88, 0, -len / 2 + 20);
  leftField.receiveShadow = true;
  scene.add(leftField);

  const rightField = new THREE.Mesh(new THREE.PlaneGeometry(160, len + 60), fieldMat);
  rightField.rotation.x = -Math.PI / 2;
  rightField.position.set(88, 0, -len / 2 + 20);
  rightField.receiveShadow = true;
  scene.add(rightField);

  // 5. Wooden Wire Fence Posts along the field edge (matching frame_002 & 004)
  const postMat = new THREE.MeshStandardMaterial({ color: '#573D26', roughness: 0.9 });
  [-1, 1].forEach((s) => {
    for (let z = 15; z > -len; z -= 8) {
      cyl(0.06, 0.08, 1.2, postMat, s * 8.4, 0.6, z, scene, 8);
    }
  });

  // 6. Radiant Midday Sunlight & Soft Hemisphere Light
  if (night) {
    const hemi = new THREE.HemisphereLight('#1E293B', '#090D16', 0.5);
    scene.add(hemi);
    const moon = new THREE.DirectionalLight('#94A3B8', 0.9);
    moon.position.set(-15, 25, 10);
    moon.castShadow = true;
    scene.add(moon);
  } else {
    const sun = new THREE.DirectionalLight('#FFFBEB', 3.4);
    sun.position.set(22, 35, 22);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -25, right: 25, top: 25, bottom: -25, near: 1, far: 90 });
    sun.shadow.bias = -0.0004;
    scene.add(sun);

    const hemi = new THREE.HemisphereLight('#BAE6FD', '#4D7C0F', 1.25);
    scene.add(hemi);

    // Fluffy 3D Clouds on Horizon (matching frame_004)
    const cloudMat = new THREE.MeshBasicMaterial({ color: '#F8FAFC', transparent: true, opacity: 0.9 });
    [
      [-35, 18, -90, 16],
      [28, 24, -110, 22],
      [-10, 22, -130, 20],
      [45, 16, -80, 14]
    ].forEach(([cx, cy, cz, cr]) => {
      const c = new THREE.Mesh(new THREE.DodecahedronGeometry(cr, 1), cloudMat);
      c.scale.set(1.6, 0.6, 1.0);
      c.position.set(cx, cy, cz);
      scene.add(c);
    });
  }

  return { scene };
}

// ── 6. First-Person Cockpit POV (Matching frame_026 & 028) ──────────────────
export function buildDetailedCockpitPOV() {
  const g = new THREE.Group();

  const dashMat = new THREE.MeshStandardMaterial({ color: '#111827', roughness: 0.85 });
  const trimMat = new THREE.MeshStandardMaterial({ color: '#334155', metalness: 0.7, roughness: 0.25 });
  const chromeMat = new THREE.MeshStandardMaterial({ color: '#F1F5F9', metalness: 0.95, roughness: 0.1 });
  const wheelMat = new THREE.MeshStandardMaterial({ color: '#1E293B', roughness: 0.45, metalness: 0.2 });

  // 1. Dashboard Base & Center Console (matching frame_026)
  const dash = box(3.6, 0.65, 1.5, dashMat, 0, -0.32, -0.85, g);
  dash.rotation.x = 0.16;

  // Warm Interior Dome/Dash Ambient Light
  const domeLight = new THREE.PointLight('#FDE68A', 2.8, 3.5);
  domeLight.position.set(-0.2, 0.45, -0.2);
  g.add(domeLight);

  // Exterior Front Hood Extending in Front of Windshield (matching frame_026!)
  const hoodMat = new THREE.MeshStandardMaterial({ color: '#F8FAFC', roughness: 0.25, metalness: 0.5 });
  const frontHood = box(2.1, 0.12, 2.6, hoodMat, 0, -0.16, -2.2, g);
  frontHood.rotation.x = -0.05;

  // High-Beam Headlights illuminating wet road & rain
  const headlightL = new THREE.SpotLight('#FFFBEB', 8.0, 45, Math.PI / 6, 0.4);
  headlightL.position.set(-0.8, -0.1, -2.5);
  headlightL.target.position.set(-0.8, -1.0, -25);
  g.add(headlightL, headlightL.target);

  const headlightR = new THREE.SpotLight('#FFFBEB', 8.0, 45, Math.PI / 6, 0.4);
  headlightR.position.set(0.8, -0.1, -2.5);
  headlightR.target.position.set(0.8, -1.0, -25);
  g.add(headlightR, headlightR.target);

  // Rearview Mirror at top of windshield
  box(0.44, 0.14, 0.04, trimMat, 0, 0.72, -0.85, g);

  // Center Air Conditioning Vents & Amber Radio Display
  box(0.55, 0.24, 0.08, trimMat, 0.55, -0.16, -0.82, g);
  const radioTex = canvasTex('radio_display', 256, 128, (c) => {
    c.fillStyle = '#0F172A';
    c.fillRect(0, 0, 256, 128);
    c.fillStyle = '#F59E0B'; // Amber backlit screen
    c.fillRect(16, 16, 224, 96);
  });
  box(0.48, 0.22, 0.09, mat({ map: radioTex }), 0.55, -0.38, -0.82, g);

  // 2. Instrument Gauge Cluster: Dual Dials + Digital "D" Gear (matching frame_028!)
  const gaugeTex = canvasTex('cockpit_dual_gauges', 512, 256, (c) => {
    c.fillStyle = '#05070A';
    c.fillRect(0, 0, 512, 256);

    const drawDial = (cx, cy, label, unit) => {
      c.strokeStyle = '#38BDF8';
      c.lineWidth = 6;
      c.beginPath();
      c.arc(cx, cy, 90, 0.75 * Math.PI, 2.25 * Math.PI);
      c.stroke();
      c.fillStyle = '#F8FAFC';
      c.font = '700 22px Inter, sans-serif';
      c.textAlign = 'center';
      c.fillText(label, cx, cy + 30);
      c.fillStyle = '#EF4444';
      c.font = '900 24px Inter, sans-serif';
      c.fillText(unit, cx, cy + 60);

      // Tick marks
      for (let a = 0.75 * Math.PI; a <= 2.25 * Math.PI; a += 0.25) {
        c.strokeStyle = '#F8FAFC';
        c.lineWidth = 3;
        c.beginPath();
        c.moveTo(cx + Math.cos(a) * 75, cy + Math.sin(a) * 75);
        c.lineTo(cx + Math.cos(a) * 88, cy + Math.sin(a) * 88);
        c.stroke();
      }
    };

    drawDial(130, 125, '65', 'MPH');
    drawDial(380, 125, '3.2', 'RPM');

    // Center Digital Display: "D" Gear (Drive) in bright cyan
    c.fillStyle = '#0284C7';
    c.beginPath(); c.roundRect(228, 90, 56, 70, 8); c.fill();
    c.fillStyle = '#FFFFFF';
    c.font = '900 48px Inter, sans-serif';
    c.fillText('D', 256, 144);
  });

  const gaugeScreen = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.58), new THREE.MeshBasicMaterial({
    map: gaugeTex,
    toneMapped: false
  }));
  gaugeScreen.position.set(-0.35, -0.06, -0.84);
  gaugeScreen.rotation.x = -0.15;
  g.add(gaugeScreen);

  // Glowing Speedometer Needles
  const speedoNeedle = new THREE.Mesh(
    new THREE.BoxGeometry(0.018, 0.18, 0.01),
    new THREE.MeshBasicMaterial({ color: '#F97316' })
  );
  speedoNeedle.position.set(-0.64, -0.04, -0.82);
  speedoNeedle.geometry.translate(0, 0.09, 0);
  g.add(speedoNeedle);

  // 3. Modern 3-Spoke Steering Wheel (Angled toward driver)
  const wheelPivot = new THREE.Group();
  wheelPivot.position.set(-0.35, 0.08, -0.42);
  wheelPivot.rotation.x = 0.28;
  g.add(wheelPivot);

  const wheelRoll = new THREE.Group();
  wheelPivot.add(wheelRoll);

  // Outer Rim with thumb grips
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.44, 0.045, 16, 36), wheelMat);
  wheelRoll.add(rim);

  // Center Airbag Horn Pad with Star Emblem
  cyl(0.14, 0.14, 0.08, trimMat, 0, 0, 0, wheelRoll, 16).rotation.x = Math.PI / 2;
  box(0.82, 0.07, 0.04, wheelMat, 0, 0, 0, wheelRoll);
  box(0.07, 0.40, 0.04, wheelMat, 0, -0.20, 0, wheelRoll);

  // 4. Driver's Two Cartoon Arms Gripping at 9 & 3 o'clock (matching frame_028!)
  const handTex = canvasTex('driver_arm_hand', 256, 128, (c) => {
    c.lineCap = 'round';
    c.lineJoin = 'round';
    // Dark purple sleeve/arm (matching frame_028)
    c.strokeStyle = '#312E81';
    c.lineWidth = 28;
    c.beginPath();
    c.moveTo(20, 64);
    c.lineTo(160, 64);
    c.stroke();
    c.strokeStyle = INK;
    c.lineWidth = 4;
    c.stroke();

    // Round White Toon Hand/Fist
    c.fillStyle = '#FFFFFF';
    c.strokeStyle = INK;
    c.lineWidth = 8;
    c.beginPath();
    c.arc(195, 64, 38, 0, Math.PI * 2);
    c.fill();
    c.stroke();
  });

  const handMat = new THREE.MeshBasicMaterial({ map: handTex, transparent: true, side: THREE.DoubleSide });

  const armL = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.28), handMat);
  armL.position.set(-0.48, 0.05, 0.06);
  armL.rotation.z = 0.25;
  wheelRoll.add(armL);

  const armR = new THREE.Mesh(new THREE.PlaneGeometry(0.55, 0.28), handMat);
  armR.position.set(0.48, 0.05, 0.06);
  armR.rotation.z = -0.25;
  armR.scale.x = -1; // mirror right hand
  wheelRoll.add(armR);

  // 5. Windshield & Moving Wiper Blade (resting at bottom, matching frame_026 & 028)
  const windshieldFrame = new THREE.Group();
  windshieldFrame.position.set(0, 0.28, -0.92);
  g.add(windshieldFrame);

  // Horizontal Windshield Wiper Arm across bottom of windshield
  const wiperArm = new THREE.Group();
  wiperArm.position.set(0, -0.32, 0.05);
  windshieldFrame.add(wiperArm);
  box(1.6, 0.03, 0.02, trimMat, 0, 0, 0, wiperArm); // horizontal blade

  g.wheelRoll = wheelRoll;
  g.wiperArm = wiperArm;
  g.speedoNeedle = speedoNeedle;

  g.update = (t, steer = 0) => {
    wheelRoll.rotation.z = steer;
    speedoNeedle.rotation.z = -0.6 + Math.sin(t * 6) * 0.08 - steer * 0.5;
  };

  return g;
}
