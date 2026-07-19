# Continuity QA (요약)

**전문:** [`docs/seamless-short-video/08-qa-and-gates.md`](../../../docs/seamless-short-video/08-qa-and-gates.md)  
**인쇄용:** [`docs/seamless-short-video/references/qa-checklist-full.md`](../../../docs/seamless-short-video/references/qa-checklist-full.md)

## Hard

- start sha == prev handoff  
- duration / aspect  
- handoff blur  
- frame0 \|ΔY\| ≤ 4, MAE ≤ 8  

## Soft

얼굴·의상·포즈·방향·배경·카메라·변형·보행 위상·노출 체감  

## CLI

```bash
python3 bin/seamless-short.py verify --project-dir <dir>
```
