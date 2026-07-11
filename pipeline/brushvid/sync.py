"""sync.py — 내레이션 동기 드로잉: 존(드로잉 순서)을 cue 구간에 배분하고 스트로크를 리타이밍.

- 자동 배분: 존 잉크 질량 누적이 cue 길이 비례 쿼터를 채우면 다음 cue 로 넘어가는
  순차 배분 (이미 찬 쿼터는 건너뜀 → 존 < cue 여도 뒤쪽 cue 에 분산)
- sync-map(data/{pid}/sync-map.json) 이 있으면 자동 배분 대신 사용 (zone→cue 수동/Claude 매핑)
- 리타이밍: 존 스트로크들을 배정 cue 구간(앞 10%는 펜 이동 여유) 안으로 선형 재배분.
  같은 cue 에 존 여러 개면 질량 비례로 구간을 순차 분할. 존 간 무스트로크 구간에서 펜은 자연 소실.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

LEAD_FRAC = 0.10  # cue 구간 앞 여유 (펜 이동)


def allocate_zones_to_cues(zone_masses: list[float], cue_lengths: list[float]) -> list[int]:
    """존(드로잉 순서)별 배정 cue 인덱스. 단조 증가, 모든 존 배정.

    cue 별 질량 쿼터 = 총 질량 × cue 길이 비례. 누적 질량이 누적 쿼터를 넘으면
    다음 cue 로 진행하며, 이미 채워진 쿼터는 건너뛴다.
    """
    if not zone_masses:
        return []
    if not cue_lengths:
        raise ValueError("cue 가 없음 — 배분 불가 (호출 전 확인)")
    total_mass = sum(zone_masses) or 1.0
    total_len = sum(cue_lengths) or 1.0
    cum_quota = []
    acc_q = 0.0
    for ln in cue_lengths:
        acc_q += total_mass * ln / total_len
        cum_quota.append(acc_q)

    out: list[int] = []
    acc = 0.0
    cue = 0
    n = len(cue_lengths)
    for m in zone_masses:
        while cue < n - 1 and acc >= cum_quota[cue] - 1e-9:
            cue += 1
        out.append(cue)
        acc += m
    return out


def _zone_windows(zones: list[dict], cues: list[dict], assignment: list[int],
                  lead_frac: float) -> list[tuple[float, float]]:
    """존별 리타이밍 창 [w0, w1] (프레임). 같은 cue 의 존들은 질량 비례 순차 분할."""
    windows: list[tuple[float, float]] = [None] * len(zones)  # type: ignore[list-item]
    for ci in sorted(set(assignment)):
        idxs = [i for i, a in enumerate(assignment) if a == ci]
        f0, f1 = float(cues[ci]["from"]), float(cues[ci]["to"])
        span = f1 - f0
        w0 = f0 + span * lead_frac
        usable = f1 - w0
        masses = [max(1.0, float(zones[i]["inkPixels"])) for i in idxs]
        total = sum(masses)
        t = w0
        for i, m in zip(idxs, masses):
            w = usable * m / total
            windows[i] = (t, t + w)
            t += w
    return windows


def apply_sync(routes_data: dict, zones: list[dict], cues: list[dict], *,
               sync_map: dict | None = None, lead_frac: float = LEAD_FRAC) -> dict:
    """routes {meta, strokes} 를 cue 동기 리타이밍한 새 dict 로 반환 (원본 불변).

    zones: routes 산출의 드로잉 순서 존 정보([{zone, inkPixels, ...}]).
    cues: 씬-로컬 [{from, to, ...}]. sync_map: {"zoneToCue": {"0": 0, ...}} (자동 배분 대신).
    cue 가 없으면 경고 후 원본 그대로 반환 (자동 off).
    """
    import copy
    if not cues:
        log.warning("sync: cue 0개 — 동기 배분 생략 (원본 유지)")
        return routes_data
    if not zones:
        log.warning("sync: 존 정보 없음 — 동기 배분 생략 (원본 유지)")
        return routes_data

    n_cues = len(cues)
    if sync_map is not None:
        mapping = {int(k): int(v) for k, v in (sync_map.get("zoneToCue") or {}).items()}
        for z, c in mapping.items():
            if not (0 <= c < n_cues):
                raise ValueError(f"sync-map: zone {z} → cue {c} 가 범위 밖 (cue {n_cues}개)")
        auto = allocate_zones_to_cues([max(1.0, float(z["inkPixels"])) for z in zones],
                                      [c["to"] - c["from"] for c in cues])
        assignment = [mapping.get(z["zone"], auto[i]) for i, z in enumerate(zones)]
        log.info("sync: sync-map 사용 (%d/%d 존 수동 매핑, 나머지 자동)", len(mapping), len(zones))
    else:
        assignment = allocate_zones_to_cues([max(1.0, float(z["inkPixels"])) for z in zones],
                                            [c["to"] - c["from"] for c in cues])

    windows = _zone_windows(zones, cues, assignment, lead_frac)

    data = copy.deepcopy(routes_data)
    strokes = data["strokes"]
    for zi, zone in enumerate(zones):
        zs = [s for s in strokes if s.get("zone") == zone["zone"]]
        if not zs:
            continue
        w0, w1 = windows[zi]
        s0 = min(s["start"] for s in zs)
        s1 = max(s["end"] for s in zs)
        span = max(1e-6, s1 - s0)
        scale = (w1 - w0) / span
        for s in zs:
            s["start"] = round(w0 + (s["start"] - s0) * scale, 2)
            s["end"] = round(w0 + (s["end"] - s0) * scale, 2)

    last_end = max((s["end"] for s in strokes), default=data["meta"]["drawEnd"])
    data["meta"]["drawEnd"] = round(last_end, 2)
    data["meta"]["penInvisibleAfter"] = round(last_end + 8, 2)
    data["meta"]["sync"] = "map" if sync_map is not None else "auto"
    data["meta"]["zoneCueAssignment"] = assignment
    return data
