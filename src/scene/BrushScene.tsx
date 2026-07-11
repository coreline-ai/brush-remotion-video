// 씬 조립 컴포넌트 — Phase 2에서 Reveal·Cursor 레이어가 여기에 조립된다.
// 이 파일은 조립만 담당하고 로직을 갖지 않는다.
import React from "react";
import { AbsoluteFill } from "remotion";

export const BrushScene: React.FC<{ paper: string }> = ({ paper }) => {
  return <AbsoluteFill style={{ backgroundColor: paper }} />;
};
