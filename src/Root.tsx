// 컴포지션 등록부 — 등록 외의 로직을 두지 않는다.
import React from "react";
import { type CalculateMetadataFunction, Composition } from "remotion";
import { FPS, RenderPropsSchema, type RenderProps } from "./schema";
import { BrushScene } from "./scene/BrushScene";

// Phase 2에서 SceneSequence로 교체된다. 지금은 paper 배경만 렌더하는 자리표시자.
const MainVideo: React.FC<RenderProps> = (props) => {
  return <BrushScene paper={props.paper} />;
};

// duration = scenes 합산. props는 여기서 parse되어 스키마 기본값이 채워진 채 컴포넌트로 전달된다.
const calculateMetadata: CalculateMetadataFunction<RenderProps> = ({ props }) => {
  const parsed = RenderPropsSchema.parse(props);
  return {
    props: parsed,
    durationInFrames: parsed.scenes.reduce((sum, s) => sum + s.durationInFrames, 0),
    fps: FPS,
  };
};

const defaultProps: RenderProps = RenderPropsSchema.parse({
  schemaVersion: 1,
  projectId: "placeholder",
  scenes: [{ id: "scene-01", durationInFrames: 90 }],
});

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BrushLandscape"
        component={MainVideo}
        width={1920}
        height={1080}
        fps={FPS}
        durationInFrames={90}
        schema={RenderPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="BrushPortrait"
        component={MainVideo}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={90}
        schema={RenderPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
    </>
  );
};
