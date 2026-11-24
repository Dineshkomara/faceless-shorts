#!/usr/bin/env python3
"""setup_backgrounds.py - Online reference sourcing & atmospheric background environment setup.

Discovers the scene environments required by script.json, searches Wikimedia Commons
and Openverse for authentic, high-resolution photography and historical art, formats them into
9:16 vertical (1080x1920) and 2:1 panoramic (2160x1920) cinematic backdrops, applies subtle
vignette and atmospheric color grading, and exports metadata to data/backgrounds.json and
src/core/backgrounds.js.

Usage:
  python3 scripts/setup_backgrounds.py <project_dir>
"""

import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

USER_AGENT = "FacelessShortsStudio/2.0 (contact@faceless-shorts.local; bot) Python-urllib/3.11"

ENVIRONMENT_PROFILES = [
    {
        "id": "battlefield",
        "keywords": ["battlefield", "army", "war", "armies", "banner", "yuddham", "kurukshetra", "soldier"],
        "search_query": "Battlefield sunset dramatic landscape",
        "fallback_query": "Sunset dramatic horizon landscape clouds",
        "lighting": {"ambient": "#4A3B32", "sun": "#F39C12", "fog": "#2C1B18", "fog_density": 0.015}
    },
    {
        "id": "royal_court",
        "keywords": ["court", "palace", "durbar", "sabha", "throne", "brahmin", "king", "ruler", "monarch"],
        "search_query": "Hampi stone temple pillars interior",
        "fallback_query": "Ancient stone palace pillars hall",
        "lighting": {"ambient": "#5D4037", "sun": "#FFD54F", "fog": "#3E2723", "fog_density": 0.01}
    },
    {
        "id": "solar_sky",
        "keywords": ["sun", "surya", "celestial", "gold", "radiance", "kunti", "baby", "divine", "sky"],
        "search_query": "Golden sunrise dramatic clouds sky",
        "fallback_query": "Sunrise golden hour clouds mountains",
        "lighting": {"ambient": "#7E5109", "sun": "#FFF9C4", "fog": "#B7950B", "fog_density": 0.012}
    },
    {
        "id": "temple_corridor",
        "keywords": ["temple", "shrine", "pillar", "sanctum", "garbhagriha", "lepakshi", "puri", "yaganti", "mandir"],
        "search_query": "Ancient Hindu stone temple corridor pillars",
        "fallback_query": "Indian stone temple architecture",
        "lighting": {"ambient": "#3E2723", "sun": "#FFA000", "fog": "#1A0F0D", "fog_density": 0.02}
    },
    {
        "id": "himalayas",
        "keywords": ["mountain", "himalayas", "sanjeevani", "peak", "snow", "altitude", "range"],
        "search_query": "Himalayas snow mountain landscape",
        "fallback_query": "Snowy mountain peaks dramatic sky",
        "lighting": {"ambient": "#2C3E50", "sun": "#EAECEE", "fog": "#1B2631", "fog_density": 0.012}
    },
    {
        "id": "forest_ashram",
        "keywords": ["forest", "ashram", "woods", "trees", "hermitage", "aranyam", "river", "nature"],
        "search_query": "Ancient Indian forest banyan trees morning mist",
        "fallback_query": "Misty ancient forest atmospheric landscape",
        "lighting": {"ambient": "#1E3F20", "sun": "#A9DFBF", "fog": "#142616", "fog_density": 0.018}
    },
    {
        "id": "biology_interior",
        "keywords": ["cells", "gut", "mucus", "bacteria", "microbial", "colon", "blood", "vessel", "organ"],
        "search_query": "Microscopic biological cell tissue glowing interior",
        "fallback_query": "Human cell bioluminescence microscope",
        "lighting": {"ambient": "#4A148C", "sun": "#E91E63", "fog": "#1A0033", "fog_density": 0.025}
    },
    {
        "id": "deep_space",
        "keywords": ["space", "universe", "stars", "galaxy", "nebula", "astronomy", "cosmos", "quantum"],
        "search_query": "Deep space nebula stars hubble astronomy",
        "fallback_query": "Milky way galaxy stars night landscape",
        "lighting": {"ambient": "#0B132B", "sun": "#5BC0BE", "fog": "#050A14", "fog_density": 0.01}
    }
]


def log(msg):
    print(f"[setup_backgrounds] {msg}", flush=True)


def extract_environments(script):
    full_text = (script.get("title", "") + " " + " ".join(l.get("text", "") for l in script.get("lines", []))).lower()
    sources_text = " ".join(script.get("sources", [])).lower()
    combined = full_text + " " + sources_text

    matched_envs = []
    seen = set()

    for env in ENVIRONMENT_PROFILES:
        score = sum(1 for kw in env["keywords"] if kw in combined)
        if score > 0 and env["id"] not in seen:
            seen.add(env["id"])
            matched_envs.append((score, env))

    # Sort by match score
    matched_envs.sort(key=lambda x: x[0], reverse=True)
    results = [env for _, env in matched_envs[:3]]

    # Always ensure at least one primary atmospheric setting
    if not results:
        results.append(ENVIRONMENT_PROFILES[0])

    return results


def search_online_background(query):
    # 1. Search Wikimedia Commons
    try:
        clean_q = urllib.parse.quote(query)
        url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={clean_q}&gsrnamespace=6&gsrlimit=8&prop=imageinfo&iiprop=url|mime|size"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                info = p.get("imageinfo", [{}])[0]
                mime = info.get("mime", "").lower()
                w = info.get("width", 0)
                h = info.get("height", 0)
                furl = info.get("url", "")
                is_valid_format = mime in ("image/jpeg", "image/png", "image/webp") and any(furl.lower().split('?')[0].endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp'))
                if is_valid_format and w >= 1000 and h >= 700:
                    img_url = furl
                    if img_url:
                        log(f"Found atmospheric backdrop ({w}x{h}): {img_url[:75]}...")
                        return img_url
    except Exception:
        pass

    # 2. Search Openverse
    try:
        clean_q = urllib.parse.quote(query)
        url = f"https://api.openverse.org/v1/images/?q={clean_q}&page_size=5"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
            for r in data.get("results", []):
                durl = r.get("url")
                if durl:
                    log(f"Found Openverse backdrop: {durl[:75]}...")
                    return durl
    except Exception:
        pass

    return None


def download_image(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def apply_cinematic_atmosphere(img, vertical=True):
    """Crops to 1080x1920 (or 2160x1920 panorama) and applies cinematic atmospheric grading."""
    target_size = (1080, 1920) if vertical else (2160, 1920)
    formatted = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS)

    # Slight contrast and color saturation boost for vibrant video display
    enhancer = ImageEnhance.Contrast(formatted)
    formatted = enhancer.enhance(1.15)
    color_enhancer = ImageEnhance.Color(formatted)
    formatted = color_enhancer.enhance(1.18)

    # Create smooth vignette to keep captions and UI readable
    vignette = Image.new("L", target_size, 255)
    draw_vig = ImageDraw.Draw(vignette)
    w, h = target_size
    # Darken top and bottom
    draw_vig.rectangle([(0, 0), (w, int(h * 0.14))], fill=140)
    draw_vig.rectangle([(0, int(h * 0.78)), (w, h)], fill=100)

    # Blur mask effect (gradient)
    gradient = Image.new("RGBA", target_size, (0, 0, 0, 0))
    draw_grad = ImageDraw.Draw(gradient)
    for y in range(int(h * 0.22)):
        alpha = int(140 * (1.0 - y / (h * 0.22)))
        draw_grad.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    for y in range(int(h * 0.75), h):
        alpha = int(180 * ((y - h * 0.75) / (h * 0.25)))
        draw_grad.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    # Composite vignette over image
    formatted = formatted.convert("RGBA")
    formatted = Image.alpha_composite(formatted, gradient).convert("RGB")
    return formatted


def generate_js_background_module(backgrounds, js_path):
    """Generates Three.js atmospheric background loader module."""
    js_content = f"""// Auto-generated Atmospheric Background Environment Module
// Provides Three.js scene environment maps, panoramic backdrops, and lighting setups.

import * as THREE from 'three';

export const BACKGROUNDS_DATA = {json.dumps(backgrounds, indent=2, ensure_ascii=False)};

const textureLoader = new THREE.TextureLoader();
const bgCache = new Map();

/**
 * Loads and applies an authentic atmospheric environment to a Three.js scene.
 * @param {{THREE.Scene}} scene - Target Three.js scene
 * @param {{string}} envId - Environment ID (e.g. 'battlefield', 'royal_court', 'solar_sky')
 */
export function applyAtmosphere(scene, envId) {{
  const bg = BACKGROUNDS_DATA.find(b => b.id === envId) || BACKGROUNDS_DATA[0];
  if (!bg || !bg.vertical_image) return;

  let tex = bgCache.get(bg.vertical_image);
  if (!tex) {{
    tex = textureLoader.load(bg.vertical_image);
    tex.colorSpace = THREE.SRGBColorSpace;
    bgCache.set(bg.vertical_image, tex);
  }}

  scene.background = tex;

  // Configure atmospheric fog if available
  if (bg.lighting?.fog) {{
    scene.fog = new THREE.FogExp2(bg.lighting.fog, bg.lighting.fog_density || 0.015);
  }}
}}

/**
 * Creates a curved 3D panoramic backdrop plane for camera panning effects.
 */
export function createPanoramicBackdrop(envId, radius = 24) {{
  const bg = BACKGROUNDS_DATA.find(b => b.id === envId) || BACKGROUNDS_DATA[0];
  if (!bg) return new THREE.Group();

  const file = bg.panorama_image || bg.vertical_image;
  let tex = bgCache.get(file);
  if (!tex) {{
    tex = textureLoader.load(file);
    tex.colorSpace = THREE.SRGBColorSpace;
    bgCache.set(file, tex);
  }}

  const geo = new THREE.CylinderGeometry(radius, radius, 36, 32, 1, true, -Math.PI / 2, Math.PI);
  const mat = new THREE.MeshBasicMaterial({{ map: tex, side: THREE.BackSide }});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.y = 8;
  return mesh;
}}
"""
    js_path.write_text(js_content, encoding="utf-8")
    log(f"Generated Three.js background module: {js_path.name}")


def main():
    proj_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    script_path = proj_dir / "script.json"
    if not script_path.exists():
        log(f"No script.json found in {proj_dir}")
        sys.exit(1)

    script = json.loads(script_path.read_text(encoding="utf-8"))
    environments = extract_environments(script)

    assets_dir = proj_dir / "assets" / "backgrounds"
    assets_dir.mkdir(parents=True, exist_ok=True)
    data_dir = proj_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    log(f"Setting up {len(environments)} atmospheric environment(s)...")

    processed = []
    for env in environments:
        env_id = env["id"]
        search_q = env["search_query"]
        log(f"Searching online for '{env_id}' environment: \"{search_q}\"...")

        img_url = search_online_background(search_q)
        if not img_url and env.get("fallback_query"):
            log(f"  Trying fallback query: \"{env['fallback_query']}\"...")
            img_url = search_online_background(env["fallback_query"])

        vert_path = assets_dir / f"bg_{env_id}.jpg"
        pano_path = assets_dir / f"pano_{env_id}.jpg"

        if img_url:
            try:
                raw_bytes = download_image(img_url)
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")

                # 1. 9:16 Vertical background
                vert_img = apply_cinematic_atmosphere(img, vertical=True)
                vert_img.save(vert_path, format="JPEG", quality=92)

                # 2. 2:1 Wide Panorama
                pano_img = apply_cinematic_atmosphere(img, vertical=False)
                pano_img.save(pano_path, format="JPEG", quality=90)

                log(f"  ✓ Vertical 9:16 backdrop generated: {vert_path.name} (1080x1920)")
                log(f"  ✓ Panoramic backdrop generated: {pano_path.name} (2160x1920)")
            except Exception as e:
                log(f"  ⚠ Failed downloading/processing backdrop for {env_id}: {e}")
        else:
            log(f"  ⚠ No online image found for {env_id}, generating procedural gradient...")
            # Procedural gradient backdrop
            grad = Image.new("RGB", (1080, 1920), color=env["lighting"]["ambient"])
            draw_grad = ImageDraw.Draw(grad)
            for y in range(1920):
                alpha = y / 1920.0
                draw_grad.line([(0, y), (1080, y)], fill=env["lighting"]["sun"])
            grad.save(vert_path, format="JPEG")
            grad.resize((2160, 1920)).save(pano_path, format="JPEG")

        processed.append({
            "id": env_id,
            "search_query": search_q,
            "source_url": img_url or "procedural",
            "vertical_image": str(vert_path.relative_to(proj_dir)),
            "panorama_image": str(pano_path.relative_to(proj_dir)),
            "lighting": env["lighting"]
        })

    # Save to data/backgrounds.json
    bg_json_path = data_dir / "backgrounds.json"
    bg_json_path.write_text(json.dumps({
        "project": proj_dir.name,
        "backgrounds": processed
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Wrote metadata to {bg_json_path.relative_to(proj_dir)}")

    # Generate src/core/backgrounds.js
    core_dir = proj_dir / "src" / "core"
    if core_dir.exists():
        generate_js_background_module(processed, core_dir / "backgrounds.js")

    log("Atmospheric background environment setup COMPLETE.")


if __name__ == "__main__":
    main()
