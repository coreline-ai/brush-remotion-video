# Asset Generation Prompts

## Purpose

Use these patterns when asking an image model, artist, or asset generator to create game-ready motion assets.

## Universal Sequential Asset Prompt

```text
Create a {frameCount}-frame {assetType} sprite sheet arranged in a {columns}x{rows} grid.
Each frame must fit inside a {frameWidth}x{frameHeight} transparent cell.
Use {paddingInsideFrame}px internal transparent padding inside every cell.
Use {gap}px transparent spacing between cells and {margin}px transparent outer margin.
Do not let any character, weapon, trail, glow, shadow, particle, text, label, or effect cross into another frame cell.
Keep the same scale, pivot, baseline, camera angle, lighting, line weight, color palette, and art style across all frames.
Show a clear progression of motion from frame 1 to frame {frameCount}.
Use transparent background.
No grid lines, no labels, no text, no watermark.
```

## Korean Version

```text
{frameCount}프레임 {assetType} 스프라이트시트를 {columns}x{rows} 그리드로 생성한다.
각 프레임은 {frameWidth}x{frameHeight} 투명 셀 안에 들어가야 한다.
각 셀 내부에는 {paddingInsideFrame}px 투명 여백을 둔다.
셀과 셀 사이에는 {gap}px 투명 간격을 두고, 시트 바깥에는 {margin}px 투명 외곽 여백을 둔다.
캐릭터, 무기, 트레일, 빛 번짐, 그림자, 파티클, 텍스트, 라벨, 이펙트가 다른 셀을 침범하면 안 된다.
모든 프레임에서 scale, pivot, baseline, 카메라 각도, 조명, 선 두께, 색상 팔레트, 아트 스타일을 동일하게 유지한다.
1프레임부터 {frameCount}프레임까지 동작이 자연스럽게 이어져야 한다.
투명 배경을 사용한다.
최종 이미지에 그리드 선, 라벨, 텍스트, 워터마크를 넣지 않는다.
```

## Hit Spark Prompt

```text
Create a 6-frame hit spark VFX sprite sheet in a 3x2 grid.
Each frame is 128x128 transparent pixels, with 16px internal padding, 24px transparent gap, and 16px outer margin.
The spark starts as a sharp white/yellow impact point, expands into angular shards, then fades.
Keep the impact pivot centered at [64,64] in every frame.
No spark, glow, particle, or shadow may cross into another cell.
Transparent background. No labels. No grid lines.
```

## Slash Trail Prompt

```text
Create an 8-frame stylized sword slash trail sprite sheet in a 4x2 grid.
Each frame is 256x256 transparent pixels, with 24px internal padding, 32px transparent gap, and 16px outer margin.
The slash begins with anticipation, forms a bright curved arc, peaks at frame 4, then fades by frame 8.
Keep pivot at [128,192] and maintain consistent perspective across frames.
No trail, glow, particle, or weapon silhouette may cross into another cell.
Transparent background. No labels. No grid lines.
```

## Reward Pop Prompt

```text
Create a 6-frame reward icon pop animation sprite sheet in a 3x2 grid.
Each frame is 192x192 transparent pixels, with 16px internal padding, 24px transparent gap, and 16px outer margin.
The reward icon scales from small to overshoot, settles, emits small sparkles, then rests.
Keep icon center pivot at [96,96].
Sparkles must stay inside each frame cell and must not overlap adjacent cells.
Transparent background. No text. No grid lines.
```

## Negative Prompt Additions

Add these when using image generation:

```text
No overlapping cells, no inconsistent character size, no shifting pivot, no changing baseline, no cropped body parts, no merged frames, no irregular spacing, no perspective change, no text, no labels, no watermark, no grid lines in final image.
```

## Prompt Review Gate

Before generating, verify that the prompt includes:

- frame count
- grid columns and rows
- exact frame width and height
- internal padding
- transparent gap
- outer margin
- pivot
- baseline if character motion
- no-overlap instruction
- consistent style instruction
- transparent background
