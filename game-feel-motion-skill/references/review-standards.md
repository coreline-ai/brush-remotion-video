# Motion and Asset Review Standards

## Verdicts

Use only:

- `Approve`
- `Block`

Do not use vague verdicts like "looks okay" or "needs polish" without a Block/Approve decision.

## Approve Criteria

Approve only if all are true:

- motion communicates the intended gameplay/UI state
- input remains responsive
- timing values are explicit
- generated assets follow spacing and non-overlap rules
- sequential frames have consistent pivot, baseline, scale, camera, and style
- manifest matches the actual layout
- art style matches the project
- motion does not hide important gameplay information
- reduced-motion behavior is defined for large movement/shake
- implementation can be repeated deterministically

## Block Criteria

Block if any are true:

- motion name is vague or not tied to gameplay purpose
- duration/easing/spring/frame count is missing
- generated frames overlap or have inconsistent spacing
- glow/trails/shadows cross into adjacent cells
- pivot/baseline shifts unintentionally
- spritesheet dimensions do not match the manifest formula
- asset style conflicts with the project
- hit/reward/skill feedback is not readable at gameplay distance
- UI motion distracts from hierarchy
- color is the only feedback channel
- screen shake or flashes are too strong without fallback
- source files or manifests are missing for production-ready sequential assets

## Review Format

```md
## Verdict
Block or Approve

## Reason
- ...

## Required Fixes
- ...

## Checked
- event/feel goal
- motion vocabulary
- asset brief
- sequential spacing
- manifest
- timing values
- implementation path
- accessibility fallback
```

## Asset-Specific Review

For each sequential asset, check:

- `sheetWidth = margin*2 + columns*frameWidth + (columns-1)*gap`
- `sheetHeight = margin*2 + rows*frameHeight + (rows-1)*gap`
- `frames <= columns*rows`
- pivot is inside the frame
- baselineY is inside the frame
- paddingInsideFrame is present
- gap is large enough for glow/trails
- no labels or grid lines in final export

## In-Game Review

Test with:

- actual gameplay camera
- real background
- target device resolution
- rapid repeated input
- multiple simultaneous VFX
- reduced-motion enabled
- low-performance mode when available
