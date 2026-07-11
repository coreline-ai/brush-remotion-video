export const motionTokens = {
  frameRate: {
    cinematic: 24,
    standard: 30,
    responsive: 60,
  },
  duration: {
    pressDown: 80,
    releasePop: 140,
    uiPopIn: 180,
    modalEnter: 240,
    modalExit: 160,
    hitFlash: 70,
    hitSpark: 140,
    hitStopLight: 40,
    hitStopHeavy: 70,
    rewardBurst: 650,
    sceneTransition: 600,
  },
  easing: {
    snappyEnter: "cubic-bezier(0.16, 1, 0.3, 1)",
    fastExit: "cubic-bezier(0.7, 0, 0.84, 0)",
    standardUi: "cubic-bezier(0.2, 0, 0, 1)",
    softUi: "cubic-bezier(0.33, 1, 0.68, 1)",
  },
  spring: {
    subtleUi: { stiffness: 260, damping: 28, mass: 1 },
    elasticUi: { stiffness: 360, damping: 20, mass: 1 },
    heavyObject: { stiffness: 180, damping: 24, mass: 1.4 },
    quickRebound: { stiffness: 520, damping: 32, mass: 0.8 },
  },
  stagger: {
    smallList: 30,
    cardReveal: 60,
    rewardItem: 90,
    dramatic: 150,
  },
  spritesheet: {
    defaultMargin: 16,
    defaultGap: 24,
    defaultPaddingInsideFrame: 16,
  },
  reducedMotion: {
    maxScale: 1.03,
    disableScreenShake: true,
    preferOpacity: true,
  },
} as const;

export type MotionTokens = typeof motionTokens;
