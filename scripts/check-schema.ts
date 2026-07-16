// 파일을 덮어쓰지 않고 Zod 원본과 export된 JSON Schema의 byte 정합을 검사한다.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { toJSONSchema } from "zod";
import { RenderPropsSchema } from "../src/schema";

const outFile = join(dirname(fileURLToPath(import.meta.url)), "..", "schema", "render-props.schema.json");
const expected = JSON.stringify(toJSONSchema(RenderPropsSchema, { io: "input" }), null, 2) + "\n";
const actual = readFileSync(outFile, "utf8");
if (actual !== expected) {
  throw new Error("render-props.schema.json 드리프트 — `npm run export-schema`를 실행하세요.");
}
console.log("schema sync PASS");
