# Deity iconography (`core/deity.js`)

Hindu deities in this style are still tall-tale toons — same big head, bean body, stick limbs — but with the
features that make them recognisable on sight. A Telugu mythology video **must** use `deityLook(name)`; a plain
toon head is wrong for Ganesha, Shiva, Hanuman and every other god.

```js
import { Toon, PROPS } from './core/toon.js';
import { deityLook } from './core/deity.js';

const ganesha = new Toon(deityLook('ganesha'), { height: 1.75 });
const shiva  = new Toon(deityLook('shiva', { body: '#8FC7E8' }), { height: 1.8 });
// hand props: any deity prop is also a normal PROPS entry
shiva.set({ mood: 'proud', holdR: PROPS.trishul, holdL: PROPS.damaru });
```

`deityLook(name, patch)` returns a normal toon look (colours + `deity: name` + `deityOpts`), so every Toon feature
works: `mood`, `blink`, `talk`, `lean`, `flip`, `restyle`, and every prop.

Available names: `ganesha` · `shiva` · `vishnu` · `krishna` · `rama` · `hanuman` · `parvati` · `lakshmi` ·
`saraswati` · `durga` · `murugan` · `asura` (alias `rakshasa`).

## Canonical features, per deity

Researched from Britannica, Wikipedia, museum iconography guides (Smithsonian, LACMA, Birmingham Museum of Art) and
the traditional iconographic texts they summarise. These are the *identifying* marks — a scene may skip a minor
attribute, but it must never contradict these.

| deity | skin | must show | optional |
|---|---|---|---|
| **Ganesha** | warm tan | elephant head, **large fan ears**, **curving trunk**, **one whole + one broken tusk**, pot belly, three-pointed crown, vermilion tilak | snake as sacred thread, modak/laddu, mouse vahana, axe, goad, noose |
| **Shiva** | **blue** (or ash-white; blue here) | **third eye** (vertical, forehead), **matted jata bun + crescent moon**, **cobra coiled at the neck**, **trishul**, vibhuti (three ash lines) | damaru, Ganga stream in the locks, tiger skin, rudraksha, skull garland (fierce forms only) |
| **Vishnu** | blue | **four arms**, **chakra** (discus) + **conch**, tall kirita crown, U-shaped namam | mace, lotus, garland (vanamala), Shesha |
| **Krishna** | blue | peacock feather in the hair, **flute**, yellow dhoti, kirita crown | cow, butter pot, discus |
| **Rama** | blue | bow (and quiver), kirita crown, tilak, yellow dhoti | arrow, Sugriva/Hanuman at his side |
| **Hanuman** | orange | **monkey muzzle + ears**, **tail**, mace (gada), tilak | mountain (Sanjeevani), army of monkeys |
| **Parvati** | warm fair | jewelled crown, bindi, necklace + earrings, red/green sari | nose ring, lotus, trishul (shared with Shiva), lion/tiger |
| **Lakshmi** | golden fair | crown, bindi, jewellery, **lotus**, red sari | coins, owl, elephants |
| **Saraswati** | fair | crown, bindi, jewellery, **white sari**, veena, swan | book, rosary |
| **Durga** | warm fair | crown, bindi, jewellery, **many arms**, trishul, lion | chakra, conch, sword, demon (Mahishasura) |
| **Murugan / Kartikeya** | warm tan | **vel (spear)**, crown, red/yellow | peacock, rooster |
| **Asura / Rakshasa** | red-brown | spiked crown, **fangs**, heavy moustache, angry brow | ten heads (Ravana — see below), extra arms, weapons |

Rules of thumb:
- **Ganesha's trunk turns to the character's left** (idampuri) in the common form; the module draws it that way. Do
  not mirror it into a right-turning (valampuri) trunk by accident — `flip` mirrors the whole cut-out, which is fine
  for staging but then he is facing the other way.
- **The broken tusk is his right tusk.** The module shortens the character's right tusk automatically.
- **Shiva is blue, never green or grey**, for this channel's palette; his throat may be darker blue.
- **Devis keep their jewellery in every shot** — it is what separates Parvati from a generic woman toon.
- **Do not draw a deity as a plain toon with only a crown.** That is the failure this module exists to prevent.

## Ravana and ten heads

Ten actual heads cannot read at 1080×1920 in a 3-second shot. Use one head with the asura crown + fangs, and put
**nine small crowns fanned behind him** as a 2D overlay (`stamp`-style) in the one shot where the ten heads matter.
State it in the narration ("ten heads") so the picture supports the words instead of competing with them.

## Camera and staging

- Deity cut-outs are the same size as people: `height` 1.75–1.9. A god is not a giant unless the script says so —
  scale him with camera distance, not with `height`, or he will not fit beside humans in the same shot.
- Keep the camera within ~60° of facing the cut-out (as with any toon) or the trunk/ears flatten.
- Crowns and jata add ~0.25 m above the head: the renderer already lowers the head slightly for crowned
  deities, but **never animate a crowned deity with `legs: 'jump'`** — the jump lifts the head above the
  cut-out box and clips the crown. Use a camera pop, `bob`, or a scale punch instead.
- The snake head and the extra pair of arms sit at shoulder height — avoid staging another character exactly there.

## What the module draws

| layer | when | contents |
|---|---|---|
| `drawDeityBack` | before the head | Ganesha's ears · Shiva's jata, crescent, side locks, Ganga, cobra coil + hood · Hanuman's tail · four arms |
| `drawDeityFront` | over the face | Ganesha's trunk, tusks, nostril · Shiva's third eye + vibhuti · namam · tilak/bindi · muzzle + monkey ears · fangs · jewellery, earrings, nose ring |
| `drawDeityTop` | after the hat | mukut / kirita / devi / asura crown · peacock feather |

Hand props (in `PROPS`, so `holdL`/`holdR` work): `trishul`, `chakra`, `shankha`, `gada`, `vel`, `flute`, `lotus`,
`damaru`, `modak`, `bow`.

## Empty hands are fine

Not every scene needs the trishul. If a deity is talking, cooking, or chasing a mouse, give them both hands free —
the iconography is in the head and body, not in the props. Props are for establishing shots and payoffs.
