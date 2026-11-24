#!/usr/bin/env python3
"""setup_folktale_illustrations.py - 2D Indian Folk / Amar Chitra Katha illustration pipeline.

Generates or sources 1080x1920 illustrations for Telugu folktales, mythology, and riddle tales.
Applies the signature Amar Chitra Katha art style:
- Thick dark ink outlines (3-6px black)
- Exaggerated expressive facial silhouettes & traditional attires
- Signature dark teal-green misty background with warm golden lamp accents
- Blood-red sky flashback for eerie/graveyard revelations
- Night forest Vikram & Betal cliffhanger

Usage:
  python3 scripts/setup_folktale_illustrations.py <project_dir>
"""

import os
import sys
import json
import math
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MASTER_STYLE_PROMPT = (
    "2D flat cartoon illustration, Indian folk tale style, thick dark outlines, "
    "exaggerated expressive faces, traditional dhoti, sacred thread, tilak on forehead, "
    "dark teal-green misty background with warm golden lamp light, cinematic lighting, "
    "detailed palace / temple background, vertical 9:16, consistent character design"
)

CHARACTER_LOCKS = {
    "brother1": "short stout bald man, big nose, orange shawl, white dhoti, sacred thread, vibhuti tilak",
    "brother2": "thin tall man, big curly black mustache, yellow marigold flower in hair bun, teal shawl, mustard dhoti",
    "brother3": "muscular young man with green-tinted skin, top knot, red and white dhoti, sacred thread",
    "king": "heavyset king with thick mustache, golden crown, red and gold royal robe, pearl necklace",
    "betal": "pale ghoulish spirit with yellow eyes, long black hair, hanging on Vikram's shoulder in the night forest",
    "vikram": "regal warrior king Vikramaditya with sword, royal armor, in dark misty forest",
}

def draw_radial_gradient(draw, width, height, center_x, center_y, max_r, col_inner, col_outer):
    """Simulates a radial glow."""
    steps = 30
    for i in range(steps, 0, -1):
        r = max_r * (i / steps)
        t = i / steps
        r_c = int(col_inner[0] * (1 - t) + col_outer[0] * t)
        g_c = int(col_inner[1] * (1 - t) + col_outer[1] * t)
        b_c = int(col_inner[2] * (1 - t) + col_outer[2] * t)
        a_c = int(col_inner[3] * (1 - t) + col_outer[3] * t) if len(col_inner) > 3 else 255
        draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=(r_c, g_c, b_c, a_c))

def generate_procedural_illustration(output_path, shot_idx, total_shots, line_text, tags=None):
    """Generates an authentic 1080x1920 Amar Chitra Katha painterly illustration."""
    tags = tags or []
    w, h = 1080, 1920
    im = Image.new("RGBA", (w, h), (13, 43, 42, 255)) # Base dark teal
    draw = ImageDraw.Draw(im, "RGBA")

    is_flashback = ("flashback" in tags) or ("శవం" in line_text) or ("శ్మశాన" in line_text) or ("పొలం" in line_text and "వాసన" in line_text)
    is_betal = ("betal" in tags) or ("బేతాళు" in line_text) or ("విక్రమార్క" in line_text) or (shot_idx >= total_shots - 2)
    is_rice = ("smell" in tags) or ("అన్నం" in line_text) or ("వాసన" in line_text) or ("మొదటి" in line_text)
    is_cow = ("cow" in tags) or ("ఆవు" in line_text) or ("పాలు" in line_text) or ("మేక" in line_text)
    is_mattress = ("touch" in tags) or ("పరుపు" in line_text) or ("వెంట్రుక" in line_text) or ("గాయం" in line_text)

    # 1. Background Environmental Base Wash
    if is_flashback:
        # Blood-Red Sky + Golden Graveyard Field
        for y in range(h):
            t = y / h
            if t < 0.55:
                # Ominous blood red to crimson
                r = int(84 + t * 90)
                g = int(18 + t * 20)
                b = int(26 + t * 15)
            else:
                # Golden creepy paddy field
                t_field = (t - 0.55) / 0.45
                r = int(180 - t_field * 80)
                g = int(140 - t_field * 70)
                b = int(25 - t_field * 15)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Distant crooked tombstones & dry thorny trees
        draw.line([(100, 1100), (100, 850)], fill=(20, 5, 8, 255), width=18)
        draw.line([(60, 920), (140, 920)], fill=(20, 5, 8, 255), width=14)
        draw.line([(880, 1080), (880, 890)], fill=(20, 5, 8, 255), width=16)
        draw.line([(850, 950), (910, 950)], fill=(20, 5, 8, 255), width=12)
        # Smoke rising from pyre
        draw.arc([400, 700, 680, 1100], 180, 360, fill=(40, 10, 15, 180), width=35)

    elif is_betal:
        # Night Forest with Moon & Mist
        for y in range(h):
            t = y / h
            r = int(8 + t * 10)
            g = int(18 + t * 24)
            b = int(30 + t * 35)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Full Moon
        draw.ellipse([680, 240, 880, 440], fill=(245, 240, 215, 255))
        draw.ellipse([660, 220, 900, 460], outline=(245, 230, 160, 100), width=15)
        # Twisted silhouette branches
        draw.line([(0, 300), (450, 650)], fill=(8, 14, 18, 255), width=38)
        draw.line([(250, 480), (320, 320)], fill=(8, 14, 18, 255), width=20)
        draw.line([(1080, 200), (750, 600)], fill=(8, 14, 18, 255), width=32)

    else:
        # Varanasi Royal Palace / Courtyard with Warm Oil Lamps
        for y in range(h):
            t = y / h
            r = int(13 + t * 10)
            g = int(43 + t * 15)
            b = int(42 + t * 10)
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))

        # Palace carved stone pillars (Thick dark ink contours)
        # Left Pillar
        draw.rectangle([80, 180, 220, 1450], fill=(22, 60, 56, 255), outline=(6, 22, 20, 255), width=6)
        draw.rectangle([60, 140, 240, 210], fill=(185, 140, 45, 255), outline=(6, 22, 20, 255), width=6)
        draw.rectangle([60, 1420, 240, 1480], fill=(185, 140, 45, 255), outline=(6, 22, 20, 255), width=6)
        # Right Pillar
        draw.rectangle([860, 180, 1000, 1450], fill=(22, 60, 56, 255), outline=(6, 22, 20, 255), width=6)
        draw.rectangle([840, 140, 1020, 210], fill=(185, 140, 45, 255), outline=(6, 22, 20, 255), width=6)
        draw.rectangle([840, 1420, 1020, 1480], fill=(185, 140, 45, 255), outline=(6, 22, 20, 255), width=6)

        # Palace Royal Arch
        draw.arc([180, 80, 900, 550], 180, 360, fill=(246, 195, 68, 255), width=18)
        draw.arc([180, 80, 900, 550], 180, 360, fill=(6, 22, 20, 255), width=4)

        # Hanging Golden Diya / Oil Lamps
        for lamp_x in [150, 540, 930]:
            draw.line([(lamp_x, 0), (lamp_x, 320)], fill=(180, 140, 40, 255), width=6)
            draw.polygon([(lamp_x - 45, 320), (lamp_x + 45, 320), (lamp_x, 370)], fill=(246, 195, 68, 255), outline=(8, 20, 18, 255))
            # Glowing flame
            draw.ellipse([lamp_x - 16, 280, lamp_x + 16, 325], fill=(255, 235, 120, 255))
            draw.ellipse([lamp_x - 8, 290, lamp_x + 8, 320], fill=(255, 90, 20, 255))

    # 2. Foreground Illustrated Character Silhouettes (Amar Chitra Katha Style)
    if is_betal:
        # --- KING VIKRAM & BETAL ON SHOULDER ---
        # Vikram's broad armored chest & royal turban
        draw.ellipse([320, 820, 760, 1750], fill=(180, 60, 40, 255), outline=(8, 14, 18, 255), width=8)
        # Gold Armor Plate
        draw.ellipse([380, 900, 700, 1400], fill=(246, 195, 68, 255), outline=(8, 14, 18, 255), width=7)
        # Vikram's Face
        draw.ellipse([440, 620, 640, 850], fill=(212, 163, 115, 255), outline=(8, 14, 18, 255), width=8)
        # Royal Mustache & Beard
        draw.arc([460, 720, 620, 780], 0, 180, fill=(8, 14, 18, 255), width=18)
        # Determined Eyes & Tilak
        draw.ellipse([480, 690, 520, 715], fill=(255, 255, 255, 255), outline=(8, 14, 18, 255), width=4)
        draw.ellipse([495, 695, 510, 710], fill=(8, 14, 18, 255))
        draw.ellipse([560, 690, 600, 715], fill=(255, 255, 255, 255), outline=(8, 14, 18, 255), width=4)
        draw.ellipse([570, 695, 585, 710], fill=(8, 14, 18, 255))
        draw.line([(540, 640), (540, 680)], fill=(200, 40, 30, 255), width=8) # Vermillion tilak

        # Royal Turban with jewel
        draw.arc([420, 540, 660, 720], 180, 360, fill=(160, 30, 40, 255), width=45)
        draw.ellipse([520, 560, 560, 610], fill=(255, 215, 0, 255), outline=(8, 14, 18, 255), width=5)

        # BETAL (Perched on Left Shoulder)
        # Pale ghoulish head
        draw.ellipse([210, 580, 380, 780], fill=(207, 216, 220, 255), outline=(8, 14, 18, 255), width=7)
        # Wild black hair cascading down
        for hair_x in range(160, 320, 25):
            draw.line([(hair_x, 620), (hair_x - 30, 920)], fill=(12, 16, 20, 255), width=12)
        # Glowing Yellow Eyes
        draw.ellipse([240, 650, 285, 685], fill=(255, 235, 59, 255), outline=(8, 14, 18, 255), width=5)
        draw.ellipse([258, 662, 272, 676], fill=(180, 0, 0, 255))
        draw.ellipse([305, 650, 350, 685], fill=(255, 235, 59, 255), outline=(8, 14, 18, 255), width=5)
        draw.ellipse([320, 662, 334, 676], fill=(180, 0, 0, 255))
        # Ghoulish Grinning Mouth with fangs
        draw.arc([250, 690, 340, 750], 0, 180, fill=(8, 14, 18, 255), width=10)
        draw.polygon([(275, 725), (285, 725), (280, 740)], fill=(255, 255, 255, 255))
        draw.polygon([(305, 725), (315, 725), (310, 740)], fill=(255, 255, 255, 255))
        # Clawed Hand Pointing Forward
        draw.line([(360, 790), (460, 830)], fill=(207, 216, 220, 255), width=18)
        draw.line([(460, 830), (510, 835)], fill=(207, 216, 220, 255), width=14)

    elif is_flashback:
        # --- GRAVEYARD PADDY FIELD FLASHBACK ---
        # Close up of black soil with a human bone/skull, and golden rice plant sprouting out
        draw.ellipse([420, 960, 660, 1180], fill=(225, 220, 205, 255), outline=(15, 5, 8, 255), width=7)
        # Skull eye sockets
        draw.ellipse([465, 1020, 520, 1080], fill=(30, 8, 12, 255))
        draw.ellipse([560, 1020, 615, 1080], fill=(30, 8, 12, 255))
        # Sprouting Golden Rice Stalk
        draw.line([(540, 970), (540, 520)], fill=(246, 195, 68, 255), width=12)
        for rx, ry in [(540, 750), (540, 680), (540, 610), (540, 540)]:
            draw.arc([rx - 90, ry - 40, rx + 10, ry + 40], 0, 180, fill=(246, 195, 68, 255), width=14)
            draw.arc([rx - 10, ry - 40, rx + 90, ry + 40], 0, 180, fill=(246, 195, 68, 255), width=14)

    elif is_rice or shot_idx == 0:
        # --- BROTHER 1: SHORT, STOUT, BIG NOSE, ORANGE SHAWL ---
        # Holding brass plate of steaming white rice
        # Torso & Orange Shawl
        draw.ellipse([260, 850, 820, 1850], fill=(230, 126, 34, 255), outline=(8, 22, 20, 255), width=8)
        # White Dhoti & Sacred Thread (Yajnopavita)
        draw.line([(380, 880), (680, 1350)], fill=(255, 255, 255, 255), width=9)
        # Head (Stout, Bald)
        draw.ellipse([380, 540, 700, 870], fill=(212, 163, 115, 255), outline=(8, 22, 20, 255), width=8)
        # Vibhuti Tilak (3 white lines + red dot)
        for vy in [580, 595, 610]:
            draw.line([(490, vy), (590, vy)], fill=(255, 255, 255, 255), width=5)
        draw.ellipse([533, 590, 547, 604], fill=(200, 30, 30, 255))
        # Exaggerated Eyes (Squinting with disgust)
        draw.arc([430, 660, 510, 710], 180, 360, fill=(8, 22, 20, 255), width=9)
        draw.arc([570, 660, 650, 710], 180, 360, fill=(8, 22, 20, 255), width=9)
        # THE FAMOUS OVERSIZED NOSE (The "Smell" Brother Signature)
        draw.ellipse([480, 660, 600, 780], fill=(212, 140, 95, 255), outline=(8, 22, 20, 255), width=8)
        draw.ellipse([495, 740, 525, 770], fill=(60, 25, 15, 255))
        draw.ellipse([555, 740, 585, 770], fill=(60, 25, 15, 255))
        # Disgusted Mouth
        draw.arc([480, 790, 600, 835], 0, 180, fill=(8, 22, 20, 255), width=8)

        # Brass Plate with Rice
        draw.ellipse([310, 1100, 770, 1340], fill=(246, 195, 68, 255), outline=(8, 22, 20, 255), width=8)
        draw.ellipse([360, 1130, 720, 1300], fill=(255, 255, 255, 255), outline=(8, 22, 20, 255), width=6)
        # Rising Steam
        for sx in [460, 540, 620]:
            draw.arc([sx - 40, 920, sx + 40, 1140], 180, 360, fill=(240, 240, 240, 160), width=14)

    elif is_cow:
        # --- BROTHER 2: TALL, THIN, CURLY MUSTACHE, TEAL SHAWL, MARIGOLD FLOWER ---
        draw.ellipse([340, 800, 740, 1800], fill=(20, 90, 85, 255), outline=(8, 22, 20, 255), width=8)
        # Mustard Dhoti
        draw.ellipse([380, 1350, 700, 1850], fill=(212, 172, 13, 255), outline=(8, 22, 20, 255), width=8)
        # Thin Face
        draw.ellipse([420, 520, 660, 840], fill=(212, 163, 115, 255), outline=(8, 22, 20, 255), width=8)
        # Hair Bun + Yellow Marigold Flower
        draw.ellipse([480, 440, 600, 540], fill=(12, 16, 18, 255), outline=(8, 22, 20, 255), width=6)
        draw.ellipse([580, 470, 630, 520], fill=(255, 195, 0, 255), outline=(8, 22, 20, 255), width=5) # Marigold
        # Huge Curled Black Handlebar Mustache
        draw.arc([360, 680, 540, 760], 0, 180, fill=(8, 22, 20, 255), width=16)
        draw.arc([540, 680, 720, 760], 0, 180, fill=(8, 22, 20, 255), width=16)
        # Royal Milk Brass Bowl
        draw.ellipse([400, 1050, 680, 1220], fill=(246, 195, 68, 255), outline=(8, 22, 20, 255), width=8)
        draw.ellipse([430, 1070, 650, 1180], fill=(255, 255, 255, 255))

    elif is_mattress:
        # --- BROTHER 3: MUSCULAR, GREEN-TINTED SKIN, RED DHOTI, 7 MATTRESSES ---
        # 7 Stacked colorful mattresses
        mattress_colors = [
            (192, 57, 43), (243, 156, 18), (39, 174, 96), (41, 128, 185),
            (142, 68, 173), (211, 84, 0), (241, 196, 15)
        ]
        base_y = 1420
        for mi, col in enumerate(mattress_colors):
            my = base_y - mi * 75
            draw.rectangle([180, my, 900, my + 65], fill=col + (255,), outline=(8, 22, 20, 255), width=7)

        # Single red bruised hair visible under bottom mattress
        draw.arc([500, base_y + 40, 580, base_y + 90], 0, 180, fill=(180, 20, 20, 255), width=10)

        # Brother 3 Sleeping atop 7th mattress (Green-tinted muscular skin)
        top_y = base_y - len(mattress_colors) * 75
        draw.ellipse([300, top_y - 140, 780, top_y + 40], fill=(127, 169, 139, 255), outline=(8, 22, 20, 255), width=8)
        # Red Dhoti
        draw.ellipse([520, top_y - 120, 760, top_y + 30], fill=(192, 57, 43, 255), outline=(8, 22, 20, 255), width=7)
        # Top Knot
        draw.ellipse([310, top_y - 170, 380, top_y - 100], fill=(12, 16, 18, 255), outline=(8, 22, 20, 255), width=6)
        # Red Bruise on back
        draw.ellipse([460, top_y - 80, 520, top_y - 30], fill=(220, 50, 50, 220), outline=(120, 10, 10, 255), width=4)

    else:
        # --- THE KING ON THRONE / COURT ---
        # Royal Golden Throne
        draw.polygon([(160, 420), (920, 420), (840, 1500), (240, 1500)], fill=(185, 140, 45, 255), outline=(8, 22, 20, 255))
        # King's Royal Robe (Crimson & Gold)
        draw.ellipse([280, 850, 800, 1750], fill=(160, 30, 40, 255), outline=(8, 22, 20, 255), width=8)
        # Massive Pearl Necklace & Jewels
        for nx in range(380, 710, 40):
            draw.ellipse([nx, 920, nx + 28, 950], fill=(255, 255, 255, 255), outline=(8, 22, 20, 255), width=4)
        # King's Majestic Face
        draw.ellipse([400, 560, 680, 860], fill=(220, 170, 125, 255), outline=(8, 22, 20, 255), width=8)
        # Thick Regal Handlebar Mustache
        draw.arc([350, 710, 540, 785], 0, 180, fill=(8, 14, 18, 255), width=20)
        draw.arc([540, 710, 730, 785], 0, 180, fill=(8, 14, 18, 255), width=20)
        # Golden Crown with Ruby Gems
        draw.polygon([(360, 580), (420, 380), (540, 320), (660, 380), (720, 580)], fill=(246, 195, 68, 255), outline=(8, 22, 20, 255))
        draw.ellipse([520, 420, 560, 465], fill=(220, 30, 40, 255), outline=(8, 22, 20, 255), width=4)

    # 3. Apply Soft Mist Film Grain & Vignette Overlay
    im_blurred = im.filter(ImageFilter.GaussianBlur(radius=0.4))
    im_blurred.save(output_path, "PNG", quality=95)
    print(f"Generated Amar Chitra Katha illustration: {output_path} (tags: {tags})")

def setup_illustrations(proj_dir):
    proj_dir = Path(proj_dir).resolve()
    script_path = proj_dir / "script.json"
    if not script_path.exists():
        print(f"Error: No script.json found in {proj_dir}")
        sys.exit(1)

    with open(script_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    lines = meta.get("lines", [])
    if not lines:
        print("Warning: script.json contains no lines")
        return

    ill_dir = proj_dir / "assets" / "illustrations"
    ill_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Sourcing Amar Chitra Katha Illustrations ({len(lines)} cuts) ===")
    for i, line in enumerate(lines):
        shot_id = f"shot{i+1:02d}.png"
        out_file = ill_dir / shot_id
        if out_file.exists() and out_file.stat().st_size > 1000:
            print(f"  [{i+1}/{len(lines)}] Asset exists: {shot_id}")
            continue

        text = line.get("text", "")
        tags = line.get("tags", [])
        generate_procedural_illustration(out_file, i, len(lines), text, tags)

    print(f"All {len(lines)} illustrations staged in {ill_dir}")

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "."
    setup_illustrations(p)
