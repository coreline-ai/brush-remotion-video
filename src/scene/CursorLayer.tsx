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

  // 붓끝(tipx,tipy)을 그리는 지점에 앵커, 스트로크 방향으로 살짝 기울임 + 미세 흔들림. +180도 회전 보정.
  const rot = Math.max(-52, Math.min(44, pose.angle * 0.24 - 8)) + Math.sin(frame * 0.42) * 0.9;

  return (
    <svg
      width={W}
      height={H}
      viewBox={`0 0 ${W} ${H}`}
      style={{
        position: "absolute",
        inset: 0,
        zIndex: 30,
        pointerEvents: "none",
        opacity: brush.opacity,
        filter: "drop-shadow(0 10px 14px rgba(0,0,0,0.12))",
      }}
    >
      <g transform={`translate(${pose.x} ${pose.y}) rotate(${rot + 180})`}>
        <image
          href={staticFile(brush.src)}
          x={-brush.tipx}
          y={-brush.tipy}
          width={brush.w}
          height={brush.h}
          preserveAspectRatio="xMinYMin meet"
        />
      </g>
    </svg>
  );
};
