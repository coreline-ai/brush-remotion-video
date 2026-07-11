# Motion Values and Tokens

## Duration Defaults

| Motion | Duration |
|---|---:|
| button press-down | 60-90ms |
| button release-pop | 100-160ms |
| UI pop-in | 140-220ms |
| tooltip fade/slide | 120-180ms |
| modal enter | 180-280ms |
| modal exit | 120-200ms |
| hit flash | 50-100ms |
| hit spark | 100-180ms |
| hit stop | 30-80ms |
| light attack | 120-220ms |
| heavy attack | 280-520ms |
| reward burst | 400-900ms |
| number ticker | 350-1000ms |
| scene transition | 350-900ms |

## Easing Defaults

| Intent | Easing |
|---|---|
| snappy enter | cubic-bezier(0.16, 1, 0.3, 1) |
| fast exit | cubic-bezier(0.7, 0, 0.84, 0) |
| standard UI | cubic-bezier(0.2, 0, 0, 1) |
| soft UI | cubic-bezier(0.33, 1, 0.68, 1) |
| mechanical | linear or stepped |
| anticipation | ease-in |
| impact recovery | ease-out |

## Spring Defaults

| Feel | stiffness | damping | mass |
|---|---:|---:|---:|
| subtle UI | 260 | 28 | 1 |
| elastic UI | 360 | 20 | 1 |
| heavy object | 180 | 24 | 1.4 |
| quick rebound | 520 | 32 | 0.8 |

## Frame Count Reference

At 30fps:

| Duration | Frames |
|---:|---:|
| 66ms | 2 |
| 100ms | 3 |
| 133ms | 4 |
| 167ms | 5 |
| 200ms | 6 |
| 267ms | 8 |
| 333ms | 10 |
| 500ms | 15 |
| 800ms | 24 |

At 60fps, double the frame count.

## Stagger Defaults

| Use | Delay |
|---|---:|
| small UI list | 20-40ms |
| card reveal | 40-80ms |
| reward items | 60-120ms |
| dramatic sequence | 120-200ms |

## TypeScript Token Shape

Use `../assets/templates/motion-tokens.template.ts` as a starter.

Required groups:

- `duration`
- `easing`
- `spring`
- `stagger`
- `frameRate`
- `spritesheet`
- `reducedMotion`

## Reduced Motion

Every large motion needs an accessible fallback:

- replace large movement with opacity/color/scale under 1.03
- remove screen shake
- remove large camera movement
- keep gameplay state visible
- preserve timing enough that gameplay logic remains clear
