# 배경 이미지 생성 가이드 (codex exec + gpt-image2)

brush-draw-reveal의 배경은 **사용자가 주는 게 아니라 스킬이 직접 생성**한다.
`codex exec` CLI로 `gpt-image2` 스킬(모델 `gpt-image-2`)을 호출해, 영상 주제에 맞는
**화이트 배경 손그림(잉크 라인 + 연한 수채화) 일러스트**를 프롬프팅해 만든다.

## 이 스킬이 요구하는 배경의 조건 (반드시 프롬프트에 반영)

- **깨끗한 흰/미색 종이 배경** (붓 리빌·정제가 전제로 하는 화이트 배경)
- **손그림 잉크 라인 아트 + 부드러운 파스텔 수채화 워시** (scene-01 스타일)
- **주제에 맞는 소재** (예: AI 워크플로우 → 뇌·기어·문서·화살표·노드)
- **여백 확보**: 상단(특히 좌상단 1/3)에 넉넉한 빈 공간 → 타이틀·위젯 자리
- **텍스트/글자 없음** (no text, no lettering — 자막·타이틀은 영상 레이어가 담당)
- **16:9 가로** 구도, 고해상도, 미니멀/에디토리얼 톤

## 프롬프트 템플릿 (영문 권장, {SUBJECT}만 교체)

```
A hand-drawn ink line-art sketch combined with soft, light pastel watercolor washes,
on a clean warm-white paper background. Subject: {SUBJECT}.
Loose confident pen strokes, delicate watercolor in violet / teal / amber tones,
airy editorial composition with GENEROUS EMPTY WHITE SPACE in the upper-left third
(reserved for title and widgets). Absolutely NO text, no letters, no numbers, no labels.
Minimal, elegant, high detail, 16:9 landscape.
```

## 호출 방법 — ⚠️ API 키 없음 → codex 내장 image_gen 만 사용

**✅ 실제 환경 검증(2026-07-04)**:
- `~/.codex/auth.json` → `auth_mode=chatgpt`, **OPENAI_API_KEY 없음** → 키 필요한 gpt-image2 `generate_image.py` 는 불가.
- 작동 바이너리 = **`/Applications/Codex.app/Contents/Resources/codex`** (npm/`/usr/local/bin/codex` 는 네이티브 바이너리 없어 ENOENT).
- 검증 커맨드(키 없이 성공, 1672×941 PNG 생성·복사): `codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C <dir> "<내장 image_gen 사용 + OUT 복사 지시 + 프롬프트>"`

**핵심**: `OPENAI_API_KEY` 가 없으므로 `generate_image.py --output`(=키 필요) 는 **쓰지 않는다**.
대신 **codex exec 로 codex 내장 `image_gen` 툴(imagegen 스킬 기본 모드, 키 불필요)** 을 구동.
내장 툴은 결과를 `$CODEX_HOME/generated_images/` 에 저장하므로 codex 에게 최종본을 목표 경로로 복사시킨다.

### codex exec (유일 경로)

```bash
bash <스킬>/scripts/gen-background.sh "<SUBJECT 영문 소재>" \
  <빌더>/public/<proj>/backgrounds/<proj>-title.png
```
스크립트가 내부적으로 실행하는 것:
```bash
codex exec "이미지를 생성해줘. 반드시 codex 내장 image_gen 툴(imagegen 스킬)을 사용하고 \
OPENAI_API_KEY 기반 CLI 는 쓰지 마. 가로 16:9 고품질로 만들고, 완성본을 '<OUT 절대경로>' 로 복사해줘. \
프롬프트: <위 템플릿을 {SUBJECT} 채워서>"
```
codex 가 내장 image_gen 툴로 이미지를 만들고(키 불필요) 지정 경로로 복사한다.

## 주의

- **API 키 금지 경로**: `generate_image.py`/Image API 직접 호출은 키가 필요하므로 사용하지 않는다.
  오직 codex 내장 image_gen(imagegen 스킬)만.
- 내장 image_gen 은 종횡비를 프롬프트/툴 옵션으로 정하며 결과는 `$CODEX_HOME/generated_images/`.
  16:9(가로)로 요청하고, brush 파이프라인이 최종적으로 1920×1080 으로 리사이즈한다.
- 생성 후 반드시 **눈으로 확인**: 흰 배경인지, 텍스트가 안 들어갔는지, 상단 여백이 있는지.
  조건 안 맞으면 프롬프트 보강해 재생성.
- codex 는 **사용자 환경(codex auth)** 에서 실행. 에이전트 Bash에선 codex 네이티브 바이너리가
  없을 수 있음(렌더와 동일하게 사용자 Terminal 위임).
