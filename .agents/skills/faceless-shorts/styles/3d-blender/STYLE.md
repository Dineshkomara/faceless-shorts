# 3D Blender Studio: Cinema-Grade 9:16 Shorts

Full 3D cinematic animation studio powered by Blender 5.2.0 LTS EEVEE Next and Apple Silicon Metal GPU acceleration.
Zero paid subscriptions, zero cloud rendering costs, 100% free and local.

## 1. Core Principles
- **100% Native 3D Assets**: Rigged 3D characters, monolithic stone pillars, reflective marble floors, dynamic torchlight, and atmospheric depth.
- **Cinematic Lighting**: 3-point lighting rig (Warm Amber Key Spot, Cool Sky Blue Fill Area, Intense Golden Rim Backlight) + flickering flame point lights.
- **Dynamic Camera Choreography**: 50mm portrait lens with physical Depth of Field (`f/2.4` aperture bokeh). Dynamic camera switching between CU (Close-Up), OTS (Over-The-Shoulder), M2S (Medium Two-Shot), and EWS (Establishing Wide Shot) with continuous subtle dolly push-ins.
- **Expressive Character Acting**:
  - Continuous sinusoidal breathing on Spine armature.
  - Natural eyelid blinks every 3-4 seconds.
  - Synchronized mouth speech articulation during dialogue lines.
  - Arm gestures (raising to chest, open palm reasoning, questioning, namaste).
  - Floating ghostly hover animation for supernatural entities (e.g. Betal).
- **Zack D. Films Science & Anatomy**: Procedural layered anatomical models with animated Boolean slicing planes that cut open to reveal inner biological structures.
- **Mobile-Optimized Typography**: HarfBuzz-shaped Telugu conjuncts and bold English subtitles with dark translucent background pill and active word highlights, placed safely above mobile UI buttons (`y = 1420`).

## 2. Environments (`environment.type`)
| Environment | Description | Lighting |
|---|---|---|
| `palace` | Grand royal court, fluted stone pillars with gold capitals, reflective marble floor, flaming brass diyas | Warm Amber Key, Cyan Fill, Intense Gold Rim |
| `charnel_ground` | Ancient knotted banyan tree with aerial roots, stone shrine, misty ground plane, brass lantern | Midnight Blue Key, Cyan Moonlit Rim, Warm Amber Lantern |
| `temple_sanctum` | Granite temple walls, sacred havan kund with glowing fire coals, brass bells | Warm Saffron Torch Key, Soft Fill, Golden Rim |
| `science_lab` | Clean dark reflective floor, circular pedestal with cyan neon glow, holographic rings | Crisp Daylight Key, Soft Fill, Cyan Rim |

## 3. Character Roles & Costumes
- **King / Monarch**: Ornate layered golden Mukut (crown) with ruby crest, golden necklace (haar) and armbands (bajuband), royal dhoti/angavastram, sacred tilak.
- **Pandit / Rishi / Scholar**: Traditional topknot hair (shikha bun), sacred Vibhuti / Tilak, rudraksha necklace, traditional dhoti.
- **Betal / Ghost**: Ethereal ash-blue skin, glowing mystical cyan eyes, floating vertical hover motion.
- **Scientist / Modern**: Stylized haircut, clean attire, medical coat / modern clothing.

## 4. Execution
```bash
# Render fast preview (first 10s / 300 frames)
python3 scripts/blender_engine.py <project_dir> --preview

# Render full master short
python3 scripts/blender_engine.py <project_dir> --full
```
Rendered output saved to `renders/<project_name>_3d.mp4` and review contact sheet to `review/3d_sheet.jpg`.
