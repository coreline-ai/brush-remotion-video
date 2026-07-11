// Zod 스키마 v1 — 이 파일이 render-props의 유일한 진실이다.
// 기본값(faint 0.6 등)도 여기에서만 정의한다. 컴포넌트는 parse된 값을 그대로 소비한다.
// JSON Schema(schema/render-props.schema.json)는 scripts/export-schema.ts로 여기서 내보내며,
// 파이썬 파이프라인은 그 산출물을 소비만 한다 (이중 정의 금지).
import { z } from "zod";

export const SCHEMA_VERSION = 1;
export const FPS = 30;

const frame = z.number().int().min(0);
// routes의 스트로크 타이밍은 소수 프레임(예: 8.07)이다 — 실측(winter-snow-pine-demo) 기준. int 금지.
const fractionalFrame = z.number().min(0);

// ---------- routes JSON (참조 시스템과 포맷 호환 — 골든 샘플 재사용을 위해) ----------

export const StrokeSchema = z.object({
  id: z.string(),
  kind: z.string(), // "contour" | "seal" 등 — 렌더는 구분하지 않으므로 열어둔다
  width: z.number().positive(),
  start: fractionalFrame,
  end: fractionalFrame,
  points: z.array(z.tuple([z.number(), z.number()])).min(1),
});

export const RoutesMetaSchema = z
  .object({
    image: z.string(), // public/ 기준 상대경로 (staticFile 규약)
    width: z.number().positive(),
    height: z.number().positive(),
    fps: z.number().positive(),
    durationInFrames: fractionalFrame,
    drawStart: fractionalFrame,
    drawEnd: fractionalFrame,
    penInvisibleAfter: fractionalFrame,
    routeCount: z.number().int().min(0),
  })
  .passthrough(); // coverage 등 부가 메타는 통과

export const RoutesDataSchema = z.object({
  meta: RoutesMetaSchema,
  strokes: z.array(StrokeSchema),
});

// ---------- 씬 구성 요소 ----------

export const CueSchema = z.object({
  text: z.string().min(1),
  from: frame,
  to: frame,
});

export const BrushSchema = z.object({
  src: z.string(), // 붓 커서 PNG (public/ 기준 상대경로)
  w: z.number().positive(),
  h: z.number().positive(),
  tipx: z.number(), // 붓끝 픽셀 좌표 (디스플레이 px)
  tipy: z.number(),
  visible: z.boolean().default(true),
  opacity: z.number().min(0).max(1).default(1),
});

export const BrushDynamicsSchema = z.object({
  drawSpeedScale: z.number().positive().default(1), // >1이면 더 천천히 그림 (1.12~1.18 권장)
  touchScale: z.number().positive().default(1), // stroke width 배율
  touchJitter: z.number().min(0).default(0), // width 랜덤 편차 (0.18 = ±18%)
  pathJitter: z.number().min(0).default(0), // path 흔들림(px)
  randomizeOrder: z.boolean().default(false),
  randomReverse: z.boolean().default(false),
  seed: z.number().int().default(1),
});

export const TopTitleSchema = z.object({
  kicker: z.string().optional(),
  lines: z.array(z.string().min(1)).min(1),
  x: z.number().optional(),
  y: z.number().optional(),
  width: z.number().optional(),
  align: z.enum(["left", "center", "right"]).default("left"),
  enterAt: frame.default(0),
  accent: z.string().optional(),
  firstWordColor: z.string().optional(), // 배경에서 추출한 인상색
  fontSize: z.number().optional(),
  kickerFontSize: z.number().optional(),
  wash: z.boolean().default(false),
});

export const SubtitleStyleSchema = z.object({
  bottom: z.number().optional(),
  fontSize: z.number().optional(),
  maxWidth: z.number().optional(),
  paddingX: z.number().optional(),
  paddingY: z.number().optional(),
  color: z.string().optional(),
  highlightColor: z.string().optional(),
  background: z.string().optional(),
  border: z.string().optional(),
});

export const NaturalEffectsSchema = z.object({
  kind: z.enum(["mist", "forestDust", "streamSparkle", "meadowWind", "sunsetGlow", "starTwinkle"]),
  opacity: z.number().min(0).max(1).default(0.05),
  parallaxScale: z.number().default(1),
  seed: z.number().int().default(1),
  endFadeOpacity: z.number().min(0).max(1).optional(),
});

// ---------- 위젯 (단일 registry 핵심 15종 — strict union: 타입별 필드 혼입은 parse 거부) ----------

const widgetBase = {
  x: z.number(),
  y: z.number(),
  w: z.number().positive(),
  h: z.number().positive(),
  enterAt: frame.default(0),
  title: z.string().min(1),
  kicker: z.string().optional(),
  caption: z.string().optional(),
  accent: z.string().optional(),
};

export const WidgetItemSchema = z.object({
  label: z.string(),
  detail: z.string().optional(),
  value: z.union([z.string(), z.number()]).optional(),
  tone: z.enum(["ok", "warn", "danger"]).optional(),
});
const items = z.array(WidgetItemSchema).default([]);

// 카드형 공통 스펙을 쓰는 카탈로그 타입 (실사용 빈도 상위 11종)
export const CARD_WIDGET_TYPES = [
  "FlowDiagram", "TimelineStepper", "DataTable", "ProcessStepCard", "WarningCard",
  "PersonAvatar", "ChatBubble", "CompareBars", "BulletList", "QuoteText", "Headline",
] as const;

export const WidgetSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("stat"), ...widgetBase, value: z.union([z.string(), z.number()]), sub: z.string().optional() }).strict(),
  z.object({ type: z.literal("text"), ...widgetBase, lines: z.array(z.string().min(1)).min(1) }).strict(),
  z.object({ type: z.literal("donut"), ...widgetBase, pct: z.number().min(0).max(100) }).strict(),
  z.object({ type: z.literal("bars"), ...widgetBase, values: z.array(z.number().min(0)).min(1) }).strict(),
  ...CARD_WIDGET_TYPES.map((t) => z.object({ type: z.literal(t), ...widgetBase, items }).strict()),
]);

// ---------- 씬 ----------

export const SceneSchema = z.object({
  id: z.string().min(1),
  routes: z.string().optional(), // routes JSON 경로 (public/ 기준). 없으면 렌더가 명시적 에러 표시
  durationInFrames: z.number().int().positive(),

  // 리빌 튜닝 — 기본값은 참조 시스템의 튜닝 결과를 채택
  faint: z.number().min(0).max(1).default(0.6), // 그리는 중 스트로크 레이어 불투명도
  edgeFeather: z.number().min(0).default(0), // 리빌 가장자리 blur(px). 0=하드
  linearDraw: z.boolean().default(false), // true면 이징 없이 등속 드로잉
  developFrames: frame.optional(), // 미지정 시 penInvisibleAfter→duration 구간 사용

  // prewash (씬 시작 시 흐린 원본 예고)
  prewashOpacity: z.number().min(0).max(1).default(0),
  prewashFrames: frame.default(0),
  prewashHoldFrames: frame.default(6),
  prewashBlur: z.number().min(0).default(12),

  // outro (씬 끝 종이 dissolve)
  outroFadeFrames: frame.default(0), // 0이면 비활성
  outroWashOpacity: z.number().min(0).max(1).default(0.88),
  outroBlur: z.number().min(0).default(0),

  brushDynamics: BrushDynamicsSchema.optional(),
  cues: z.array(CueSchema).default([]),
  topTitle: TopTitleSchema.optional(),
  subtitleStyle: SubtitleStyleSchema.optional(),
  naturalEffects: NaturalEffectsSchema.optional(),
  widgets: z.array(WidgetSchema).default([]),
});

// ---------- 프로젝트 전체 (render-props) ----------

export const RenderPropsSchema = z.object({
  schemaVersion: z.literal(SCHEMA_VERSION),
  projectId: z.string().min(1),
  title: z.string().optional(),
  format: z.enum(["youtube", "shorts"]).default("youtube"),
  audio: z.string().nullable().default(null), // null = 영상만 렌더 (이후 mux)
  paper: z.string().default("#fbfaf6"),
  brush: BrushSchema.optional(),
  scenes: z.array(SceneSchema).min(1),
});

export type Stroke = z.infer<typeof StrokeSchema>;
export type RoutesData = z.infer<typeof RoutesDataSchema>;
export type Cue = z.infer<typeof CueSchema>;
export type Brush = z.infer<typeof BrushSchema>;
export type BrushDynamics = z.infer<typeof BrushDynamicsSchema>;
export type TopTitle = z.infer<typeof TopTitleSchema>;
export type SubtitleStyle = z.infer<typeof SubtitleStyleSchema>;
export type NaturalEffects = z.infer<typeof NaturalEffectsSchema>;
export type Scene = z.infer<typeof SceneSchema>;
export type RenderProps = z.infer<typeof RenderPropsSchema>;
export type Widget = z.infer<typeof WidgetSchema>;
export type WidgetItem = z.infer<typeof WidgetItemSchema>;
export type CardWidget = Extract<Widget, { items: WidgetItem[] }>;
