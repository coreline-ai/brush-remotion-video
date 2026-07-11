// 씬 조립 — routes 데이터 로드와 타임라인 파생만 하고, 그리기는 레이어에 위임한다.
// 레이어 순서: 종이 배경 → RevealLayer(z10) → CursorLayer(z30). (연출 레이어는 다음 워크스트림에서 추가)
import React, { useEffect, useMemo, useState } from "react";
import { AbsoluteFill, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { buildDynamicStrokes } from "../lib/dynamics";
import { RoutesDataSchema, type Brush, type RoutesData, type Scene } from "../schema";
import { CursorLayer } from "./CursorLayer";
import { EffectLayer } from "./EffectLayer";
import { RevealLayer } from "./RevealLayer";
import { SubtitleLayer } from "./SubtitleLayer";
import { TitleLayer } from "./TitleLayer";

// 종이 질감 — 참조 시스템과 동일 값 (골든 파리티 전제, 임의 변경 금지)
const PAPER_TEXTURE =
  "radial-gradient(circle at 20% 16%, rgba(255,255,255,0.5), transparent 32%), radial-gradient(circle at 74% 72%, rgba(90,80,60,0.04), transparent 46%)";

export const BrushScene: React.FC<{ scene: Scene; paper: string; brush?: Brush }> = ({ scene, paper, brush }) => {
  const frame = useCurrentFrame();
  const { width: W, height: H } = useVideoConfig();
  const [data, setData] = useState<RoutesData | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [handle] = useState(() => (scene.routes ? delayRender(`routes:${scene.id}`) : null));

  useEffect(() => {
    if (!scene.routes || handle === null) return;
    let alive = true;
    fetch(staticFile(scene.routes))
      .then((r) => r.json())
      .then((json: unknown) => {
        if (alive) {
          const parsed = RoutesDataSchema.parse(json); // 로드 시점 검증 — 침묵 실패 금지
          parsed.strokes.sort((a, b) => a.start - b.start);
          setData(parsed);
        }
        continueRender(handle);
      })
      .catch((e: unknown) => {
        if (alive) setLoadError(String(e));
        continueRender(handle);
      });
    return () => {
      alive = false;
    };
  }, [scene.routes, scene.id, handle]);

  // prewash 적용 중에는 붓 드로잉 타임라인을 지연 — 워시가 사라진 뒤 빈 종이에서 다시 그린다
  const introDelayFrames =
    scene.prewashOpacity > 0.001 && scene.prewashFrames > 0 ? Math.max(0, Math.round(scene.prewashFrames)) : 0;
  const drawFrame = frame - introDelayFrames;

  const dynamic = useMemo(
    () => (data ? buildDynamicStrokes(data.strokes, data.meta.penInvisibleAfter, scene.brushDynamics) : null),
    [data, scene.brushDynamics],
  );

  if (!scene.routes || loadError) {
    return (
      <AbsoluteFill style={{ backgroundColor: paper, alignItems: "center", justifyContent: "center" }}>
        <div style={{ fontFamily: "monospace", fontSize: 28, color: "#b45a4a" }}>
          {loadError ? `routes 로드 실패: ${scene.routes} — ${loadError}` : `routes 누락: scene "${scene.id}"`}
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ backgroundColor: paper, overflow: "hidden" }}>
      <AbsoluteFill style={{ backgroundImage: PAPER_TEXTURE }} />
      {data && dynamic && (
        <>
          <RevealLayer
            scene={scene}
            image={data.meta.image}
            strokes={dynamic.strokes}
            penInvisibleAfter={dynamic.penInvisibleAfter}
            routesDuration={data.meta.durationInFrames}
            frame={frame}
            drawFrame={drawFrame}
            W={W}
            H={H}
          />
          {scene.naturalEffects && (
            <EffectLayer
              frame={frame}
              drawFrame={drawFrame}
              penInvisibleAfter={dynamic.penInvisibleAfter}
              routesDuration={data.meta.durationInFrames}
              W={W}
              H={H}
              spec={scene.naturalEffects}
            />
          )}
          <CursorLayer
            frame={frame}
            drawFrame={drawFrame}
            strokes={dynamic.strokes}
            penInvisibleAfter={dynamic.penInvisibleAfter}
            linearDraw={scene.linearDraw}
            brush={brush}
            W={W}
            H={H}
          />
        </>
      )}
      {scene.topTitle && <TitleLayer frame={frame} spec={scene.topTitle} />}
      <SubtitleLayer frame={frame} cues={scene.cues} style={scene.subtitleStyle} />
    </AbsoluteFill>
  );
};
