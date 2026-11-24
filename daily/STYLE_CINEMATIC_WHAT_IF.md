# Cinematic What If — Locked Style Profile

This is an optional, English-only visual style for original science-grounded “What If” stories. Select it explicitly as `cinematic-what-if`; it never replaces, edits, or silently changes another style. English topic and fact-check rules still apply. Asakthi/Telugu remains in its chosen Telugu style, even when both channels run together. Use this file as a binding art-direction profile; use `REFERENCE_CINEMATIC_WHAT_IF.md` for story and production detail.

## 1. Visual identity

The identity is **simple dark-ink stick figures inside a sophisticated, low-key cinematic flat-vector world**. Use clean vector-like shapes, layered flat-shaded forms, and soft linear/radial gradients in environments only. Characters stay graphic and flat. No 3D-looking characters, photorealism, photography, clip art, emoji, anime, manga, watercolor, clay, pixel art, or comic outlines. Do not draw outlines around scenery or props. Do not apply gradients or realistic surface shading to characters. Every frame carries subtle fine film grain, a soft vignette, letterbox bars, and constant slow camera drift. Grain and vignette are nearly invisible at phone size; bars may smoothly adjust thickness between compositions.

Render at the selected aspect ratio. The reference master prompt's horizontal default is 2:1, with 2.39:1 scope for drama (title, freeze, climax, intense close-up). For Shorts, use the configured vertical output and protect its caption-safe area; do not crop a vertical master to fake a widescreen file. In either layout, keep subtle letterbox bars present and animate their height smoothly between compositions. Preserve the existing output resolution, captions, and delivery format configured by the pipeline.

The environment carries the sophistication: dark mid-tone value structure, deep purple/navy shadows, warm amber light, soft gradients, parallax planes, selective atmosphere, restrained grain, and a vignette. Keep roughly 60–75% of the composition in dark mid-tones and use only 1–3 bright accents. Choose one motivated key light per scene and show its source or a clear reason for its direction. Light spills onto floors and nearby edges; use restrained window glow, lamp cones, monitor light, sunset, moonlight, or occasional god rays. Avoid turning every frame into a glow or particle effect.

## 2. Locked character bible

### Lead male

- Pure dark-ink stick figure; head is a solid circle, `#0e0b12`.
- Only face details: warm-cream `#f4efe6` dot/circle eyes, simple mouth shapes, and occasional simple brow lines. No nose, ears, detailed eye anatomy, skin texture, or realistic proportions.
- One signature colored garment: deep-blue jacket `#1e56a0`. This is the only character color on him; head, torso base, arms, legs, and feet remain dark ink.
- Thick limbs are round-capped line segments, width 11–13 px at 1080p. The torso is a thick line with a simple jacket shape over it. Feet are short forward-pointing stubs. Hands terminate as rounded arm ends; no visible fingers at normal viewing scale.
- Always give the lit side a thin warm cream/amber rim edge `#ffc68a`, width 4–5 px at 1080p. Keep it visible against both dark and bright backgrounds without making the figure glow.

### Lead female

- Same stick-figure construction, face vocabulary, thick limbs, hand/foot rules, and lit-side rim edge as the lead male.
- Use a slightly lighter ink/cream head fill to distinguish her silhouette while retaining the same simple face language.
- One signature garment: soft-violet top `#9b59b6`; this color is locked to her and is her only character color. A ponytail, bun, or simple dark hair shape may distinguish her silhouette.

### Supporting cast and continuity

- In narrative scenes, use 2–3 figures in most shots when the beat supports an interaction, reaction, or social consequence. A solo close-up or mechanism insert is correct when it tells that beat more clearly; never add a crowd just to fill space. Keep no more than four figures in focus; distant extras may be simplified dark silhouettes.
- Every recurring figure gets exactly one signature colored garment/accessory and keeps it for the whole video. Never reuse either lead's locked color for a supporting character. Examples: best friend green jacket `#27ae60` plus cap; scientist white lab coat plus round glasses; skeptic orange shirt `#e67e22` plus headband; partner teal jersey `#1abc9c` plus ponytail; authority maroon tracksuit `#8b1a1a` plus one fitting prop; child yellow tee `#f1c40f` at 72% scale with a proportionally larger head; mysterious figure black trench and fedora; other role-appropriate jackets, shirts, jerseys, tracksuits, lab coats, or dresses. Extras may be plain ink with no color.
- Maintain a character sheet in `data/characters.json` (or the project's existing character manifest): ID, role, head fill, exact signature item and hex, hair/headwear, scale, eye/mouth/brow vocabulary, and rim-light color. Re-describe the full design in every standalone image/video prompt or shot-board card; never rely on “same as before.” In code, instantiate from the locked manifest so repeat shots cannot drift.
- When the narration mentions a friend, doctor, teacher, rival, family member, speaker, or reacting group, put the relevant figure on-screen with a readable pose/expression. Do not invent factual people or dialogue; any fictional example must be framed as an illustration.
- Far-side arms/legs use subtle dark purple-gray `#2b2333`; near-side limbs stay `#0e0b12`. This difference adds depth without outlines.

## 3. Acting and motion

Expression and silhouette do most of the acting. Available expressions: neutral, smile, happy, joy, surprised, shocked, scared, worried, nervous, angry, determined, sad, cry, smirk, sleepy, thinking, confused, and awe. Use simple eyes (dot, ring, or wider circle), mouth shapes (small smile, flat, grin, frown, smirk, wavy, open-o), and occasional raised/worried/angry brows only. Change expression on the narrated beat and motivate every change through the event. Characters blink naturally about every 2.5–4 seconds. Give standing/sitting poses subtle breathing and purposeful head turns, tilts, reaches, points, shrugs, waves, walks, or reactions. Talking mouth motion belongs only to a character visibly speaking quoted dialogue; narrator voice never lip-syncs to the lead.

Keep feet grounded with contact shadows. Move the camera in every shot (slow push/pull, lateral drift, tracking, crane, motivated roll, or impact shake), unless a brief hold is essential to read a diagram; then keep characters or scene elements moving. Let parallax layers move at different rates. Smoothly move within a set; hard-cut only for a real location or time change. Do not regenerate the world mid-shot.

## 4. Environments and recurring motifs

Build every location from simple, specific flat shapes with soft gradients, clean geometry, and distant layers extending past the frame. Limit environment texture to floor lines, window mullions, blinds, and lit-window grids. Use depth layers where the shot supports them: sky, skyline/hills, architecture/back wall, floor and props, figures, then one soft foreground shape such as glassware, a plant, railing, crowd edge, or a shoulder. Most medium shots may use a subtle foreground layer; keep it soft and out of the focal area.

Large windows with mullions and sky gradients are a signature environment element when location-appropriate: sunset/golden hour or night skyline, warm lit windows, moon/sun glow, optional blinds. Other usable settings include labs, cafes, bedrooms, kitchens, classrooms, offices, hospitals, locker rooms, stadiums, streets, rooftops, piers, roads, parks, airports, and space. Do not force windows into locations where they do not belong. Extend walls, floors, and skies beyond the camera frame so moves never expose edges.

Keep the environment alive in nearly every appropriate scene with one or two motivated details: a slowly drifting cloud, moving clock hand, flickering/warming light, paper or leaf in a draft, rain, distant crowd, steam, bubbles, or a few dust motes. They should support location and mood, not shimmer across the whole frame or compete with the face/action. Freeze-frame/time-stop is a signature beat: use 1–3 per video only when the story earns it; enter with a brief flash, cool the palette, hold particles in place, allow only the hero to move, and show a small multiplier badge only when the number is part of the story. Stars, lens streaks, and fog are occasional effects, not a permanent layer.

## 5. Cinematography and shot vocabulary

Plan a varied visual rhythm across the whole edit; never repeat a shot type or near-identical composition consecutively. Use these approximate shares as a guide, not a quota that creates filler:

- Establishing wide ~10%: location and small figures, slow push-in.
- Medium interaction/two-shot ~25%: side or three-quarter view, figures facing each other.
- Over-shoulder ~10%: a large soft foreground silhouette, sharp subject behind.
- Expressive face close-up ~10–15%: head fills much of the composition, readable rim crescent, darkened/soft background.
- Insert/macro ~10%: one simple object, hand-end/arm action, phone/watch/door/food detail; no visible fingers at ordinary scale.
- Top-down/diagram ~5%: clear trajectory or mechanism with one short timing/value label.
- Use occasional profile, low-angle, overhead, point-of-view, tracking, or pull-back reveal to cover remaining beats.
- Blueprint diagram when it clarifies a real mechanism: navy grid, light-blue line art, restrained gold highlight and only essential labels.
- Data card/UI only when narration introduces a number or measure: reveal and animate the specific number as it is spoken.
- Title card and ending are short, integrated scene moments, not persistent HUDs. When an end screen is used, include the thought-provoking question in italic serif, a small comment bubble, a subscribe pill, and the relevant cast lined up; keep each element clear and readable, and do not force an end card into a story whose emotional ending works better without it.

Show one dominant action and a clean silhouette. Use thirds; center only when a face close-up or deliberate symmetry calls for it. Change shot scale/viewpoint when the explanation changes. Use an establishing setup, action/interaction, revealing insert, mechanism/diagram, consequence, and emotional/payoff angle as the story needs. Do not chase percentages by repeating a shot or adding a gratuitous cut.

## 6. Graphics, typography, and text

- Fredoka Bold for titles and big question/chapter phrases: all caps, generous tracking, restrained warm glow.
- Nunito Black for labels, measurements, readouts, and numbers.
- Playfair Display Black Italic for the final thought-provoking question.
- Gold emphasizes a key number; coral/red marks a genuinely alarming value; cream handles labels; blueprint blue is reserved for technical diagrams.
- Allowed in-scene graphics: title/question, tiny multiplier/day badge, readout, one data card with counter/curve, comparison bar, dimension arrow, leader-line label, meter, blueprint, speech bubble for actual dialogue, and a short end question/comment/subscribe treatment when appropriate. Graphics belong to the scene and share its perspective/light; do not add a separate post-production HUD layer.
- Every narrated number/measurement that matters should appear in a readable in-scene graphic timed to the word. Do not display trivial numbers that add no understanding.
- Keep text minimal: at most 1–2 short labels at once; no full sentences outside the title/question/end card. Give each graphic a clear reason to appear, animate in with a restrained scale/fade or a single soft pop, then clear it before the next beat. Never duplicate the active caption as a banner or pile a label, title, badge, and caption together.

## 7. Hard exclusions and QA checks

Never use photoreal people, realistic face anatomy, nose/ear details, character gradients, thick outlines on scenery, frozen/static camera for an entire shot, narrator lip-sync, ungrounded characters, changing garment colors, over four foreground figures, a white empty backdrop (except a one-frame flash), walls of text, repeated signature colors, or non-style treatments such as 3D characters/anime/clay/watercolor/pixel art. Avoid making the lead always dead-center, filling every frame with props, overdoing atmosphere/grain/glow, or letting a foreground layer cover an expression or caption.

Before staging, inspect a full contact sheet and full-size opening, interaction, close-up, diagram/data, freeze/reveal if used, and ending frames. Check exact character garment colors and silhouettes across shots, rim-light visibility, feet/contact shadow, expression beats, camera movement, graphic timing/legibility, safe areas, and no caption collisions. If a scene is busy at phone size, remove elements before adding detail.
