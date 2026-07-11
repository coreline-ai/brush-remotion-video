# Sequential Motion Assets

## Purpose

Use this reference when creating frame-by-frame spritesheets, VFX sequences, slash trails, reward bursts, cooldown sequences, transition masks, or any generated image asset that contains multiple motion frames.

## Contract

Every sequential asset must follow this contract:

```text
fixed cell size
+ fixed grid layout
+ fixed margin
+ fixed gap
+ fixed internal padding
+ fixed pivot
+ fixed baseline
+ fixed scale
+ transparent background
+ no cross-cell overlap
+ manifest metadata
```

## Layout Terms

| Term | Meaning |
|---|---|
| frameWidth | width of one grid cell |
| frameHeight | height of one grid cell |
| columns | number of frames per row |
| rows | number of frame rows |
| margin | transparent border around the whole sheet |
| gap | transparent spacing between cells |
| paddingInsideFrame | transparent safe zone inside each cell |
| pivot | anchor point used by the engine |
| baselineY | shared floor/foot line for characters |

## Sheet Size Formula

```text
sheetWidth =
margin * 2
+ columns * frameWidth
+ (columns - 1) * gap

sheetHeight =
margin * 2
+ rows * frameHeight
+ (rows - 1) * gap
```

Example:

```text
columns = 4
rows = 2
frameWidth = 256
frameHeight = 256
margin = 16
gap = 24

sheetWidth = 16*2 + 4*256 + 3*24 = 1128
sheetHeight = 16*2 + 2*256 + 1*24 = 568
```

## Recommended Defaults

| Asset type | Frame size | Frames | Gap | Internal padding | FPS |
|---|---:|---:|---:|---:|---:|
| small UI pop | 128x128 | 4-6 | 12-16 | 8-12 | 30 |
| reward icon burst | 192x192 | 6-10 | 16-24 | 12-16 | 30 |
| hit spark | 128x128 | 4-6 | 16-24 | 12-16 | 30 |
| slash trail | 256x256 | 6-8 | 24-32 | 16-24 | 30 |
| character attack | 256x256 | 3-8 | 24-32 | 16-24 | 24-30 |
| character death | 256x256 | 8-16 | 24-32 | 16-24 | 24-30 |
| transition mask | 512x512 | 8-16 | 32 | 0-16 | 30 |

## Non-Overlap Rules

Block the asset if any of these cross into another frame cell:

- character silhouette
- weapon
- slash arc
- glow
- shadow
- particle
- dust
- explosion bloom
- UI shine
- text or label

Generated assets often fail because glow/trails extend beyond cell bounds. Require more internal padding or larger cells when motion contains large arcs or particles.

## Pivot and Baseline Rules

For characters:

- pivot should usually be at feet center or body center depending on engine convention.
- baselineY must remain constant across all frames.
- head height may change for squash/stretch, but feet contact should not drift unless the animation intentionally jumps.

For UI:

- pivot should usually be center.
- shadow should stay inside the cell.
- scale changes must not cross the internal padding safe zone.

For VFX:

- pivot should match impact point.
- expanding particles must remain inside the internal padding.
- if the VFX expands beyond the cell, increase frame size instead of letting it bleed.

## Manifest Example

```json
{
  "id": "spr_player_attack_slash_01",
  "type": "spritesheet",
  "motion": "attack-slash",
  "frames": 8,
  "fps": 30,
  "layout": {
    "columns": 4,
    "rows": 2,
    "frameWidth": 256,
    "frameHeight": 256,
    "margin": 16,
    "gap": 24,
    "paddingInsideFrame": 16
  },
  "pivot": [128, 192],
  "baselineY": 192,
  "loop": false,
  "tags": ["combat", "slash", "player"]
}
```

## QA Checklist

Block if:

- cells are uneven
- gap differs between frames
- frame count does not match manifest
- sheet size does not match formula
- pivot or baseline shifts without intent
- any visible pixel crosses into neighboring cells
- alpha bleed appears at cell edges
- the sequence jitters when played
- source file is missing for a production asset
