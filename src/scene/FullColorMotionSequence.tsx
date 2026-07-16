import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";

export type MotionCamera =
  | "push-in"
  | "push-out"
  | "pan-left"
  | "pan-right"
  | "rise"
  | "fall"
  | "arc-left"
  | "arc-right";

export type MotionEffect =
  | "none"
  | "rays"
  | "mist"
  | "birds"
  | "stars"
  | "storm"
  | "sparkles"
  | "lanterns"
  | "fireflies"
  | "ripples"
  | "aurora"
  | "trail";

export type FullColorMotionScene = {
  id: string;
  image: string;
  durationInFrames: number;
  camera: MotionCamera;
  effect: MotionEffect;
  intensity?: number;
};

export type FullColorMotionProps = {
  projectId: string;
  scenes: FullColorMotionScene[];
};

const TRANSITION_FRAMES = 12;
const clampProgress = (frame: number, duration: number) =>
  interpolate(frame, [0, Math.max(duration - 1, 1)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const cameraTransform = (camera: MotionCamera, progress: number) => {
  const eased = Easing.inOut(Easing.cubic)(progress);
  const gentleWave = Math.sin(progress * Math.PI) * 12;
  let scale = 1.03;
  let x = 0;
  let y = 0;

  switch (camera) {
    case "push-in":
      scale = 1.03 + eased * 0.12;
      break;
    case "push-out":
      scale = 1.15 - eased * 0.12;
      break;
    case "pan-left":
      scale = 1.1;
      x = 56 - eased * 112;
      y = gentleWave * 0.35;
      break;
    case "pan-right":
      scale = 1.1;
      x = -56 + eased * 112;
      y = -gentleWave * 0.35;
      break;
    case "rise":
      scale = 1.1;
      y = 42 - eased * 92;
      break;
    case "fall":
      scale = 1.1;
      y = -42 + eased * 92;
      break;
    case "arc-left":
      scale = 1.1;
      x = 46 - eased * 92;
      y = -28 + Math.sin(progress * Math.PI) * 54;
      break;
    case "arc-right":
      scale = 1.1;
      x = -46 + eased * 92;
      y = -28 + Math.sin(progress * Math.PI) * 54;
      break;
  }

  return `translate(${x}px, ${y}px) scale(${scale})`;
};

const Rays: React.FC<{ time: number; intensity: number }> = ({ time, intensity }) => (
  <AbsoluteFill
    style={{
      opacity: 0.1 + Math.sin(time * 0.65) * 0.035 + intensity * 0.035,
      background:
        "conic-gradient(from 214deg at 34% 48%, transparent 0deg, rgba(255,223,151,0.42) 9deg, transparent 18deg, transparent 46deg, rgba(255,209,121,0.25) 57deg, transparent 68deg, transparent 105deg, rgba(255,234,179,0.3) 117deg, transparent 133deg)",
      mixBlendMode: "screen",
      transform: `scale(1.1) rotate(${time * 0.4}deg)`,
    }}
  />
);

const Mist: React.FC<{ time: number; intensity: number }> = ({ time, intensity }) => (
  <AbsoluteFill style={{ opacity: 0.14 + intensity * 0.05, filter: "blur(28px)" }}>
    {[0, 1, 2, 3].map((i) => {
      const drift = ((time * (8 + i * 1.3) + i * 29) % 150) - 35;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${drift}%`,
            top: `${57 + i * 10}%`,
            width: `${72 + i * 14}%`,
            height: "25%",
            borderRadius: "50%",
            background: "rgba(227,231,255,0.42)",
          }}
        />
      );
    })}
  </AbsoluteFill>
);

const Birds: React.FC<{ time: number }> = ({ time }) => (
  <AbsoluteFill style={{ opacity: 0.7 }}>
    {[0, 1, 2, 3, 4].map((i) => {
      const x = ((time * (7 + i) + i * 21) % 125) - 12;
      const y = 20 + ((i * 13 + time * 1.5) % 19);
      const wing = 4 + Math.sin(time * 8 + i) * 2;
      return (
        <svg
          key={i}
          viewBox="0 0 32 16"
          style={{
            position: "absolute",
            width: 32 + i * 3,
            height: 16 + i,
            left: `${x}%`,
            top: `${y}%`,
            transform: `rotate(${Math.sin(time + i) * 8}deg)`,
          }}
        >
          <path
            d={`M 1 10 Q 8 ${10 - wing} 16 10 Q 24 ${10 - wing} 31 10`}
            fill="none"
            stroke="rgba(31,23,48,0.78)"
            strokeWidth="2.2"
            strokeLinecap="round"
          />
        </svg>
      );
    })}
  </AbsoluteFill>
);

const Stars: React.FC<{ time: number; warm?: boolean }> = ({ time, warm = false }) => (
  <AbsoluteFill>
    {Array.from({ length: 42 }, (_, i) => {
      const left = (i * 37 + 11) % 100;
      const top = (i * 19 + 7) % 74;
      const pulse = 0.22 + ((Math.sin(time * (1.4 + (i % 5) * 0.25) + i) + 1) / 2) * 0.72;
      const size = 1.5 + (i % 4) * 0.7;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${left}%`,
            top: `${top}%`,
            width: size,
            height: size,
            borderRadius: "50%",
            opacity: pulse,
            background: warm ? "#ffe6a1" : "#eff4ff",
            boxShadow: `0 0 ${size * 3}px ${warm ? "#ffbd56" : "#a6c8ff"}`,
          }}
        />
      );
    })}
  </AbsoluteFill>
);

const Storm: React.FC<{ time: number }> = ({ time }) => {
  const lightning = Math.max(0, Math.sin(time * 2.1 - 0.7)) ** 28;
  return (
    <AbsoluteFill>
      <AbsoluteFill
        style={{
          opacity: 0.2 + Math.sin(time * 0.6) * 0.05,
          background: "linear-gradient(135deg, rgba(19,14,53,0.52), transparent 58%, rgba(89,41,125,0.22))",
          mixBlendMode: "multiply",
        }}
      />
      <AbsoluteFill
        style={{
          opacity: lightning * 0.23,
          background: "linear-gradient(120deg, transparent 45%, rgba(229,223,255,0.74) 49%, transparent 54%)",
          mixBlendMode: "screen",
        }}
      />
    </AbsoluteFill>
  );
};

const RisingLights: React.FC<{
  time: number;
  color: string;
  count: number;
  size: number;
}> = ({ time, color, count, size }) => (
  <AbsoluteFill>
    {Array.from({ length: count }, (_, i) => {
      const left = (i * 29 + 6) % 96;
      const travel = (time * (3.4 + (i % 4) * 0.55) + i * 7) % 112;
      const top = 110 - travel;
      const wobble = Math.sin(time * 1.7 + i) * 1.4;
      const dotSize = size + (i % 3) * 1.4;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: `${left + wobble}%`,
            top: `${top}%`,
            width: dotSize,
            height: dotSize * 1.35,
            borderRadius: "50% 50% 45% 45%",
            opacity: 0.38 + (i % 4) * 0.11,
            background: color,
            boxShadow: `0 0 ${dotSize * 4}px ${color}`,
          }}
        />
      );
    })}
  </AbsoluteFill>
);

const Ripples: React.FC<{ time: number }> = ({ time }) => (
  <AbsoluteFill style={{ overflow: "hidden", opacity: 0.43 }}>
    {[0, 1, 2].map((i) => {
      const phase = (time * 0.18 + i / 3) % 1;
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: "50%",
            top: "78%",
            width: `${16 + phase * 92}%`,
            height: `${4 + phase * 20}%`,
            border: "2px solid rgba(224,239,255,0.62)",
            borderRadius: "50%",
            transform: "translate(-50%, -50%)",
            opacity: 1 - phase,
          }}
        />
      );
    })}
  </AbsoluteFill>
);

const Aurora: React.FC<{ time: number }> = ({ time }) => (
  <AbsoluteFill style={{ overflow: "hidden", opacity: 0.33, filter: "blur(22px)", mixBlendMode: "screen" }}>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        style={{
          position: "absolute",
          left: `${-22 + i * 22 + Math.sin(time * 0.45 + i) * 5}%`,
          top: `${6 + i * 11}%`,
          width: "72%",
          height: "27%",
          borderRadius: "50%",
          transform: `rotate(${-16 + i * 18 + Math.sin(time * 0.3 + i) * 5}deg)`,
          background:
            i === 1
              ? "linear-gradient(90deg, transparent, rgba(131,255,207,0.65), transparent)"
              : "linear-gradient(90deg, transparent, rgba(158,118,255,0.58), transparent)",
        }}
      />
    ))}
  </AbsoluteFill>
);

const Trail: React.FC<{ time: number }> = ({ time }) => (
  <AbsoluteFill style={{ overflow: "hidden", opacity: 0.55, mixBlendMode: "screen" }}>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        style={{
          position: "absolute",
          left: `${-42 + ((time * (12 + i * 2.4) + i * 38) % 170)}%`,
          top: `${22 + i * 18}%`,
          width: "28%",
          height: 4 + i * 2,
          borderRadius: 999,
          transform: "rotate(-20deg)",
          background: "linear-gradient(90deg, transparent, rgba(255,224,151,0.88), transparent)",
          boxShadow: "0 0 18px rgba(255,207,101,0.7)",
        }}
      />
    ))}
  </AbsoluteFill>
);

const EffectLayer: React.FC<{ effect: MotionEffect; time: number; intensity: number }> = ({
  effect,
  time,
  intensity,
}) => {
  switch (effect) {
    case "rays":
      return <Rays time={time} intensity={intensity} />;
    case "mist":
      return <Mist time={time} intensity={intensity} />;
    case "birds":
      return <Birds time={time} />;
    case "stars":
      return <Stars time={time} />;
    case "storm":
      return <Storm time={time} />;
    case "sparkles":
      return <RisingLights time={time} color="#ffe29a" count={28} size={3} />;
    case "lanterns":
      return <RisingLights time={time} color="#ffb34f" count={19} size={7} />;
    case "fireflies":
      return <RisingLights time={time} color="#e8ff8e" count={25} size={2.5} />;
    case "ripples":
      return <Ripples time={time} />;
    case "aurora":
      return <Aurora time={time} />;
    case "trail":
      return <Trail time={time} />;
    case "none":
      return null;
  }
};

const FullColorMotionScene: React.FC<{ scene: FullColorMotionScene; crossfadeIn: boolean }> = ({
  scene,
  crossfadeIn,
}) => {
  const frame = useCurrentFrame();
  const progress = clampProgress(frame, scene.durationInFrames + (crossfadeIn ? TRANSITION_FRAMES : 0));
  const opacity = crossfadeIn
    ? interpolate(frame, [0, TRANSITION_FRAMES], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : 1;
  const time = frame / 30;

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#090617", opacity }}>
      <Img
        src={staticFile(scene.image)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: cameraTransform(scene.camera, progress),
          transformOrigin: "center center",
          willChange: "transform",
        }}
      />
      <EffectLayer effect={scene.effect} time={time} intensity={scene.intensity ?? 1} />
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          background:
            "radial-gradient(ellipse at center, transparent 47%, rgba(8,4,22,0.05) 72%, rgba(8,4,22,0.28) 120%)",
        }}
      />
    </AbsoluteFill>
  );
};

export const FullColorMotionSequence: React.FC<FullColorMotionProps> = ({ scenes }) => {
  let offset = 0;
  return (
    <AbsoluteFill style={{ backgroundColor: "#090617" }}>
      {scenes.map((scene, index) => {
        const crossfadeIn = index > 0;
        const from = crossfadeIn ? offset - TRANSITION_FRAMES : offset;
        const durationInFrames = scene.durationInFrames + (crossfadeIn ? TRANSITION_FRAMES : 0);
        offset += scene.durationInFrames;
        return (
          <Sequence key={scene.id} from={from} durationInFrames={durationInFrames} premountFor={30}>
            <FullColorMotionScene scene={scene} crossfadeIn={crossfadeIn} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
