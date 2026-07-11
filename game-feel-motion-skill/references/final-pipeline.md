# Final Game Feel Motion Pipeline

## Purpose

Turn a game event into a polished, implementable, and reviewable motion system.

## Pipeline

```text
1. Event
2. Feel Goal
3. Motion Vocabulary
4. Asset Brief
5. Sequential Asset Contract
6. Asset Generation / Production
7. Manifest / Atlas
8. Implementation Values
9. Engine Integration
10. In-game Test
11. Block / Approve QA
```

## 1. Event

Identify the trigger:

- input: tap, hold, drag, release, cancel, combo, joystick action
- combat: hit, crit, block, parry, dodge, death, skill cast
- reward: coin, item, rare drop, level up, quest clear
- UI: button, modal, tab, toast, inventory, tooltip, card
- transition: scene change, map enter, portal, loading, victory/defeat

## 2. Feel Goal

Choose one primary feel and one secondary feel.

| Feel | Motion bias |
|---|---|
| Snappy | short duration, high contrast timing, hard stop |
| Heavy | longer anticipation, strong impact frame, slower recovery |
| Elastic | spring, overshoot, rebound, squash/stretch |
| Premium | smooth easing, layered delay, restrained effects |
| Dangerous | fast attack, sharp flashes, high contrast VFX |
| Rewarding | burst, stagger, glow, count-up, audio/haptic marker |
| Soft | rounded easing, low contrast, low amplitude |
| Urgent | short pulses, repeated attention, high readability |

## 3. Motion Vocabulary

Use stable names so design, art, and code discuss the same behavior.

| Name | Use |
|---|---|
| pop-in | small UI/object appears with scale overshoot |
| press-down | button compresses on input |
| release-pop | button rebounds after release |
| hit-flash | target flashes briefly on damage |
| hit-stop | short gameplay pause at impact |
| stagger | delayed sequence across multiple items |
| reward-burst | particles/glow/icons expand outward |
| number-ticker | numeric value animates upward |
| slash-trail | attack arc or weapon trail follows swing |
| cooldown-wipe | radial/linear mask reveals skill readiness |
| screen-shake | camera offset used for impact |
| radial-reveal | circular transition mask opens or closes |
| wipe-transition | directional scene transition |
| rubber-band | UI/object overshoots and returns |

## 4. Asset Brief

Create the asset brief before implementation.

Minimum fields:

- motion name
- gameplay purpose
- art style
- required source assets
- required game-ready exports
- frame count and fps
- frame size, gap, margin, padding
- pivot and baseline
- loop mode
- engine target
- QA risks

Use `../assets/templates/asset-brief.md` or `../assets/templates/sequential-asset-brief.md`.

## 5. Sequential Asset Contract

For frame-based motion, require:

- same cell size
- same pivot
- same baseline
- same scale
- same camera angle
- same lighting direction
- fixed margin
- fixed gap
- internal transparent padding
- no overlap across cells
- transparent background
- manifest with layout metadata

Read `sequential-motion-assets.md` for strict rules.

## 6. Asset Generation / Production

Choose the right production path.

| Target | Recommended asset form |
|---|---|
| 2D character | frame-by-frame spritesheet or skeletal animation |
| 2D VFX | spritesheet, particle texture, or shader mask |
| UI | SVG/PNG states plus motion tokens |
| Transition | mask sequence, shader mask, or procedural animation |
| 3D character | rigged animation clips plus VFX attachments |

Keep source files separate from game-ready exports.

```text
assets/source/
assets/game-ready/
assets/atlases/
assets/manifests/
```

## 7. Manifest / Atlas

Every sequential asset must include machine-readable metadata:

- id
- type
- motion
- frame count
- fps
- columns / rows
- frameWidth / frameHeight
- margin / gap / internal padding
- pivot
- baselineY
- loop
- tags

Validate with `../scripts/validate_spritesheet_manifest.py`.

## 8. Implementation Values

Every motion needs concrete values:

- duration in ms
- frame count at target fps
- easing or spring
- delay/stagger
- amplitude
- reduced-motion fallback
- trigger and cancellation rule

Read `motion-values-and-tokens.md`.

## 9. Engine Integration

Do not wire raw input directly to visual effects. Use events/actions.

```text
INPUT → action
UPDATE → state/event
RENDER → animation/VFX/UI response
```

Good:

```text
action.attack.pressed → combat.attack.started → vfx.slash.spawn
```

Bad:

```text
MouseDown → directly mutate slash sprite frame
```

## 10. In-game Test

Test in the real context:

- gameplay distance
- target resolution
- real background
- multiple simultaneous effects
- low-end performance mode
- reduced-motion setting
- keyboard/mouse/gamepad/touch as relevant

## 11. Block / Approve QA

Approve only when the motion:

- communicates gameplay state clearly
- preserves input responsiveness
- has clean asset spacing and manifest data
- matches art direction
- does not hide critical information
- has accessible fallback
- can be implemented deterministically

Read `review-standards.md` for final gates.
