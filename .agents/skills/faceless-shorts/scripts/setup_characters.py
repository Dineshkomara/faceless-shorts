#!/usr/bin/env python3
"""setup_characters.py - Online reference sourcing & character asset generation.

Searches Wikipedia, Wikimedia Commons, and cultural archives for authentic reference
portraits/paintings of characters in the script. Generates formatted character sprites,
extracts authentic color palettes, produces character cards, and registers them in data/characters.json
and src/core/characters.js.

Usage:
  python3 scripts/setup_characters.py <project_dir>
"""

import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

USER_AGENT = "FacelessShortsStudio/2.0 (contact@faceless-shorts.local; bot) Python-urllib/3.11"

# Known canonical figures for instant accurate query mapping
ICONOGRAPHY_DB = {
    # Epic & Mythological (Indian / Telugu)
    "karna": {
        "search_term": "Karna",
        "name": "Karna (కర్ణుడు)",
        "role": "Solar warrior of Mahabharata, famed for invulnerable golden armor",
        "attributes": ["golden kavacha armor", "kundala earrings", "radiant solar aura", "bow Vijaya"],
        "default_colors": {"skin": "#D4A373", "armor": "#FFD700", "attire": "#B83B5E", "aura": "#FFA500"}
    },
    "indra": {
        "search_term": "Indra",
        "name": "Indra (ఇంద్రుడు)",
        "role": "King of Devas, god of rain and lightning",
        "attributes": ["golden crown", "vajra thunderbolt", "white elephant Airavata", "regal silk"],
        "default_colors": {"skin": "#E0AC69", "armor": "#E8B83C", "attire": "#2B580C", "aura": "#4A90E2"}
    },
    "hanuman": {
        "search_term": "Hanuman",
        "name": "Hanuman (హనుమంతుడు)",
        "role": "Embodiment of devotion, strength, and protector",
        "attributes": ["golden gada mace", "sanjeevani mountain", "saffron dhoti", "sacred tail"],
        "default_colors": {"skin": "#E28743", "armor": "#E28743", "attire": "#D35400", "aura": "#F39C12"}
    },
    "krishna": {
        "search_term": "Krishna",
        "name": "Sri Krishna (శ్రీకృష్ణుడు)",
        "role": "Supreme philosopher, guide of Gita, lifting Govardhana",
        "attributes": ["peacock feather crown", "bansuri flute", "pitambara yellow silk", "blue complexion"],
        "default_colors": {"skin": "#5DADE2", "armor": "#F4D03F", "attire": "#F1C40F", "aura": "#85C1E9"}
    },
    "shiva": {
        "search_term": "Shiva",
        "name": "Lord Shiva (పరమశివుడు)",
        "role": "The cosmic yogi, destroyer of ignorance",
        "attributes": ["third eye", "crescent moon", "trishula trident", "vasuki serpent"],
        "default_colors": {"skin": "#85C1E9", "armor": "#A6ACAF", "attire": "#AF601A", "aura": "#D5D8DC"}
    },
    "ganesha": {
        "search_term": "Ganesha",
        "name": "Lord Ganesha (గణపతి)",
        "role": "Lord of beginnings and remover of obstacles",
        "attributes": ["elephant head", "curved trunk", "single broken tusk", "modaka sweet"],
        "default_colors": {"skin": "#EDBB99", "armor": "#F4D03F", "attire": "#C0392B", "aura": "#F39C12"}
    },
    "surya": {
        "search_term": "Surya",
        "name": "Surya Bhagavan (సూర్యదేవుడు)",
        "role": "Solar deity, giver of light and life",
        "attributes": ["radiant solar rays", "seven-horse chariot", "golden lotus", "divine radiance"],
        "default_colors": {"skin": "#F39C12", "armor": "#F1C40F", "attire": "#E67E22", "aura": "#F9E79F"}
    },
    "tenali rama": {
        "search_term": "Tenali Rama",
        "name": "Tenali Ramakrishna (తెనాలి రామకృష్ణ)",
        "role": "Legendary court jester, poet and scholar of Krishnadevaraya",
        "attributes": ["scholarly angavastram", "tilaka mark", "palm-leaf scroll", "witty smile"],
        "default_colors": {"skin": "#D4A373", "armor": "#FFFFFF", "attire": "#E5E7E9", "aura": "#F5B041"}
    },
    "vikram": {
        "search_term": "Vikramaditya",
        "name": "Vikramaditya (విక్రమార్కుడు)",
        "role": "Legendary king carrying Betal through the night cremation ground",
        "attributes": ["kirita crown", "royal mustache", "warrior sword", "regal navy silk"],
        "default_colors": {"skin": "#D4A373", "armor": "#F4D03F", "attire": "#1F4E79", "aura": "#3498DB"}
    },
    "betal": {
        "search_term": "Vetala",
        "name": "Betal (బేతాళుడు)",
        "role": "Spectral vampire spirit hanging from Vikram's shoulder posing riddles",
        "attributes": ["pale ghostly skin", "vampiric fangs", "wild black locks", "dark shroud"],
        "default_colors": {"skin": "#D8DEE4", "armor": "#3B3346", "attire": "#2C2A38", "aura": "#9B59B6"}
    },
    "king": {
        "search_term": "Maharaja",
        "name": "Maharaja (మహారాజు)",
        "role": "King of Varanasi who tests the sensitivity of the three brothers",
        "attributes": ["mukut crown", "royal mustache", "ruby silk robe", "pearl necklace"],
        "default_colors": {"skin": "#E2A772", "armor": "#FFD700", "attire": "#8E1616", "aura": "#E67E22"}
    },
    "pandit": {
        "search_term": "Pandit",
        "name": "Pandita (పండితుడు)",
        "role": "Brahmin scholar possessing extraordinary superhuman sensory faculty",
        "attributes": ["sacred thread", "vermilion tilak", "scholarly shawl", "cotton dhoti"],
        "default_colors": {"skin": "#D4A373", "armor": "#F39C12", "attire": "#E8734A", "aura": "#F1C40F"}
    },
    # Scientific & Historical (English)
    "einstein": {
        "search_term": "Albert_Einstein",
        "name": "Albert Einstein",
        "role": "Theoretical physicist, father of general relativity",
        "attributes": ["wild white hair", "tweed sweater", "chalkboard equations", "mustache"],
        "default_colors": {"skin": "#F5CBA7", "armor": "#566573", "attire": "#2C3E50", "aura": "#BDC3C7"}
    },
    "galileo": {
        "search_term": "Galileo_Galilei",
        "name": "Galileo Galilei",
        "role": "Father of modern observational astronomy",
        "attributes": ["refracting telescope", "renaissance collar", "bearded astronomer", "celestial globe"],
        "default_colors": {"skin": "#EDBB99", "armor": "#784212", "attire": "#1B2631", "aura": "#FAD7A0"}
    },
    "darwin": {
        "search_term": "Charles_Darwin",
        "name": "Charles Darwin",
        "role": "Naturalist and evolutionary biologist",
        "attributes": ["long flowing beard", "field notebook", "fossil specimen", "magnifying glass"],
        "default_colors": {"skin": "#F5CBA7", "armor": "#4A235A", "attire": "#17202A", "aura": "#D7BDE2"}
    }
}


def log(msg):
    print(f"[setup_characters] {msg}", flush=True)


def extract_characters_from_script(script):
    # 1. If explicit characters exist
    if script.get("characters") and isinstance(script["characters"], list):
        return script["characters"]

    # 2. Match known characters from text
    full_text = script.get("title", "") + " " + " ".join(l.get("text", "") for l in script.get("lines", []))
    sources_text = " ".join(script.get("sources", []))
    combined = (full_text + " " + sources_text).lower()

    detected = []
    seen = set()

    # Check known database
    for key, info in ICONOGRAPHY_DB.items():
        # Match english key or telugu name parts
        if key in combined or any(w.lower() in combined for w in info["name"].split()):
            if key not in seen:
                seen.add(key)
                detected.append({
                    "id": key.replace(" ", "_"),
                    "search_term": info["search_term"],
                    "name": info["name"],
                    "role": info["role"],
                    "attributes": info["attributes"],
                    "default_colors": info["default_colors"]
                })

    # If no specific figures matched, detect generic archetypes
    if not detected:
        generic_roles = [
            ("scientist", "Scientist / Researcher", ["lab coat", "safety goggles", "pipette", "data clipboard"]),
            ("doctor", "Surgeon / Physician", ["scrubs", "stethoscope", "sterile gloves", "surgical mask"]),
            ("astronaut", "Astronaut / Explorer", ["pressurized spacesuit", "reflective visor", "mission patch"]),
            ("human", "Human Observer", ["casual modern attire", "expressive facial reactions"]),
            ("warrior", "Ancient Warrior", ["forged plate armor", "crested helm", "battle spear", "shield"]),
            ("monarch", "Emperor / Ruler", ["royal diadem", "embroidered mantle", "scepter of state"])
        ]
        for role_id, role_name, attrs in generic_roles:
            if role_id in combined:
                detected.append({
                    "id": role_id,
                    "search_term": role_name,
                    "name": role_name,
                    "role": f"Primary visual subject for {role_name}",
                    "attributes": attrs,
                    "default_colors": {"skin": "#D4A373", "armor": "#3498DB", "attire": "#2C3E50", "aura": "#F39C12"}
                })
                break

    if not detected:
        # Fallback protagonist
        detected.append({
            "id": "protagonist",
            "search_term": "Human portrait historical",
            "name": "Protagonist",
            "role": "Narrator and visual focus",
            "attributes": ["expressive gesture", "key prop focus"],
            "default_colors": {"skin": "#D4A373", "armor": "#E67E22", "attire": "#1A5276", "aura": "#F4D03F"}
        })

    return detected


def fetch_online_reference(search_term):
    """Searches Wikipedia Page Summary API and Wikimedia Commons for authentic reference image."""
    # 1. Try Wikipedia Summary API
    try:
        wiki_title = urllib.parse.quote(search_term.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            img_url = data.get("originalimage", {}).get("source") or data.get("thumbnail", {}).get("source")
            if img_url:
                log(f"Found Wikipedia reference for '{search_term}': {img_url[:75]}...")
                return img_url, data.get("description", "")
    except Exception:
        pass

    # 2. Try Wikimedia Commons search
    try:
        clean_q = urllib.parse.quote(f"{search_term} painting artwork portrait")
        url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch={clean_q}&gsrnamespace=6&gsrlimit=5&prop=imageinfo&iiprop=url|mime|size"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            pages = data.get("query", {}).get("pages", {})
            for p in pages.values():
                info = p.get("imageinfo", [{}])[0]
                mime = info.get("mime", "")
                if "image/" in mime and "svg" not in mime:
                    furl = info.get("url")
                    if furl:
                        log(f"Found Wikimedia Commons reference for '{search_term}': {furl[:75]}...")
                        return furl, p.get("title", "")
    except Exception:
        pass

    return None, ""


def download_image(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read()


def extract_palette(image):
    """Extract dominant skin, attire, and metallic/accent colors from image."""
    thumb = image.resize((64, 64))
    pixels = list(thumb.getdata())
    # Exclude very dark and near-white
    valid = [p[:3] for p in pixels if 30 < (p[0] + p[1] + p[2]) / 3 < 235]
    if not valid:
        return {"skin": "#D4A373", "attire": "#B83B5E", "accent": "#FFD700"}

    # Sort by brightness
    valid.sort(key=lambda c: (c[0] * 0.299 + c[1] * 0.587 + c[2] * 0.114))
    dark = valid[len(valid) // 6]
    mid = valid[len(valid) // 2]
    bright = valid[-len(valid) // 6]

    to_hex = lambda c: f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}".upper()
    return {
        "attire": to_hex(dark),
        "skin": to_hex(mid),
        "accent": to_hex(bright)
    }


def generate_character_sprite(image, out_path, border_color=(255, 215, 0)):
    """Creates a high-fidelity framed circular portrait sprite with alpha transparency."""
    size = (512, 512)
    cropped = ImageOps.fit(image, size, method=Image.Resampling.LANCZOS)

    # Create circular mask
    mask = Image.new("L", size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((10, 10, size[0] - 10, size[1] - 10), fill=255)

    # Output RGBA sprite
    sprite = Image.new("RGBA", size, (0, 0, 0, 0))
    sprite.paste(cropped, (0, 0), mask=mask)

    # Draw golden accent border ring
    draw_sprite = ImageDraw.Draw(sprite)
    draw_sprite.ellipse((10, 10, size[0] - 10, size[1] - 10), outline=border_color, width=8)
    draw_sprite.ellipse((16, 16, size[0] - 16, size[1] - 16), outline=(255, 255, 255, 180), width=3)

    sprite.save(out_path, format="PNG")


def generate_character_card(char_info, ref_image, out_path):
    """Creates a visual presentation card showing character details and color swatches."""
    card = Image.new("RGB", (640, 800), color="#0F172A")
    draw = ImageDraw.Draw(card)

    # Card header
    draw.rectangle([(0, 0), (640, 70)], fill="#1E293B")
    draw.text((24, 22), "CHARACTER DESIGN SHEET", fill="#94A3B8")

    # Character name & role
    name = char_info.get("name", "Character")
    draw.text((24, 85), name[:32], fill="#F8FAFC")
    role = char_info.get("role", "")
    draw.text((24, 115), role[:55], fill="#38BDF8")

    # Reference Image
    thumb_size = (592, 440)
    fit_img = ImageOps.fit(ref_image, thumb_size, method=Image.Resampling.LANCZOS)
    card.paste(fit_img, (24, 150))
    draw.rectangle([(24, 150), (616, 590)], outline="#334155", width=3)

    # Attributes box
    draw.rectangle([(24, 606), (616, 710)], fill="#1E293B", outline="#334155")
    draw.text((36, 616), "ICONOGRAPHY & CANONICAL ATTRIBUTES:", fill="#94A3B8")
    attrs = char_info.get("attributes", [])
    for idx, attr in enumerate(attrs[:3]):
        draw.text((36, 642 + idx * 20), f"• {attr}", fill="#E2E8F0")

    # Color swatches
    draw.text((24, 726), "COLOR PALETTE:", fill="#94A3B8")
    colors = char_info.get("colors", {})
    swatch_x = 160
    for key, hex_code in colors.items():
        try:
            draw.rectangle([(swatch_x, 722), (swatch_x + 36, 756)], fill=hex_code, outline="#FFFFFF")
            draw.text((swatch_x + 42, 730), f"{key}: {hex_code}", fill="#CBD5E1")
            swatch_x += 150
        except Exception:
            pass

    card.save(out_path, format="JPEG", quality=90)


def generate_js_module(characters, js_path):
    """Generates Three.js / Canvas helper module for character assets with active-speaker animation."""
    js_content = f"""// Auto-generated Character Asset Module
// Cinema-Grade Three.js multi-character staging & dialogue visual cues.

import * as THREE from 'three';

export const CHARACTERS_DATA = {json.dumps(characters, indent=2, ensure_ascii=False)};

const textureLoader = new THREE.TextureLoader();
const spriteCache = new Map();

/**
 * Creates a Three.js textured billboard sprite mesh for a character.
 * @param {{string}} charId - ID of the character (e.g. 'karna', 'indra')
 * @param {{number}} scale - World scale in units (default: 2.2)
 * @returns {{THREE.Sprite}} Configured Three.js sprite
 */
export function createCharacterSprite(charId, scale = 2.2) {{
  const char = CHARACTERS_DATA.find(c => c.id === charId) || CHARACTERS_DATA[0];
  if (!char || !char.sprite) return new THREE.Group();

  let tex = spriteCache.get(char.sprite);
  if (!tex) {{
    tex = textureLoader.load(char.sprite);
    tex.colorSpace = THREE.SRGBColorSpace;
    spriteCache.set(char.sprite, tex);
  }}

  const material = new THREE.SpriteMaterial({{ map: tex, transparent: true }});
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(scale, scale, 1);
  return sprite;
}}

/**
 * Creates an animated 3D Character Actor with dynamic active-speaker visual cues.
 * Features:
 *  - Speech vibration / breathing rhythm when actively speaking
 *  - Subtle listening idle & micro-gestures when passive
 *  - Dynamic aura ring highlight pulsing on the speaking actor
 * @param {{string}} charId - Character ID
 * @param {{number}} scale - Base scale in world units
 */
export function createCharacterActor(charId, scale = 2.2) {{
  const group = new THREE.Group();
  group.name = `actor_${{charId}}`;
  group.userData = {{
    charId,
    baseScale: scale,
    isSpeaking: false,
    speakIntensity: 0
  }};

  const sprite = createCharacterSprite(charId, scale);
  group.add(sprite);

  // Subtle circular aura halo behind character
  const auraGeo = new THREE.RingGeometry(0.7 * scale, 0.88 * scale, 32);
  const char = CHARACTERS_DATA.find(c => c.id === charId) || {{}};
  const auraColor = char.colors?.aura || '#FFD700';
  const auraMat = new THREE.MeshBasicMaterial({{
    color: new THREE.Color(auraColor),
    transparent: true,
    opacity: 0.15,
    side: THREE.DoubleSide
  }});
  const auraMesh = new THREE.Mesh(auraGeo, auraMat);
  auraMesh.position.z = -0.05;
  group.add(auraMesh);

  /**
   * Updates actor animations according to current playback time and active speaker.
   * @param {{number}} t - Time in seconds
   * @param {{string|null}} activeSpeakerId - ID of currently speaking character
   */
  group.update = function(t, activeSpeakerId) {{
    const speaking = activeSpeakerId === charId;
    const targetIntensity = speaking ? 1.0 : 0.0;
    this.userData.speakIntensity += (targetIntensity - this.userData.speakIntensity) * 0.18;
    const si = this.userData.speakIntensity;

    // Vocal bounce & breathing
    const speechBounce = Math.sin(t * 13.5) * 0.04 * si;
    const idleBreath = Math.sin(t * 2.2) * 0.012 * (1.0 - si * 0.7);
    const curScale = this.userData.baseScale * (1.0 + speechBounce + idleBreath);
    sprite.scale.set(curScale, curScale, 1);

    // Subtle head/body tilt while delivering dialogue
    const tilt = Math.sin(t * 6.5) * 0.025 * si;
    sprite.material.rotation = tilt;

    // Aura illumination pulse
    const auraPulse = (0.2 + 0.45 * si) + Math.sin(t * 8.0) * 0.15 * si;
    auraMat.opacity = Math.max(0.05, Math.min(0.85, auraPulse));
    const auraScale = 1.0 + 0.08 * Math.sin(t * 4.0) * si;
    auraMesh.scale.set(auraScale, auraScale, 1);
  }};

  return group;
}}

/**
 * Finds the active speaker at time `t` from a `words` array.
 * @param {{Array}} words - List of word timing objects with `start`, `end`, and `speaker`
 * @param {{number}} t - Current playback time in seconds
 * @returns {{string|null}} Speaker ID or null
 */
export function getActiveSpeakerAtTime(words, t) {{
  if (!words || !words.length) return null;
  // Look for word overlapping t
  for (let i = 0; i < words.length; i++) {{
    const w = words[i];
    if (t >= w.start - 0.05 && t <= w.end + 0.08) {{
      return w.speaker || null;
    }}
  }}
  return null;
}}

/**
 * Draws character portrait on a 2D canvas context.
 */
export function drawCharacter2D(ctx, charId, x, y, radius = 80) {{
  const char = CHARACTERS_DATA.find(c => c.id === charId);
  if (!char) return;

  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, Math.PI * 2);
  ctx.fillStyle = char.colors?.skin || '#D4A373';
  ctx.fill();
  ctx.lineWidth = 4;
  ctx.strokeStyle = char.colors?.armor || '#FFD700';
  ctx.stroke();
  ctx.restore();
}}
"""
    js_path.write_text(js_content, encoding="utf-8")
    log(f"Generated Three.js character loader module: {js_path.name}")


def main():
    proj_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    script_path = proj_dir / "script.json"
    if not script_path.exists():
        log(f"No script.json found in {proj_dir}")
        sys.exit(1)

    script = json.loads(script_path.read_text(encoding="utf-8"))
    characters_raw = extract_characters_from_script(script)

    assets_dir = proj_dir / "assets" / "characters"
    assets_dir.mkdir(parents=True, exist_ok=True)
    data_dir = proj_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    log(f"Setting up {len(characters_raw)} character(s) from authentic online references...")

    processed = []
    for char in characters_raw:
        c_id = char["id"]
        search_q = char.get("search_term", char["name"])
        log(f"Searching online reference imagery for '{char['name']}' ({search_q})...")

        img_url, source_desc = fetch_online_reference(search_q)
        ref_path = assets_dir / f"ref_{c_id}.jpg"
        sprite_path = assets_dir / f"{c_id}.png"
        card_path = assets_dir / f"card_{c_id}.jpg"

        palette = char.get("default_colors", {"skin": "#D4A373", "armor": "#FFD700", "attire": "#B83B5E"})

        if img_url:
            try:
                raw_bytes = download_image(img_url)
                ref_path.write_bytes(raw_bytes)
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
                extracted = extract_palette(img)
                palette.update(extracted)

                # Generate sprite
                generate_character_sprite(img, sprite_path)
                # Generate visual presentation card
                char["colors"] = palette
                generate_character_card(char, img, card_path)

                log(f"  ✓ Reference downloaded ({img.size[0]}x{img.size[1]})")
                log(f"  ✓ Character sprite generated: {sprite_path.name}")
                log(f"  ✓ Color palette extracted: {palette}")
            except Exception as e:
                log(f"  ⚠ Failed processing image for {c_id}: {e}")
        else:
            log(f"  ⚠ No online image found for {c_id}, creating stylized procedural asset...")
            # Create a stylized fallback canvas image
            canvas = Image.new("RGB", (512, 512), color=palette.get("attire", "#2C3E50"))
            draw = ImageDraw.Draw(canvas)
            draw.ellipse((60, 60, 452, 452), fill=palette.get("skin", "#D4A373"), outline=palette.get("armor", "#FFD700"), width=12)
            draw.text((120, 240), char["name"][:16], fill="#FFFFFF")
            canvas.save(ref_path, format="JPEG")
            generate_character_sprite(canvas, sprite_path)

        char_record = {
            "id": c_id,
            "name": char["name"],
            "role": char.get("role", ""),
            "attributes": char.get("attributes", []),
            "colors": palette,
            "reference_url": img_url or "procedural",
            "reference_file": str(ref_path.relative_to(proj_dir)),
            "sprite": str(sprite_path.relative_to(proj_dir)),
            "card": str(card_path.relative_to(proj_dir)) if card_path.exists() else None
        }
        processed.append(char_record)

    # Save to data/characters.json
    characters_json_path = data_dir / "characters.json"
    characters_json_path.write_text(json.dumps({
        "project": proj_dir.name,
        "title": script.get("title", ""),
        "characters": processed
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Wrote metadata to {characters_json_path.relative_to(proj_dir)}")

    # Check if project uses Tall Tale 3D (toon.js exists)
    core_dir = proj_dir / "src" / "core"
    toon_js = core_dir / "toon.js"
    if toon_js.exists():
        log("Detected Tall Tale 3D engine: generating Character Design Module and Audit Sheet...")
        tt_chars = {}
        for c in characters_raw:
            c_id = c["id"]
            look = c.get("look")
            if not look:
                pal = c.get("default_colors", {})
                head_col = pal.get("skin", "#D4A373")
                body_col = pal.get("attire", "#E8734A")
                role_str = (c["name"] + " " + c.get("role", "")).lower()
                d_opts = {}
                extra = []
                if any(w in role_str for w in ["king", "monarch", "emperor", "రాజు"]):
                    d_opts["crown"] = "mukut"
                    d_opts["jewellery"] = True
                    extra.append("mustache")
                elif any(w in role_str for w in ["spirit", "ghost", "betal", "బేతాళుడు"]):
                    d_opts["fangs"] = True
                    head_col = "#D8DEE4"
                    body_col = "#2C2A38"
                elif any(w in role_str for w in ["brahmin", "scholar", "pandit", "పండితుడు"]):
                    d_opts["tilak"] = "#D8343F"
                elif any(w in role_str for w in ["god", "deva", "krishna", "shiva", "hanuman"]):
                    d_opts["jewellery"] = True

                look = {
                    "head": head_col,
                    "body": body_col,
                    "pattern": "plain",
                    "deity": "custom",
                    "deityOpts": d_opts,
                    "extra": extra
                }

            tt_chars[c_id] = {
                "id": c_id,
                "name": c["name"],
                "englishName": c.get("englishName", c.get("search_term", c["name"])),
                "role": c.get("role", ""),
                "look": look,
                "height": c.get("height", 1.75)
            }

        js_content = "// Tall Tale 3D Character Roster\nimport { Toon, PROPS } from './toon.js';\nimport { deityLook } from './deity.js';\n\nexport const CHARACTER_DESIGNS = " + json.dumps(tt_chars, indent=2, ensure_ascii=False) + ";\n\nexport function makeCharacter(id, overrides = {}) {\n  const conf = CHARACTER_DESIGNS[id];\n  if (!conf) throw new Error('Unknown character id: ' + id);\n  const look = { ...conf.look, ...(overrides.look || {}) };\n  const height = overrides.height || conf.height || 1.75;\n  const toon = new Toon(look, { height });\n  if (conf.holdR && !overrides.holdR) toon.set({ holdR: conf.holdR });\n  return toon;\n}\n"
        (core_dir / "characters.js").write_text(js_content, encoding="utf-8")
        log("  ✓ Wrote src/core/characters.js")

        # Create character-audit.html
        audit_html = proj_dir / "character-audit.html"
        cards_json = json.dumps(list(tt_chars.values()), ensure_ascii=False)
        html_code = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Character Design Sheet</title>
<style>
@font-face {{ font-family: 'Inter'; font-weight: 900; src: url('fonts/Inter-Black.otf'); }}
@font-face {{ font-family: 'Inter'; font-weight: 700; src: url('fonts/Inter-Bold.otf'); }}
body {{ margin: 0; background: #18171F; color: #FFF6E6; font-family: 'Inter', sans-serif; }}
canvas {{ display: block; }}
</style></head><body><canvas id="cv" width="1920" height="1080"></canvas>
<script type="importmap">{{"imports":{{"three":"./vendor/three.module.js","three/addons/":"./vendor/addons/"}}}}</script>
<script type="module">
import {{ drawToon, PROPS }} from './src/core/toon.js';
const chars = {cards_json};
const cv = document.getElementById('cv'), g = cv.getContext('2d');
g.fillStyle = '#18171F'; g.fillRect(0, 0, cv.width, cv.height);
const bgGrad = g.createRadialGradient(960, 400, 100, 960, 540, 900);
bgGrad.addColorStop(0, '#262333'); bgGrad.addColorStop(1, '#14131A');
g.fillStyle = bgGrad; g.fillRect(0, 0, cv.width, cv.height);
g.fillStyle = '#F2C230'; g.font = '900 36px Inter'; g.textAlign = 'left';
g.fillText('CHARACTER DESIGN SHEET (TALL TALE 3D)', 60, 70);
g.fillStyle = '#A9A6B8'; g.font = '700 18px Inter';
g.fillText('PROJECT: {script.get("title", proj_dir.name)}', 60, 105);
g.strokeStyle = '#38344A'; g.lineWidth = 2; g.beginPath(); g.moveTo(60, 130); g.lineTo(1860, 130); g.stroke();
const count = chars.length, cardW = (1860 - 60 - (count - 1) * 24) / count, startX = 60, cardY = 160, cardH = 860;
chars.forEach((c, i) => {{
  const cx = startX + i * (cardW + 24);
  g.save(); g.beginPath(); g.roundRect(cx, cardY, cardW, cardH, 16);
  g.fillStyle = '#201D2B'; g.fill(); g.strokeStyle = '#3D3852'; g.lineWidth = 3; g.stroke(); g.clip();
  const cg = g.createLinearGradient(0, cardY, 0, cardY + 500);
  cg.addColorStop(0, '#2D283E'); cg.addColorStop(1, '#201D2B');
  g.fillStyle = cg; g.fillRect(cx, cardY, cardW, cardH);
  g.fillStyle = 'rgba(0,0,0,0.45)'; g.beginPath(); g.ellipse(cx + cardW/2, cardY + 550, cardW * 0.36, 18, 0, 0, Math.PI * 2); g.fill();
  g.save(); const scale = 0.46; g.translate(cx + cardW/2 - 256 * scale, cardY + 90); g.scale(scale, scale);
  drawToon(g, c.look, {{ mood: i % 2 ? 'smug' : 'proud', armL: [14, 8], armR: [14, 8], legs: 'stand' }});
  g.restore();
  g.fillStyle = '#FFF6E6'; g.font = '900 24px Inter'; g.textAlign = 'center';
  g.fillText(c.name, cx + cardW/2, cardY + 600);
  g.fillStyle = '#F2C230'; g.font = '800 15px Inter';
  g.fillText((c.englishName || c.id).toUpperCase(), cx + cardW/2, cardY + 630);
  g.fillStyle = '#A9A6B8'; g.font = '700 13px Inter';
  const words = (c.role || '').split(' ');
  let line = '', curY = cardY + 665;
  for (let n = 0; n < words.length; n++) {{
    const tl = line + words[n] + ' ';
    if (g.measureText(tl).width > cardW - 32 && n > 0) {{ g.fillText(line, cx + cardW/2, curY); line = words[n] + ' '; curY += 20; }}
    else {{ line = tl; }}
  }}
  g.fillText(line, cx + cardW/2, curY);
  g.restore();
}});
window.__ready = true;
</script></body></html>"""
        audit_html.write_text(html_code, encoding="utf-8")
        log("  ✓ Wrote character-audit.html")

        # Snapshot character design sheet
        review_dir = proj_dir / "review"
        review_dir.mkdir(parents=True, exist_ok=True)
        out_sheet = review_dir / "characters.png"
        try:
            import subprocess
            import shutil
            chrome_bin = os.environ.get('CHROME') or shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser') or '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
            snap_script = f"""
import fs from 'node:fs'; import {{ spawn }} from 'node:child_process'; import http from 'node:http';
const srv = http.createServer((req, res) => {{
  const f = '{proj_dir}' + req.url.split('?')[0];
  if (fs.existsSync(f)) {{
    const ext = f.split('.').pop();
    const mime = {{ html: 'text/html', js: 'text/javascript', otf: 'font/otf', ttf: 'font/ttf', png: 'image/png' }}[ext] || 'application/octet-stream';
    res.writeHead(200, {{ 'Content-Type': mime }});
    fs.createReadStream(f).pipe(res);
  }} else {{ res.writeHead(404); res.end(); }}
}}).listen(0, '127.0.0.1', async () => {{
  const port = srv.address().port;
  const chrome = spawn({json.dumps(chrome_bin)}, [
    '--headless=new', '--screenshot={out_sheet}', '--window-size=1920,1080',
    `http://127.0.0.1:${{port}}/character-audit.html`
  ]);
  chrome.on('close', () => srv.close());
}});
"""
            subprocess.run(["node", "-e", snap_script], timeout=15, check=True)
            log(f"  ✓ Character Design Sheet rendered: {out_sheet.name}")
        except Exception as err:
            log(f"  ⚠ Character Design Sheet snapshot warning: {err}")

    elif core_dir.exists():
        generate_js_module(processed, core_dir / "characters.js")

    log("Character design and reference asset setup COMPLETE.")


if __name__ == "__main__":
    main()
