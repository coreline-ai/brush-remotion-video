// RenderPropsSchema → JSON Schema 내보내기.
// 파이썬 파이프라인(brushvid.props)은 이 산출물을 소비만 한다 — 스키마를 따로 정의하지 않는다.
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { zodToJsonSchema } from "zod-to-json-schema";
import { RenderPropsSchema } from "../src/schema";

const outFile = join(dirname(fileURLToPath(import.meta.url)), "..", "schema", "render-props.schema.json");
const jsonSchema = zodToJsonSchema(RenderPropsSchema, "RenderProps");

mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, JSON.stringify(jsonSchema, null, 2) + "\n");
console.log(`wrote ${outFile}`);
