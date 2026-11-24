# Engineering Explainer Visual Profile

Use this profile for English videos about dams, bridges, buildings, machines, infrastructure, and other physical systems. The target is a compact animated engineering documentary like the supplied Polavaram reference: a clear narrated explanation carried by changing 3D diagrams, construction sequences, maps, and labels. The reference is about 98 seconds in 9:16. Its visual sequence moves from a river locator map to diversion-flow diagrams, machinery close-ups, dam cross-sections, and the finished spillway. This profile defines a visual language, not content to copy.

## Story and factual standard

- Start with the physical problem and a striking consequence or scale comparison. Explain the system in cause-and-effect order: site/context → constraint → temporary works or first step → structural mechanism → construction sequence → finished system → why it matters.
- Choose only the beats that fit the topic. For a dam, this may mean river diversion, cofferdams, foundation treatment, dam sections, spillway, gates, and power/water route. For a bridge, show foundations, supports, temporary centering, load path, and the completed crossing. Never force arches, concrete, or any other mechanism into an unrelated topic.
- Build the narration from facts verified against at least two reliable sources. Prefer official project/engineering sources, academic or professional references, and reputable reporting. Save source titles and URLs in `script.json`. Attribute disputed designs, dates, dimensions, completion status, and project targets; distinguish planned targets from achieved work.
- Keep the narration conversational and explanatory. Target 90–180 seconds when the process needs it; do not pad to hit a fixed duration. Write a distinct visual beat for each meaningful clause. No duplicated topic text, fabricated numbers, generic claims that modern structures fail, or unsupported superlatives.
- The first 2–3 seconds must show the subject and the core puzzle. End by resolving that puzzle, with a brief audience prompt only if it follows naturally.

## Visual language

- Use the existing Three.js scene pipeline to create topic-specific 3D models and cutaways. The explanatory model is the hero: no talking cartoon cast, stock-photo slideshow, or repeated generic establishing shot for this profile.
- Use a sequence of distinct compositions: a map or aerial locator; a wide site view; close construction details; a cross-section or exploded view; a finished-system view. Reframe, orbit, crane, dolly, or cut when the narration changes scale or mechanism. Keep each shot legible on a phone.
- Animate the process in visible steps. Components enter, move, fill, lock, or carry load at the moment the narration explains them. Use arrows, flow paths, dashed construction lines, section cuts, and restrained labels to reveal the mechanism. Keep the geometry readable and internally consistent across shots.
- For rivers and waterworks, show the water route explicitly: old channel, diversion route, temporary works, and final route must not visually contradict one another. For structural systems, make force/load paths visible and label them plainly.
- Use clean, restrained colors: earth/stone for ground and structure, blue for water, one warm accent for the active component or key phrase. Give labels a solid or outlined backing and enough contrast. Do not place essential details beneath subtitles or platform controls.
- On-screen headings name the current structure or stage in concise English. Captions follow the narration, use short readable phrases, and highlight the current spoken word or phrase in the warm accent. Keep one caption line or two short lines within the mobile safe area.
- Add a small unobtrusive project/channel mark. Avoid persistent decorative UI, crowded technical labels, and title cards that delay the explanation.

## Edit, sound, and review gates

- Cut or materially reframe every 2–5 seconds on average. A complex mechanism may hold longer while it visibly animates. Avoid a static camera and avoid motion that distracts from a diagram.
- Set `script.json` `music` to `engineering`: a restrained, evolving documentary bed with warm low pads, a soft measured pulse, and sparse high notes. It should grow slightly into the construction/reveal, settle under dense narration, and resolve at the completed structure. Avoid a bright pop beat, suspense-horror drone, or triumphal fanfare.
- Declare cues with `cue(t, type)` in `src/shots.js` so `capture.mjs cues` writes them into `data/cues.json`. Use the mixer cues `river_flow`, `excavation`, `concrete`, `machinery`, and `gate` only where they match visible actions. Use a few soft transitions or impacts only when they clarify a cut or reveal. Aim for roughly 5–10 meaningful cues in a 90-second piece, not one per shot. Keep water as a quiet continuous bed only for shots that show water; never let effects mask speech.
- Narration remains dominant; the music preset is mixed quietly and ducked smoothly under speech. Leave some moments and cuts without effects so the mechanism and natural pauses can breathe.
- Before rendering, run the scene/check command and correct broken assets, invalid paths, and missing timing. Render the visual contact sheet and inspect the opening, one frame from each major process stage, and the payoff. At least one of the inspected frames must show that labels, arrows, and captions remain inside the vertical safe area.
- After rendering, verify the final file has video and audio, is vertical 9:16, has no truncated narration, and has a matching cover and review sheet. Never stage for upload if these checks fail. Record any accepted minor visual issue in the project ledger.

## Suggested beat map

1. Hook: show the completed structure or the dangerous physical problem.
2. Locate it: map/aerial view and one useful scale or geography fact.
3. State the constraint: water, soil, load, height, access, or material.
4. Explain the construction order with an animated cutaway.
5. Zoom into the key engineering mechanism and label what carries force or moves flow.
6. Reassemble to the finished structure; show the function and one sourced project fact.
7. Resolve the opening question.

This is an adaptable checklist. Drop irrelevant beats and add topic-specific ones; do not reuse the Polavaram sequence as a factual template for every project.
