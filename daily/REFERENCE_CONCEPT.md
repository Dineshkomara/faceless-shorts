# English Concept Explainer Profile

Use for the English channel across psychology, instinct, everyday behavior, body/brain, animals, physical science, history, and engineering. The reference idea is “The Instinct That Makes You Crash”: a simple situation exposes a counterintuitive human mechanism, then visuals let viewers watch that mechanism happen. Use the structure as a guide; do not repeat that topic or invent a true story.

## Topic and evidence

- Pick one concrete question with a one-sentence retellable answer. Prefer familiar situations with a surprising mechanism over broad “facts about X” topics.
- Check key factual claims against at least two credible sources. Favor the original paper, university lab, government or engineering authority, and a reputable synthesis. Save source titles and direct URLs in `script.json` as objects with `title` and `url` fields.
- Distinguish established evidence from proposed explanations. Do not invent precise rates, causal certainty, named experiments, accidents, people, or quotations. A hypothetical scene must be visibly and verbally treated as an illustration.
- Use one narrator and connected, conversational sentences. No list-like delivery, fake urgency, fabricated dialogue, repetitive rhetorical questions, or forced “congratulations” outro.
- Target 45–90 seconds when the idea supports it. Cut or materially reframe every 2–4 seconds on average; hold longer only while the central mechanism visibly changes.

## Visual direction

- In the default 3D styles, use a topic-specific 3D set and objects, not a stock-scene slideshow. A selected style profile such as cinematic-what-if supplies its own renderer and complete visual rules; follow it instead of this default. Characters may act out a situation, but every object and gesture must explain the same concept.
- Plan 3–5 useful sets or viewpoints: a recognizable setup, a close detail, a cutaway/model of the hidden mechanism, a consequence, and a payoff. Use only the sets that help this idea.
- Keep one dominant focal action in each shot. Use a clean background and deliberate negative space. Prefer a small coherent palette with one accent.
- Captions are the only persistent overlay. Remove persistent HUD panels, repeated scene banners, decorative UI, needless labels, duplicate captions, excessive particles/grain/bloom, and props unrelated to the explanation. Use at most one short explanatory label in addition to captions, and only while it carries useful information.
- Never repeat a composition in back-to-back shots. Avoid showing the same hero prop at slightly different zoom levels; change the action, viewpoint, scale, or scene when the idea changes.
- Before render, inspect the contact sheet at phone size. For each frame ask: “What should I look at first? Does every visible element help the spoken idea?” Simplify any frame with competing focal points or text. Inspect captions against the safe area and key frames full size.

## Audio

- Set `script.json` `music` to `concept`: a warm, restrained curiosity bed that builds gently with discovery and resolves at the payoff. Keep it under narration and duck it smoothly.
- Use a few quiet, meaningful `heartbeat`, `tock`, `whoosh`, `pop`, or `thud` cues at real emphasis points. Engineering topics may use `river_flow`, `excavation`, `concrete`, `machinery`, and `gate` when those actions are on screen. Do not add an effect to every cut.
- Preview narration and mix; reject clipped speech, harsh sibilance, audible pumping, masked consonants, and effects louder than the spoken line.

## Learning requirement

At the start of each English run, read the latest `feedback_loop.py guidance --channel en` result and explicitly apply its single next improvement. At the end, complete `review/quality_review.json`, including reviewed frame paths, scores, checks, source list, asset-library search/use decisions, and one concrete next improvement. Run the feedback QA gate before staging. If it fails, simplify or fix the work and re-review; a failed video is not staged.
