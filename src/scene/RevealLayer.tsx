// 2단계 수묵화 리빌: ① 붓이 지나간 자리만 배경을 연하게(faint) 드러내고
// ② 완성 후 전체가 또렷하게 발현(develop)된다. prewash(인트로 예고)와 outro(종이 dissolve)도 담당.
// 수식·구조는 참조 시스템의 튜닝 결과를 채택 — 임의 변경 시 골든 diff가 깨진다.
import React, { useId } from "react";
import { AbsoluteFill, interpolate, staticFile } from "remotion";
import { clamp, easeDevelop, sharedProgress } from "../lib/easing";
import { toPath, type Point } from "../lib/geometry";
import type { Scene, Stroke } from "../schema";

type Props = {
  scene: Scene;
  image: string; // 배경 그림 (public/ 기준 상대경로, routes meta.image)
  strokes: Stroke[]; // brushDynamics 적용 후
  penInvisibleAfter: number;
  routesDuration: number; // routes meta.durationInFrames
  frame: number;
  drawFrame: number; // frame - introDelay (prewash 동안 드로잉 지연)
  W: number;
  H: number;
};

export const RevealLayer: React.FC<Props> = ({ scene, image, strokes, penInvisibleAfter, routesDuration, frame, drawFrame, W, H }) => {
  const patId = `brushpat-${useId().replace(/[:]/g, "")}`;
  const introDelayFrames = frame - drawFrame;

  const prewashAlpha = introDelayFrames > 0
    ? interpolate(
        frame,
        [0, Math.min(scene.prewashHoldFrames, introDelayFrames), introDelayFrames],
        [scene.prewashOpacity, scene.prewashOpacity, 0],
        clamp,
      )
    : 0;

  // develop: 모든 획이 끝난 뒤(penInvisibleAfter) 전체 원본을 또렷하게 페이드 인
  const dStart = penInvisibleAfter;
  const dEnd = scene.developFrames != null ? dStart + scene.developFrames : routesDuration - 4;
  const developOpacity = interpolate(drawFrame, [dStart, dEnd], [0, 1], easeDevelop);

  const outroFrames = Math.max(0, Math.round(scene.outroFadeFrames));
  const outroAlpha = outroFrames > 0
    ? interpolate(frame, [Math.max(0, scene.durationInFrames - outroFrames), scene.durationInFrames], [0, 1], easeDevelop)
    : 0;

  const { faint, edgeFeather, linearDraw } = scene;

  const strokePaths = (stroke: "mask" | "pattern") =>
    strokes.map((s) => (
      <path
        key={s.id}
        d={toPath(s.points as Point[])}
        fill="none"
        stroke={stroke === "mask" ? "#fff" : `url(#${patId})`}
        strokeWidth={s.width}
        strokeLinecap="round"
        strokeLinejoin="round"
        pathLength={1}
        strokeDasharray={1}
        strokeDashoffset={1 - sharedProgress(drawFrame, s.start, s.end, linearDraw)}
        opacity={drawFrame < s.start ? 0 : 1}
      />
    ));

  return (
    <>
      {/* 단일 SVG: 이미지 패턴을 한 번만 디코드해 prewash·faint 리빌·develop이 공유 */}
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ position: "absolute", inset: 0, zIndex: 10, pointerEvents: "none" }}>
        <defs>
          <pattern id={patId} patternUnits="userSpaceOnUse" x="0" y="0" width={W} height={H}>
            <image href={staticFile(image)} x="0" y="0" width={W} height={H} preserveAspectRatio="none" />
          </pattern>
          {prewashAlpha > 0.001 && scene.prewashBlur > 0 && (
            <filter id={`pw-${patId}`} x="-8%" y="-8%" width="116%" height="116%">
              <feGaussianBlur stdDeviation={scene.prewashBlur} />
            </filter>
          )}
          {/* edgeFeather: 스트로크를 흰색 마스크로 그리고 마스크에만 블러 —
              이미지 내용은 선명 유지, 리빌 "가장자리만" 붓 질감처럼 부드럽게 */}
          {edgeFeather > 0 && developOpacity < 0.92 && (
            <mask id={`fm-${patId}`} maskUnits="userSpaceOnUse" x="0" y="0" width={W} height={H}>
              <g filter={`url(#fb-${patId})`}>{strokePaths("mask")}</g>
            </mask>
          )}
          {edgeFeather > 0 && (
            <filter id={`fb-${patId}`} x="-8%" y="-8%" width="116%" height="116%">
              <feGaussianBlur stdDeviation={edgeFeather} />
            </filter>
          )}
        </defs>

        {/* prewash: 씬 시작에만 흐린 전체 화면을 잠깐 보여준 뒤 사라짐 (첫 화면 공백 방지) */}
        {prewashAlpha > 0.001 && (
          <rect x="0" y="0" width={W} height={H} fill={`url(#${patId})`} opacity={prewashAlpha}
            filter={scene.prewashBlur > 0 ? `url(#pw-${patId})` : undefined} />
        )}

        {/* 1단계 faint 리빌 — develop≥0.92면 전체 rect가 덮으므로 생략(렌더 부하↓) */}
        {developOpacity < 0.92 && (
          edgeFeather > 0 ? (
            <rect x="0" y="0" width={W} height={H} fill={`url(#${patId})`} mask={`url(#fm-${patId})`} opacity={faint} />
          ) : (
            <g opacity={faint}>{strokePaths("pattern")}</g>
          )
        )}

        {/* 2단계 develop — 전체 이미지가 또렷하게 발현 */}
        {developOpacity > 0.001 && (
          <rect x="0" y="0" width={W} height={H} fill={`url(#${patId})`} opacity={developOpacity} />
        )}
      </svg>

      {/* outro: 씬 끝 종이 dissolve */}
      {outroAlpha > 0.001 && (
        <AbsoluteFill
          style={{
            zIndex: 80,
            pointerEvents: "none",
            opacity: Math.min(1, Math.max(0, outroAlpha * scene.outroWashOpacity)),
            background:
              "radial-gradient(circle at 22% 18%, rgba(255,255,255,0.90), rgba(251,250,246,0.72) 36%, transparent 62%), linear-gradient(180deg, rgba(255,255,253,0.96), rgba(248,245,237,0.98))",
            backdropFilter: scene.outroBlur > 0 ? `blur(${scene.outroBlur}px)` : undefined,
          }}
        />
      )}
    </>
  );
};
