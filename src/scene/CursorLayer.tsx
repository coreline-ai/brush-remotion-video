// 붓 커서: 지금 그려지고 있는 스트로크의 선두를 따라간다.
// 선을 실제로 드러내는 순간에만 보이고(이동/퇴장 모션 없음), brush 이미지가 없으면 커서를 그리지 않는다.
import React from "react";
import { staticFile } from "remotion";
import { sharedProgress } from "../lib/easing";
import { pointOnPolyline, type Point } from "../lib/geometry";
import type { Brush, Stroke } from "../schema";

export type PenPose = { x: number; y: number; angle: number };

export function getPenPose(drawFrame: number, strokes: Stroke[], penOff: number, linear = false): PenPose | null {
  if (!strokes.length || drawFrame >= penOff) return null;
  for (const s of strokes) {
    if (drawFrame >= s.start && drawFrame <= s.end) {
      const p = sharedProgress(drawFrame, s.start, s.end, linear);
      return pointOnPolyline(s.points as Point[], p);
    }
  }
  return null;
}

type Props = {
  frame: number; // 절대 프레임 — 미세 흔들림(wobble)용
  drawFrame: number;
  strokes: Stroke[];
  penInvisibleAfter: number;
  linearDraw: boolean;
  brush?: Brush;
  W: number;
  H: number;
};

export const CursorLayer: React.FC<Props> = ({ frame, drawFrame, strokes, penInvisibleAfter, linearDraw, brush, W, H }) => {
  if (!brush || brush.visible === false || brush.opacity === 0) return null;
  const pose = getPenPose(drawFrame, strokes, penInvisibleAfter, linearDraw);
  if (!pose) return null;

  const layerStyle: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    zIndex: 30,
    pointerEvents: "none",
    opacity: brush.opacity,
    filter: "drop-shadow(0 10px 14px rgba(0,0,0,0.12))",
  };

  // 내장 벡터 펜 — 펜촉이 원점(그리는 지점), 펜대는 우상향. 펜 전용 회전 상수(붓보다 절제된 기울기).
  if (brush.kind === "pen") {
    const scale = (brush.w ?? 140) / 180;
    const rot = Math.max(-34, Math.min(30, pose.angle * 0.18 - 6)) + Math.sin(frame * 0.42) * 0.7;
    return (
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={layerStyle}>
        <g transform={`translate(${pose.x} ${pose.y}) rotate(${rot}) scale(${scale})`}>
          <path d="M-12 -26 L-138 -152" stroke="rgba(0,0,0,0.16)" strokeWidth="16" strokeLinecap="round" transform="translate(4 6)" />
          <path d="M-12 -26 L-136 -150" stroke="#1c1c1c" strokeWidth="14" strokeLinecap="round" />
          <path d="M-14 -28 L-134 -148" stroke="#3a6df0" strokeWidth="4.5" strokeLinecap="round" opacity="0.85" />
          <circle cx="-136" cy="-150" r="9" fill="#1c1c1c" />
          <circle cx="-136" cy="-150" r="4" fill="#3a6df0" opacity="0.9" />
          <path d="M0 0 L-26 -8 L-8 -26 Z" fill="#1c1c1c" />
          <path d="M0 0 L-13 -4 L-4 -13 Z" fill="#4a4a4a" />
          <path d="M-80 -60 L-118 -98" stroke="#9a9a9a" strokeWidth="4" strokeLinecap="round" />
        </g>
      </svg>
    );
  }

  // 이미지 커서(붓 등): 붓끝(tipx,tipy)을 그리는 지점에 앵커, +180도 회전 보정.
  const rot = Math.max(-52, Math.min(44, pose.angle * 0.24 - 8)) + Math.sin(frame * 0.42) * 0.9;
  if (brush.src == null) return null; // 스키마 refine이 보증하지만 안전망

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={layerStyle}>
      <g transform={`translate(${pose.x} ${pose.y}) rotate(${rot + 180})`}>
        <image
          href={staticFile(brush.src)}
          x={-(brush.tipx ?? 0)}
          y={-(brush.tipy ?? 0)}
          width={brush.w}
          height={brush.h}
          preserveAspectRatio="xMinYMin meet"
        />
      </g>
    </svg>
  );
};
