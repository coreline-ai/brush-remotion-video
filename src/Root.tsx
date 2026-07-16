// 컴포지션 등록부 — 등록 외의 로직을 두지 않는다.
import React from "react";
import { type CalculateMetadataFunction, Composition } from "remotion";
import { FPS, RenderPropsSchema, type RenderProps } from "./schema";
import {
  FullColorMotionSequence,
  type FullColorMotionProps,
} from "./scene/FullColorMotionSequence";
import { SceneSequence } from "./scene/SceneSequence";

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

const motionDefaultProps: FullColorMotionProps = {
  projectId: "motion-placeholder",
  scenes: [
    {
      id: "scene-01",
      image: "images/scene-01.png",
      durationInFrames: 300,
      camera: "push-in",
      effect: "rays",
    },
  ],
};

const calculateMotionMetadata: CalculateMetadataFunction<FullColorMotionProps> = ({ props }) => ({
  props,
  durationInFrames: props.scenes.reduce((sum, scene) => sum + scene.durationInFrames, 0),
  fps: FPS,
});

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BrushLandscape"
        component={SceneSequence}
        width={1920}
        height={1080}
        fps={FPS}
        durationInFrames={90}
        schema={RenderPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="BrushLandscape4K"
        component={SceneSequence}
        width={3840}
        height={2160}
        fps={FPS}
        durationInFrames={90}
        schema={RenderPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="BrushPortrait"
        component={SceneSequence}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={90}
        schema={RenderPropsSchema}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
      <Composition
        id="FullColorMotionLandscape"
        component={FullColorMotionSequence}
        width={1920}
        height={1080}
        fps={FPS}
        durationInFrames={300}
        defaultProps={motionDefaultProps}
        calculateMetadata={calculateMotionMetadata}
      />
    </>
  );
};
