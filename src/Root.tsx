// 컴포지션 등록부 — 등록 외의 로직을 두지 않는다.
import React from "react";
import { type CalculateMetadataFunction, Composition } from "remotion";
import { FPS, RenderPropsSchema, type RenderProps } from "./schema";
import { BrushScene } from "./scene/BrushScene";

// 멀티씬 SceneSequence는 다음 워크스트림(연출 레이어)에서 추가된다. 지금은 첫 씬만 렌더.
const MainVideo: React.FC<RenderProps> = (props) => {
  return <BrushScene scene={props.scenes[0]} paper={props.paper} brush={props.brush} />;
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
