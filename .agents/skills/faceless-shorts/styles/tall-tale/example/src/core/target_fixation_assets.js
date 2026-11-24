// Specialized 3D Assets for "The Instinct That Makes You Crash (Target Fixation)"
// Provides: buildCar, buildPoliceCruiser, buildTowTruck, buildTargetTree, buildCockpitPOV, buildHighwayScene, buildRainSystem
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

const cyl = (r1, r2, h, m, x, y, z, parent, seg = 16) => {
  const c = new THREE.Mesh(new THREE.CylinderGeometry(r1, r2, h, seg), m);
  c.position.set(x, y, z);
  c.castShadow = c.receiveShadow = true;
  if (parent) parent.add(c);
  return c;
};

// --- Volumetric Light Cone ---
export function createLightCone(len = 16, rad = 2.4, col = '#FFF5CC', opacity = 0.35) {
  const geo = new THREE.CylinderGeometry(0.12, rad, len, 24, 1, true);
  geo.translate(0, len / 2, 0);
  geo.rotateX(Math.PI / 2);
  const mat = new THREE.MeshBasicMaterial({
    color: col,
    transparent: true,
    opacity: opacity,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false
  });
  return new THREE.Mesh(geo, mat);
}

// --- High-Quality 3D Vehicle ---
export function buildCar({
  color = '#8A99A8',
  glassCol = '#1E293B',
  damaged = false,
  police = false,
  headlights = true,
  taillights = true
} = {}) {
  const g = new THREE.Group();
  const W = 2.0, L = 4.4, H = 1.35;

  // Car Paint Material
  const paintMat = new THREE.MeshStandardMaterial({
    color: police ? '#111827' : color,
    metalness: 0.6,
    roughness: 0.25
  });

  const chromeMat = new THREE.MeshStandardMaterial({
    color: '#E2E8F0',
    metalness: 0.9,
    roughness: 0.1
  });

  const glassMat = new THREE.MeshStandardMaterial({
    color: glassCol,
    roughness: 0.1,
    metalness: 0.1,
    transparent: true,
    opacity: 0.85
  });

  const blackMat = new THREE.MeshStandardMaterial({ color: '#1A202C', roughness: 0.8 });
  const tireMat = new THREE.MeshStandardMaterial({ color: '#111317', roughness: 0.9 });

  // 1. Lower Chassis
  const chassis = box(W, 0.45, L * 0.96, paintMat, 0, 0.45, 0, g);

  // 2. Cabin / Greenhouse
  const cabin = new THREE.Group();
  cabin.position.set(0, 0.65, -0.2);
  g.add(cabin);

  // Cabin roof
  box(W * 0.88, 0.08, L * 0.52, paintMat, 0, 0.72, 0, cabin);

  // Windshield (front sloped)
  const windshield = box(W * 0.86, 0.68, 0.08, glassMat, 0, 0.38, L * 0.24, cabin);
  windshield.rotation.x = 0.55;

  // Rear window (rear sloped)
  const rearWin = box(W * 0.86, 0.64, 0.08, glassMat, 0, 0.40, -L * 0.24, cabin);
  rearWin.rotation.x = -0.55;

  // Side windows
  [-1, 1].forEach((s) => {
    box(0.06, 0.48, L * 0.44, glassMat, s * (W * 0.44 - 0.01), 0.38, 0, cabin);
    // Side Mirrors
    box(0.22, 0.14, 0.14, paintMat, s * (W * 0.48 + 0.1), 0.52, L * 0.22, g);
  });

  // Front Hood & Grill
  const hood = box(W * 0.96, 0.25, L * 0.35, paintMat, 0, 0.62, L * 0.32, g);
  const grill = box(W * 0.75, 0.22, 0.08, blackMat, 0, 0.42, L * 0.49, g);
  const bumper = box(W * 1.02, 0.18, 0.22, chromeMat, 0, 0.25, L * 0.48, g);
  const rearBumper = box(W * 1.02, 0.18, 0.22, chromeMat, 0, 0.25, -L * 0.48, g);

  // 3. Headlights & Cones
  const headMat = new THREE.MeshStandardMaterial({
    color: '#FFFDF0',
    emissive: '#FFF9D2',
    emissiveIntensity: headlights ? 3.5 : 0.2
  });
  const tailMat = new THREE.MeshStandardMaterial({
    color: '#EF4444',
    emissive: '#DC2626',
    emissiveIntensity: taillights ? 2.5 : 0.2
  });

  const lightCones = [];
  [-1, 1].forEach((s) => {
    // Headlight lenses
    box(0.36, 0.18, 0.06, headMat, s * (W * 0.38), 0.50, L * 0.49, g);
    // Taillights
    box(0.36, 0.16, 0.06, tailMat, s * (W * 0.38), 0.52, -L * 0.49, g);

    if (headlights) {
      const cone = createLightCone(16, 2.2, '#FFF9E6', 0.28);
      cone.position.set(s * (W * 0.38), 0.50, L * 0.52);
      g.add(cone);
      lightCones.push(cone);
    }
  });

  // 4. Wheels
  const wheels = [];
  [
    [-W * 0.52, L * 0.30],
    [W * 0.52, L * 0.30],
    [-W * 0.52, -L * 0.30],
    [W * 0.52, -L * 0.30]
  ].forEach(([wx, wz]) => {
    const wg = new THREE.Group();
    wg.position.set(wx, 0.34, wz);
    // Tire
    const tire = cyl(0.34, 0.34, 0.24, tireMat, 0, 0, 0, wg, 20);
    tire.rotation.z = Math.PI / 2;
    // Hubcap
    const cap = cyl(0.20, 0.20, 0.25, chromeMat, 0, 0, 0, wg, 12);
    cap.rotation.z = Math.PI / 2;
    g.add(wg);
    wheels.push(wg);
  });

  // 5. Police Livery & Roof Lightbar (if police)
  let sirenBar = null;
  if (police) {
    // White doors
    [-1, 1].forEach((s) => {
      const doorPanel = box(0.04, 0.42, L * 0.45, new THREE.MeshStandardMaterial({ color: '#F8FAFC', roughness: 0.3 }), s * (W * 0.49), 0.48, 0, g);
      // Star badge on door
      const star = new THREE.Mesh(new THREE.PlaneGeometry(0.35, 0.35), new THREE.MeshBasicMaterial({
        color: '#D4AF37',
        side: THREE.DoubleSide
      }));
      star.position.set(s * (W * 0.51 + 0.01), 0.50, 0);
      star.rotation.y = s * Math.PI / 2;
      g.add(star);
    });

    // Roof Lightbar
    sirenBar = new THREE.Group();
    sirenBar.position.set(0, 1.44, -0.2);
    box(W * 0.65, 0.08, 0.18, chromeMat, 0, 0, 0, sirenBar);

    const redLight = box(0.24, 0.12, 0.14, new THREE.MeshStandardMaterial({ color: '#EF4444', emissive: '#EF4444', emissiveIntensity: 4.0 }), -W * 0.20, 0.08, 0, sirenBar);
    const blueLight = box(0.24, 0.12, 0.14, new THREE.MeshStandardMaterial({ color: '#3B82F6', emissive: '#3B82F6', emissiveIntensity: 4.0 }), W * 0.20, 0.08, 0, sirenBar);
    g.add(sirenBar);

    sirenBar.red = redLight;
    sirenBar.blue = blueLight;
  }

  // 6. Damage deformation
  if (damaged) {
    hood.rotation.x = -0.45;
    hood.position.y += 0.25;
    hood.position.z -= 0.18;
    bumper.rotation.y = 0.25;
    bumper.position.z -= 0.25;
    windshield.rotation.z = 0.15;
  }

  g.wheels = wheels;
  g.sirenBar = sirenBar;
  g.lightCones = lightCones;
  g.update = (t, steer = 0) => {
    // Spin wheels
    wheels.forEach((w) => {
      w.children.forEach((c) => (c.rotation.x += 0.15));
    });
    // Steer front wheels
    wheels[0].rotation.y = steer;
    wheels[1].rotation.y = steer;

    // Siren strobe
    if (sirenBar) {
      const flash = Math.sin(t * 18);
      sirenBar.red.material.emissiveIntensity = flash > 0 ? 5.0 : 0.2;
      sirenBar.blue.material.emissiveIntensity = flash < 0 ? 5.0 : 0.2;
    }
  };

  return g;
}

// --- Heavy-Duty Red Tow Truck ---
export function buildTowTruck() {
  const g = new THREE.Group();
  const W = 2.4, L = 6.8;
  const redMat = new THREE.MeshStandardMaterial({ color: '#DC2626', metalness: 0.5, roughness: 0.3 });
  const darkMat = new THREE.MeshStandardMaterial({ color: '#1E293B', roughness: 0.7 });
  const chromeMat = new THREE.MeshStandardMaterial({ color: '#F1F5F9', metalness: 0.95, roughness: 0.1 });
  const glassMat = new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.1, transparent: true, opacity: 0.8 });

  // Chassis Frame
  box(W * 0.85, 0.45, L, darkMat, 0, 0.45, 0, g);

  // Truck Cab (Front)
  const cab = new THREE.Group();
  cab.position.set(0, 0.65, L * 0.28);
  g.add(cab);

  box(W, 1.25, L * 0.32, redMat, 0, 0.65, 0, cab);
  // Hood
  box(W * 0.94, 0.75, L * 0.22, redMat, 0, 0.40, L * 0.24, cab);
  // Front Chrome Grill
  box(W * 0.82, 0.65, 0.12, chromeMat, 0, 0.38, L * 0.35, cab);
  // Windshield
  const ws = box(W * 0.88, 0.55, 0.08, glassMat, 0, 0.95, L * 0.16, cab);
  ws.rotation.x = 0.25;

  // Vertical Chrome Smokestacks
  [-1, 1].forEach((s) => {
    cyl(0.09, 0.09, 2.6, chromeMat, s * (W * 0.52), 1.6, -L * 0.12, cab, 16);
  });

  // Flatbed / Boom Section
  const flatbed = box(W * 0.98, 0.25, L * 0.58, darkMat, 0, 0.75, -L * 0.20, g);

  // A-Frame Crane Boom
  const boom = new THREE.Group();
  boom.position.set(0, 0.9, -L * 0.15);
  g.add(boom);

  const armL = cyl(0.08, 0.08, 3.4, redMat, -0.6, 1.3, -0.8, boom, 12);
  armL.rotation.x = -0.7;
  const armR = cyl(0.08, 0.08, 3.4, redMat, 0.6, 1.3, -0.8, boom, 12);
  armR.rotation.x = -0.7;

  // Tow Cable & Hook
  cyl(0.02, 0.02, 1.8, darkMat, 0, 1.3, -2.1, boom, 6);
  const hook = box(0.24, 0.32, 0.12, chromeMat, 0, 0.4, -2.1, boom);

  // Marquee Roof Sign ("TREE TOWING · CASH ONLY")
  const signTex = canvasTex('towsign', 512, 128, (c) => {
    c.fillStyle = '#FEF08A';
    c.fillRect(0, 0, 512, 128);
    c.strokeStyle = '#991B1B';
    c.lineWidth = 8;
    c.strokeRect(8, 8, 496, 112);
    c.fillStyle = '#991B1B';
    c.font = '900 36px Inter, sans-serif';
    c.textAlign = 'center';
    c.fillText('TREE TOWING', 256, 52);
    c.font = '900 28px Inter, sans-serif';
    c.fillStyle = '#166534';
    c.fillText('CASH ONLY · $$$', 256, 96);
  });
  const signMesh = box(2.4, 0.65, 0.12, [chromeMat, chromeMat, chromeMat, chromeMat, mat({ map: signTex }), mat({ map: signTex })], 0, 2.3, L * 0.28, g);

  // 6 Heavy Wheels
  const tireMat = new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.9 });
  [
    [-W * 0.54, L * 0.35],
    [W * 0.54, L * 0.35],
    [-W * 0.54, -L * 0.22],
    [W * 0.54, -L * 0.22],
    [-W * 0.54, -L * 0.42],
    [W * 0.54, -L * 0.42]
  ].forEach(([wx, wz]) => {
    const wg = new THREE.Group();
    wg.position.set(wx, 0.45, wz);
    const tire = cyl(0.45, 0.45, 0.32, tireMat, 0, 0, 0, wg, 20);
    tire.rotation.z = Math.PI / 2;
    cyl(0.26, 0.26, 0.34, chromeMat, 0, 0, 0, wg, 12).rotation.z = Math.PI / 2;
    g.add(wg);
  });

  return g;
}

// --- The Iconic Tree & Flashing Marquee Arrow ---
export function buildTargetTree({ chopped = false, hasSign = true } = {}) {
  const g = new THREE.Group();

  const barkMat = new THREE.MeshStandardMaterial({
    color: '#3B2219',
    roughness: 0.95,
    metalness: 0.05
  });

  const leafMat1 = new THREE.MeshStandardMaterial({ color: '#2D5A27', roughness: 0.85 });
  const leafMat2 = new THREE.MeshStandardMaterial({ color: '#3E7D35', roughness: 0.80 });
  const leafMat3 = new THREE.MeshStandardMaterial({ color: '#1E3F1A', roughness: 0.90 });

  // 1. Trunk Base / Stump
  const stump = cyl(0.58, 0.72, 1.2, barkMat, 0, 0.6, 0, g, 16);

  // Stump Top with Tree Rings (visible when chopped)
  const ringsTex = canvasTex('treerings', 256, 256, (c) => {
    c.fillStyle = '#D9A362';
    c.fillRect(0, 0, 256, 256);
    c.strokeStyle = '#8B5A2B';
    c.lineWidth = 3;
    for (let r = 15; r < 120; r += 12) {
      c.beginPath();
      c.arc(128 + Math.sin(r) * 6, 128 + Math.cos(r) * 6, r, 0, Math.PI * 2);
      c.stroke();
    }
  });
  const stumpTop = new THREE.Mesh(new THREE.CircleGeometry(0.58, 16), mat({ map: ringsTex }));
  stumpTop.rotation.x = -Math.PI / 2;
  stumpTop.position.set(0, 1.205, 0);
  g.add(stumpTop);

  // 2. Upper Trunk and Branches (if not chopped)
  const upperTree = new THREE.Group();
  g.add(upperTree);

  if (!chopped) {
    // Upper main trunk
    cyl(0.44, 0.58, 3.2, barkMat, 0, 2.8, 0, upperTree, 14);
    // Forking branches
    const b1 = cyl(0.24, 0.38, 2.4, barkMat, 0.6, 4.4, 0.4, upperTree, 10);
    b1.rotation.z = -0.4;
    b1.rotation.x = 0.2;

    const b2 = cyl(0.22, 0.36, 2.2, barkMat, -0.6, 4.3, -0.3, upperTree, 10);
    b2.rotation.z = 0.45;
    b2.rotation.x = -0.25;

    // Foliage Clumps (Multiple overlapping organic spheres)
    const clumps = [
      [0, 5.2, 0, 1.8, leafMat1],
      [1.1, 4.8, 0.6, 1.4, leafMat2],
      [-1.1, 4.7, -0.5, 1.35, leafMat3],
      [0.4, 6.0, -0.4, 1.5, leafMat2],
      [-0.5, 5.8, 0.5, 1.4, leafMat1],
      [0, 6.7, 0, 1.2, leafMat3]
    ];
    clumps.forEach(([cx, cy, cz, cr, cm]) => {
      const leaf = new THREE.Mesh(new THREE.DodecahedronGeometry(cr, 1), cm);
      leaf.position.set(cx, cy, cz);
      leaf.castShadow = leaf.receiveShadow = true;
      upperTree.add(leaf);
    });
  }

  // 3. Giant Flashing Marquee Sign ("DON'T HIT THIS TREE")
  const bulbs = [];
  let arrowSignGroup = null;

  if (hasSign) {
    arrowSignGroup = new THREE.Group();
    // Positioned at eye level (y: 2.2m on trunk, or on wooden post when chopped)
    arrowSignGroup.position.set(0, chopped ? 1.6 : 2.4, 0.75);
    g.add(arrowSignGroup);

    if (chopped) {
      // Wooden mounting post from stump to sign
      cyl(0.08, 0.08, 1.4, barkMat, 0, -0.6, -0.05, arrowSignGroup, 8);
    }

    // A. Center White Warning Board
    const warningTex = canvasTex('dont_hit_tree_board', 256, 320, (c) => {
      c.fillStyle = '#FFFDF5';
      c.fillRect(0, 0, 256, 320);
      c.strokeStyle = '#B91C1C';
      c.lineWidth = 12;
      c.strokeRect(8, 8, 240, 304);
      c.fillStyle = '#B91C1C';
      c.font = '900 52px Inter, sans-serif';
      c.textAlign = 'center';
      c.fillText("DON'T", 128, 75);
      c.fillText("HIT", 128, 145);
      c.fillText("THIS", 128, 215);
      c.fillText("TREE", 128, 285);
    });

    const boardMat = new THREE.MeshStandardMaterial({
      map: warningTex,
      roughness: 0.3,
      metalness: 0.1
    });
    const centerBoard = box(1.3, 1.6, 0.08, boardMat, 0, 0, 0, arrowSignGroup);

    // B. Curved Horseshoe / Arch Border around Board
    const redMarqueeMat = new THREE.MeshStandardMaterial({
      color: '#DC2626',
      roughness: 0.35,
      metalness: 0.2
    });

    // Arch Frame Top & Sides
    box(1.7, 0.22, 0.16, redMarqueeMat, 0, 0.9, 0, arrowSignGroup); // Top
    box(0.22, 1.8, 0.16, redMarqueeMat, -0.75, 0.0, 0, arrowSignGroup); // Left
    box(0.22, 1.8, 0.16, redMarqueeMat, 0.75, 0.0, 0, arrowSignGroup); // Right
    box(1.7, 0.22, 0.16, redMarqueeMat, 0, -0.9, 0, arrowSignGroup); // Bottom

    // Arrow pointer at bottom pointing right toward tree
    const arrowMesh = box(0.5, 0.5, 0.16, redMarqueeMat, 0.9, -0.9, 0, arrowSignGroup);
    arrowMesh.rotation.z = -0.78;

    // C. Dual Perimeter Rows of Glowing Incandescent Bulbs
    const bulbPts = [
      // Top row
      [-0.65, 0.9], [-0.35, 0.9], [0, 0.9], [0.35, 0.9], [0.65, 0.9],
      // Bottom row
      [-0.65, -0.9], [-0.35, -0.9], [0, -0.9], [0.35, -0.9], [0.65, -0.9],
      // Left edge
      [-0.75, 0.6], [-0.75, 0.2], [-0.75, -0.2], [-0.75, -0.6],
      // Right edge
      [0.75, 0.6], [0.75, 0.2], [0.75, -0.2], [0.75, -0.6]
    ];

    bulbPts.forEach(([bx, by], i) => {
      const bMat = new THREE.MeshStandardMaterial({
        color: '#FFFBEB',
        emissive: '#FDE047',
        emissiveIntensity: 4.5
      });
      const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.08, 12, 10), bMat);
      bulb.position.set(bx, by, 0.12);
      arrowSignGroup.add(bulb);
      bulbs.push(bulb);
    });
  }

  g.upperTree = upperTree;
  g.arrowSign = arrowSignGroup;
  g.bulbs = bulbs;

  g.update = (t) => {
    // Sequential chasing / flashing lights
    bulbs.forEach((b, i) => {
      const phase = (i + Math.floor(t * 10)) % 3 === 0;
      b.material.emissiveIntensity = phase ? 6.0 : 0.4;
    });
  };

  return g;
}

// --- First-Person Driver Cockpit POV ---
export function buildCockpitPOV() {
  const g = new THREE.Group();
  const dashMat = new THREE.MeshStandardMaterial({ color: '#0F172A', roughness: 0.85 });
  const trimMat = new THREE.MeshStandardMaterial({ color: '#94A3B8', metalness: 0.8, roughness: 0.2 });
  const wheelMat = new THREE.MeshStandardMaterial({ color: '#475569', roughness: 0.3, metalness: 0.4 });
  const blackMat = new THREE.MeshStandardMaterial({ color: '#1A202C', roughness: 0.8 });

  // Interior Cabin Glow Light (illuminates steering wheel & driver hands)
  const cabinLight = new THREE.PointLight('#38BDF8', 3.5, 3.5, 1.0);
  cabinLight.position.set(-0.35, 0.45, -0.25);
  g.add(cabinLight);

  const dashGlow = new THREE.PointLight('#F97316', 1.8, 2.0, 1.2);
  dashGlow.position.set(-0.35, 0.05, -0.75);
  g.add(dashGlow);

  // 1. Dashboard Base
  const dash = box(3.2, 0.55, 1.4, dashMat, 0, -0.35, -0.85, g);
  dash.rotation.x = 0.18;

  // Center Air Vents & Hazard Switch
  box(0.55, 0.22, 0.08, trimMat, 0.6, -0.18, -0.82, g);
  box(0.12, 0.12, 0.09, new THREE.MeshStandardMaterial({ color: '#EF4444', emissive: '#DC2626', emissiveIntensity: 1.5 }), 0.6, -0.05, -0.82, g);

  // 2. Instrument Gauge Cluster (Speedometer & Tachometer)
  const gaugeTex = canvasTex('gauges', 512, 256, (c) => {
    c.fillStyle = '#05070A';
    c.fillRect(0, 0, 512, 256);
    // Draw Speedo Dial Left
    const drawDial = (cx, cy, maxVal, label) => {
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
      c.fillText('MPH', cx, cy + 60);
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
    drawDial(130, 125, 120, '65');
    drawDial(380, 125, 8, '3.2');
  });

  const gaugeScreen = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 0.55), new THREE.MeshBasicMaterial({
    map: gaugeTex,
    toneMapped: false
  }));
  gaugeScreen.position.set(-0.35, -0.08, -0.84);
  gaugeScreen.rotation.x = -0.15;
  g.add(gaugeScreen);

  // Glowing Orange Speedometer Needle
  const speedoNeedle = new THREE.Mesh(
    new THREE.BoxGeometry(0.015, 0.16, 0.01),
    new THREE.MeshBasicMaterial({ color: '#F97316' })
  );
  speedoNeedle.position.set(-0.64, -0.06, -0.82);
  speedoNeedle.geometry.translate(0, 0.08, 0);
  g.add(speedoNeedle);

  // 3. Steering Wheel (Torus Rim + Column + Spokes)
  const wheelPivot = new THREE.Group();
  wheelPivot.position.set(-0.35, 0.08, -0.42);
  wheelPivot.rotation.x = 0.28;
  g.add(wheelPivot);

  const wheelRoll = new THREE.Group();
  wheelPivot.add(wheelRoll);

  // Rim
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.44, 0.045, 16, 36), wheelMat);
  wheelRoll.add(rim);

  // Central Hub & 3 Spokes
  cyl(0.14, 0.14, 0.08, trimMat, 0, 0, 0, wheelRoll, 16).rotation.x = Math.PI / 2;
  box(0.82, 0.07, 0.04, wheelMat, 0, 0, 0, wheelRoll);
  box(0.07, 0.40, 0.04, wheelMat, 0, -0.20, 0, wheelRoll);

  // 4. Cartoon Hands Gripping the Steering Wheel (Left & Right)
  const handTex = canvasTex('driverhand', 128, 128, (c) => {
    c.lineCap = 'round';
    c.lineJoin = 'round';
    c.fillStyle = '#FFFFFF';
    c.strokeStyle = INK;
    c.lineWidth = 8;
    // Stylized toon fist with thumb curled
    c.beginPath();
    c.roundRect(24, 24, 80, 80, [20, 20, 20, 20]);
    c.fill();
    c.stroke();
    // Finger segment creases
    c.beginPath();
    c.moveTo(50, 24); c.lineTo(50, 75);
    c.moveTo(76, 24); c.lineTo(76, 75);
    c.stroke();
  });

  const handMat = new THREE.MeshBasicMaterial({ map: handTex, transparent: true, side: THREE.DoubleSide });
  const handL = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.32), handMat);
  handL.position.set(-0.42, 0.18, 0.08);
  handL.rotation.z = 0.45;
  wheelRoll.add(handL);

  const handR = new THREE.Mesh(new THREE.PlaneGeometry(0.32, 0.32), handMat);
  handR.position.set(0.42, 0.18, 0.08);
  handR.rotation.z = -0.45;
  handR.scale.x = -1; // mirror right hand
  wheelRoll.add(handR);

  // 5. Windshield & Moving Wipers
  const windshieldFrame = new THREE.Group();
  windshieldFrame.position.set(0, 0.25, -0.92);
  g.add(windshieldFrame);

  // A-Pillars (Left and Right frame)
  box(0.14, 1.8, 0.14, trimMat, -1.3, 0.35, 0.25, windshieldFrame).rotation.z = 0.28;
  box(0.14, 1.8, 0.14, trimMat, 1.3, 0.35, 0.25, windshieldFrame).rotation.z = -0.28;

  // Rearview Mirror
  const mirror = box(0.34, 0.12, 0.06, trimMat, 0.2, 0.85, -0.05, windshieldFrame);
  mirror.rotation.y = -0.15;

  // Wipers (Pivot from bottom of windshield)
  const wipers = [];
  [-0.45, 0.45].forEach((wx) => {
    const wp = new THREE.Group();
    wp.position.set(wx, -0.35, 0.05);
    windshieldFrame.add(wp);
    // Wiper Arm & Blade
    cyl(0.015, 0.015, 0.65, blackMat, 0, 0.32, 0, wp).rotation.z = 0;
    box(0.02, 0.72, 0.02, blackMat, 0.04, 0.32, 0, wp);
    wipers.push(wp);
  });

  g.wheelPivot = wheelPivot;
  g.wheelRoll = wheelRoll;
  g.wipers = wipers;
  g.speedoNeedle = speedoNeedle;

  g.update = (t, steer = 0, wiperSpeed = 4.5) => {
    // Steer wheel & hands smoothly
    wheelRoll.rotation.z = steer;

    // Needle bounce
    speedoNeedle.rotation.z = -0.6 + Math.sin(t * 6) * 0.08 - steer * 0.5;

    // Wiper swing (back and forth)
    const wipe = Math.sin(t * wiperSpeed);
    wipers.forEach((w) => {
      w.rotation.z = wipe * 0.85 + 0.45;
    });
  };

  return g;
}

// --- 3D Highway Environment ---
export function buildHighwayScene({ len = 140, wet = false, night = false } = {}) {
  const scene = new THREE.Scene();

  if (night) {
    scene.background = new THREE.Color('#060913');
    scene.fog = new THREE.FogExp2('#070B16', 0.022);
  } else {
    scene.background = new THREE.Color('#60A5FA');
    scene.fog = new THREE.FogExp2('#93C5FD', 0.008);
  }

  // 1. Asphalt Road Texture with Double Yellow Lines
  const roadTex = canvasTex('asphalt_road_' + wet, 512, 1024, (c) => {
    c.fillStyle = wet ? '#181C24' : '#2A2E38';
    c.fillRect(0, 0, 512, 1024);

    // Grain
    for (let i = 0; i < 3500; i++) {
      c.fillStyle = (i % 2 === 0) ? '#1E232E' : '#323744';
      c.fillRect((i * 137) % 512, (i * 269) % 1024, 2, 2);
    }

    // Double Solid Yellow Lines down middle
    c.fillStyle = '#EAB308';
    c.fillRect(250, 0, 5, 1024);
    c.fillRect(257, 0, 5, 1024);

    // White Shoulder Dashes on edges
    c.fillStyle = '#E2E8F0';
    for (let y = 0; y < 1024; y += 96) {
      c.fillRect(40, y, 6, 48);
      c.fillRect(466, y, 6, 48);
    }
  });

  const roadMat = new THREE.MeshStandardMaterial({
    map: roadTex,
    roughness: wet ? 0.12 : 0.75,
    metalness: wet ? 0.25 : 0.05
  });

  const road = new THREE.Mesh(new THREE.PlaneGeometry(9.0, len), roadMat);
  road.rotation.x = -Math.PI / 2;
  road.position.set(0, 0.01, -len / 2 + 15);
  road.receiveShadow = true;
  scene.add(road);

  // 2. Grassy / Desert Terrain on Both Sides
  const groundTex = canvasTex('terrain_' + night, 512, 512, (c) => {
    c.fillStyle = night ? '#0F1E13' : '#4E7E36';
    c.fillRect(0, 0, 512, 512);
    for (let i = 0; i < 2000; i++) {
      c.fillStyle = night ? '#152B1B' : '#5C9340';
      c.fillRect((i * 97) % 512, (i * 179) % 512, 3, 3);
    }
  });

  const groundMat = new THREE.MeshStandardMaterial({
    map: groundTex,
    roughness: 0.9,
    metalness: 0.0
  });

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(240, len + 60), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(0, 0, -len / 2 + 15);
  ground.receiveShadow = true;
  scene.add(ground);

  // 3. Wooden Telephone Poles & Sagging Power Lines along left side
  const woodMat = new THREE.MeshStandardMaterial({ color: '#4A3425', roughness: 0.9 });
  const wireMat = new THREE.MeshBasicMaterial({ color: '#1E293B' });

  for (let z = 10; z > -len; z -= 22) {
    const pole = cyl(0.14, 0.18, 9.5, woodMat, -6.5, 4.75, z, scene, 8);
    box(2.2, 0.12, 0.12, woodMat, -6.5, 9.1, z, scene);
    // Crossarm insulators
    [-0.9, 0.9].forEach((ix) => {
      cyl(0.04, 0.04, 0.2, wireMat, -6.5 + ix, 9.25, z, scene, 6);
    });
  }

  // 4. Lighting Rig
  if (night) {
    const hemi = new THREE.HemisphereLight('#1E293B', '#090D16', 0.45);
    scene.add(hemi);

    const moon = new THREE.DirectionalLight('#94A3B8', 0.8);
    moon.position.set(-15, 25, 10);
    moon.castShadow = true;
    moon.shadow.mapSize.set(1024, 1024);
    scene.add(moon);
  } else {
    const sun = new THREE.DirectionalLight('#FFF7ED', 2.8);
    sun.position.set(18, 30, 20);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, {
      left: -20, right: 20, top: 20, bottom: -20, near: 1, far: 80
    });
    sun.shadow.bias = -0.0004;
    scene.add(sun);

    const hemi = new THREE.HemisphereLight('#BAE6FD', '#475569', 1.1);
    scene.add(hemi);
  }

  return { scene };
}

// --- Dynamic 3D Rain Particle System ---
export function buildRainSystem(count = 2500) {
  const geo = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 6);
  const speeds = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    const x = (Math.random() - 0.5) * 36;
    const y = Math.random() * 24;
    const z = (Math.random() - 0.5) * 50 - 10;
    const len = 0.55 + Math.random() * 0.45;

    positions[i * 6 + 0] = x;
    positions[i * 6 + 1] = y;
    positions[i * 6 + 2] = z;

    // Wind tilt (-15 degrees X, downward Y)
    positions[i * 6 + 3] = x - 0.12;
    positions[i * 6 + 4] = y - len;
    positions[i * 6 + 5] = z;

    speeds[i] = 22 + Math.random() * 12;
  }

  geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  const mat = new THREE.LineBasicMaterial({
    color: '#93C5FD',
    transparent: true,
    opacity: 0.55,
    blending: THREE.AdditiveBlending
  });

  const lines = new THREE.LineSegments(geo, mat);

  lines.update = (dt) => {
    const pos = geo.attributes.position.array;
    for (let i = 0; i < count; i++) {
      const dropSpeed = speeds[i] * dt;
      pos[i * 6 + 1] -= dropSpeed;
      pos[i * 6 + 4] -= dropSpeed;
      pos[i * 6 + 0] -= dropSpeed * 0.12;
      pos[i * 6 + 3] -= dropSpeed * 0.12;

      // Wrap around
      if (pos[i * 6 + 1] < 0) {
        pos[i * 6 + 1] = 22 + Math.random() * 4;
        pos[i * 6 + 4] = pos[i * 6 + 1] - 0.7;
        pos[i * 6 + 0] = (Math.random() - 0.5) * 36;
        pos[i * 6 + 3] = pos[i * 6 + 0] - 0.12;
      }
    }
    geo.attributes.position.needsUpdate = true;
  };

  return lines;
}
