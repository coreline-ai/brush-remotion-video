#!/usr/bin/env python3
"""Prepare 60 sourced cosmic images for the v0.3 ten-minute production."""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples/cosmic-random-brush-v03/assets"
CACHE = ROOT / "tmp/cosmic-random-brush-v03-source"
SIZE = (1920, 1080)
USAGE = "https://www.nasa.gov/nasa-brand-center/images-and-media/"
API = "https://images-api.nasa.gov"


def spec(scene: int, slug: str, title: str, query: str, fit: str = "cover") -> dict:
    return {"scene": scene, "slug": slug, "title": title, "query": query, "fit": fit,
            "seed": 260712 + (scene - 1) * 37}


SCENES = [
    spec(1, "earth-orbit-sunrise", "01. 지구 궤도 일출", "earth orbit sunrise"),
    spec(2, "earth-at-night", "02. 밤의 지구", "earth at night from space"),
    spec(3, "aurora-from-orbit", "03. 궤도 위 오로라", "aurora from international space station"),
    spec(4, "blue-marble", "04. 푸른 구슬", "blue marble"),
    spec(5, "storm-from-space", "05. 폭풍의 눈", "hurricane eye from space earth"),
    spec(6, "sahara-from-orbit", "06. 사하라의 결", "Sahara desert from space"),
    spec(7, "himalayas-from-space", "07. 히말라야의 능선", "Himalayas from space"),
    spec(8, "city-lights", "08. 도시의 불빛", "city lights earth from space"),
    spec(9, "ocean-cloud-swirls", "09. 구름의 소용돌이", "earth cloud patterns ISS"),
    spec(10, "earthrise", "10. 달 너머 지구", "Earthrise", "contain-dark"),
    spec(11, "lunar-tranquility", "11. 고요의 바다", "Apollo lunar surface horizon"),
    spec(12, "copernicus-crater", "12. 코페르니쿠스 크레이터", "Copernicus crater moon"),
    spec(13, "lunar-far-side", "13. 달의 뒷면", "lunar far side moon"),
    spec(14, "apollo-earthrise", "14. 아폴로의 지구돋이", "Apollo Earthrise moon", "contain-dark"),
    spec(15, "mars-horizon", "15. 화성의 지평선", "Mars horizon Curiosity rover"),
    spec(16, "mars-dunes", "16. 화성의 모래언덕", "Mars dunes"),
    spec(17, "valles-marineris", "17. 마리너 계곡", "Valles Marineris Mars"),
    spec(18, "olympus-mons", "18. 올림푸스 산", "Olympus Mons Mars"),
    spec(19, "mars-polar-cap", "19. 화성의 극관", "Mars polar ice cap"),
    spec(20, "phobos-over-mars", "20. 포보스와 화성", "Phobos Mars moon", "contain-dark"),
    spec(21, "mercury", "21. 수성", "Mercury planet full disk", "contain-dark"),
    spec(22, "venus", "22. 금성", "Venus planet full disk", "contain-dark"),
    spec(23, "jupiter", "23. 목성", "Jupiter planet full disk", "contain-dark"),
    spec(24, "great-red-spot", "24. 대적점", "Jupiter Great Red Spot"),
    spec(25, "io", "25. 이오", "Jupiter moon Io full disk", "contain-dark"),
    spec(26, "europa", "26. 유로파", "Jupiter moon Europa full disk", "contain-dark"),
    spec(27, "saturn", "27. 토성", "Saturn planet Cassini", "contain-dark"),
    spec(28, "saturn-rings", "28. 토성의 고리", "Saturn and its Rings", "cover"),
    spec(29, "uranus", "29. 천왕성", "Uranus planet full disk", "contain-dark"),
    spec(30, "neptune", "30. 해왕성", "Neptune planet full disk", "contain-dark"),
    spec(31, "tarantula-nebula", "31. 타란툴라 성운", "Tarantula Nebula Spitzer"),
    spec(32, "carina-nebula", "32. 카리나 성운", "Carina Nebula"),
    spec(33, "orion-nebula", "33. 오리온 성운", "Orion Nebula"),
    spec(34, "pillars-of-creation", "34. 창조의 기둥", "Pillars of Creation"),
    spec(35, "helix-nebula", "35. 헬릭스 성운", "Helix Nebula"),
    spec(36, "crab-nebula", "36. 게 성운", "Crab Nebula"),
    spec(37, "veil-nebula", "37. 베일 성운", "Veil Nebula"),
    spec(38, "rosette-nebula", "38. 장미 성운", "Rosette Nebula"),
    spec(39, "star-cluster", "39. 별들의 군집", "star cluster Hubble"),
    spec(40, "supernova-remnant", "40. 초신성의 흔적", "supernova remnant"),
    spec(41, "milky-way-center", "41. 우리은하의 중심", "Milky Way center"),
    spec(42, "andromeda", "42. 안드로메다", "Andromeda galaxy"),
    spec(43, "barred-spiral", "43. 막대나선은하", "Barred Spiral Galaxy"),
    spec(44, "whirlpool-galaxy", "44. 소용돌이 은하", "Whirlpool Galaxy"),
    spec(45, "sombrero-galaxy", "45. 솜브레로 은하", "Sombrero Galaxy"),
    spec(46, "edge-on-galaxy", "46. 옆으로 본 은하", "edge-on galaxy Hubble"),
    spec(47, "interacting-galaxies", "47. 춤추는 두 은하", "interacting galaxies Hubble"),
    spec(48, "galaxy-cluster", "48. 은하단", "galaxy cluster Hubble"),
    spec(49, "deep-field", "49. 허블 딥 필드", "Hubble deep field"),
    spec(50, "gravitational-lens", "50. 중력렌즈", "gravitational lens galaxy cluster"),
    spec(51, "black-hole-jet", "51. 블랙홀의 제트", "Black Hole With Jet artist concept"),
    spec(52, "accretion-disk", "52. 강착원반", "black hole accretion disk artist concept"),
    spec(53, "neutron-star", "53. 중성자별", "neutron star artist concept", "contain-dark"),
    spec(54, "pulsar", "54. 펄서", "pulsar nebula"),
    spec(55, "quasar", "55. 퀘이사", "quasar artist concept"),
    spec(56, "cosmic-web", "56. 우주 거대망", "cosmic web simulation"),
    spec(57, "exoplanet", "57. 외계행성", "exoplanet artist concept"),
    spec(58, "protostar", "58. 태어나는 별", "protostar Webb"),
    spec(59, "deep-universe", "59. 심우주", "Webb deep space galaxies"),
    spec(60, "pale-blue-dot", "60. 창백한 푸른 점", "Pale Blue Dot Voyager", "contain-dark"),
]

KNOWN = {
    1: ROOT / "examples/cosmic-random-brush-v02/assets/scene-01-earth-orbit-sunrise.png",
    11: ROOT / "examples/cosmic-random-brush-v02/assets/scene-06-low-contrast-lunar-surface.png",
    28: ROOT / "examples/cosmic-random-brush-v02/assets/scene-02-saturn-rings.png",
    31: ROOT / "examples/cosmic-random-brush-v02/assets/scene-04-tarantula-nebula.png",
    43: ROOT / "examples/cosmic-random-brush-v02/assets/scene-03-barred-spiral-galaxy.png",
    51: ROOT / "examples/cosmic-random-brush-v02/assets/scene-05-black-hole-accretion-disk.png",
}
KNOWN_META = {
    1: (None, "Approved cosmic-random-brush v0.1 source", None, None),
    11: ("as11-40-5881", "NASA/JSC", "Apollo 11 Mission image - Lunar surface and horizon", "https://images.nasa.gov/details/as11-40-5881"),
    28: ("PIA01969", "NASA/JPL", "Saturn and its Rings", "https://images.nasa.gov/details/PIA01969"),
    31: ("PIA23647", "NASA/JPL-Caltech", "Tarantula Nebula Spitzer 3-Color Image", "https://images.nasa.gov/details/PIA23647"),
    43: ("GSFC_20171208_Archive_e002154", "NASA, ESA, and The Hubble Heritage Team (STScI/AURA); acknowledgment P. Knezek (WIYN)", "Barred Spiral Galaxy", "https://images.nasa.gov/details/GSFC_20171208_Archive_e002154"),
    51: ("PIA22085", "NASA/JPL-Caltech", "Black Hole With Jet (Artist's Concept)", "https://images.nasa.gov/details/PIA22085"),
}
PREFERRED = {
    2: "GSFC_20171208_Archive_e001587",
    4: "GSFC_20171208_Archive_e001386",
    5: "GSFC_20171208_Archive_e000525",
    9: "iss022e005807",
    10: "as17-152-23272",
    13: "art002e012702",
    14: "GSFC_20171208_Archive_e000496",
    15: "PIA17947",
    17: "PIA04262",
    18: "PIA10020",
    19: "PIA24286",
    21: "PIA16908",
    22: "PIA00478",
    23: "PIA01371",
    24: "PIA21772",
    25: "PIA01368",
    26: "PIA00016",
    27: "PIA21047",
    29: "PIA18182",
    30: "PIA00050",
    38: "PIA09268",
    41: "PIA03653",
    52: "PIA14730",
    56: "PIA17014",
    57: "PIA26601",
    58: "PIA18928",
    59: "webb_first_deep_field",
    60: "PIA00452",
}
BAD_TITLE = re.compile(r"\b(animation|diagram|chart|spectrum|spectra|poster|logo|comparison|model grid|map of)\b", re.I)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "brush-remotion-video/0.3"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def download(url: str, path: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "brush-remotion-video/0.3"})
    with urllib.request.urlopen(request, timeout=120) as response:
        path.write_bytes(response.read())


def candidate_url(nasa_id: str) -> str | None:
    asset = get_json(f"{API}/asset/{urllib.parse.quote(nasa_id)}")
    hrefs = [item.get("href", "").replace("http://", "https://")
             for item in asset.get("collection", {}).get("items", [])]
    images = [h for h in hrefs if h.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png"))]
    for marker in ("~large.", "~orig.", "~medium.", "~small."):
        for href in images:
            if marker in href.lower():
                return href
    return images[0] if images else None


def metadata_for_id(nasa_id: str) -> dict:
    result = get_json(f"{API}/search?{urllib.parse.urlencode({'nasa_id': nasa_id})}")
    items = result.get("collection", {}).get("items", [])
    if not items:
        raise RuntimeError(f"NASA metadata missing for {nasa_id}")
    return (items[0].get("data") or [{}])[0]


def fetch_candidate(nasa_id: str, data: dict) -> tuple[Path, dict]:
    url = candidate_url(nasa_id)
    if not url:
        raise RuntimeError(f"NASA asset missing for {nasa_id}")
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
    cached = CACHE / f"{nasa_id}{suffix}"
    if not cached.is_file():
        download(url, cached)
    description = data.get("description", "")
    credit = data.get("secondary_creator") or data.get("photographer")
    if not credit:
        match = re.search(r"Credit:\s*([^<\n]{3,180})", description, re.I)
        credit = match.group(1).strip() if match else f"NASA/{data.get('center', 'Image Library')}"
    return cached, {
        "nasaId": nasa_id, "sourceTitle": data.get("title", nasa_id), "credit": credit,
        "sourcePage": f"https://images.nasa.gov/details/{nasa_id}",
        "originalUrl": url, "dateCreated": data.get("date_created"),
        "center": data.get("center"),
    }


def choose_source(scene: dict, used: set[str]) -> tuple[Path, dict]:
    preferred = PREFERRED.get(scene["scene"])
    if preferred:
        source, metadata = fetch_candidate(preferred, metadata_for_id(preferred))
        used.add(preferred)
        return source, metadata
    query = urllib.parse.urlencode({"q": scene["query"], "media_type": "image", "page_size": 30})
    result = get_json(f"{API}/search?{query}")
    for item in result.get("collection", {}).get("items", []):
        data = (item.get("data") or [{}])[0]
        nasa_id = data.get("nasa_id")
        title = data.get("title", "")
        if not nasa_id or nasa_id in used or BAD_TITLE.search(title):
            continue
        try:
            cached, metadata = fetch_candidate(nasa_id, data)
            with Image.open(cached) as im:
                if min(im.size) < 600 or max(im.size) < 1000:
                    continue
            used.add(nasa_id)
            return cached, metadata
        except Exception as exc:
            print(f"skip {scene['scene']:02d} {nasa_id}: {exc}")
            time.sleep(0.1)
    raise RuntimeError(f"scene-{scene['scene']:02d}: no usable NASA result for {scene['query']!r}")


def normalize(source: Path, fit: str) -> Image.Image:
    im = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    if fit == "contain-dark":
        scale = min((SIZE[0] * 0.94) / im.width, (SIZE[1] * 0.94) / im.height)
        resized = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", SIZE, (2, 4, 13))
        canvas.paste(resized, ((SIZE[0] - resized.width) // 2, (SIZE[1] - resized.height) // 2))
        return canvas
    scale = max(SIZE[0] / im.width, SIZE[1] / im.height)
    resized = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.Resampling.LANCZOS)
    left = (resized.width - SIZE[0]) // 2
    top = (resized.height - SIZE[1]) // 2
    return resized.crop((left, top, left + SIZE[0], top + SIZE[1]))


def write_contact_sheet(entries: list[dict]) -> None:
    tw, th, label_h, cols = 320, 180, 28, 5
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (tw * cols, (th + label_h) * rows), (3, 5, 13))
    draw = ImageDraw.Draw(sheet)
    for index, entry in enumerate(entries):
        im = Image.open(ROOT / entry["file"]).convert("RGB").resize((tw, th), Image.Resampling.LANCZOS)
        x, y = (index % cols) * tw, (index // cols) * (th + label_h)
        sheet.paste(im, (x, y))
        draw.text((x + 7, y + th + 6), f"{entry['scene']:02d}. {entry['slug']}", fill=(220, 240, 255))
    sheet.save(OUT / "contact-sheet.jpg", quality=91)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    used = {meta[0] for meta in KNOWN_META.values() if meta[0]}
    entries = []
    for scene in SCENES:
        output = OUT / f"scene-{scene['scene']:02d}-{scene['slug']}.png"
        if scene["scene"] in KNOWN:
            source = KNOWN[scene["scene"]]
            output.write_bytes(source.read_bytes())
            nasa_id, credit, source_title, source_page = KNOWN_META[scene["scene"]]
            metadata = {"nasaId": nasa_id, "credit": credit, "sourceTitle": source_title,
                        "sourcePage": source_page, "originalUrl": None, "dateCreated": None,
                        "center": None}
        else:
            source, metadata = choose_source(scene, used)
            normalize(source, scene["fit"]).save(output, optimize=True)
        with Image.open(output) as image:
            if image.size != SIZE:
                raise ValueError(f"{output}: {image.size} != {SIZE}")
        entry = {**scene, **metadata,
                 "file": str(output.relative_to(ROOT)),
                 "sourceFileSha256": sha256(source),
                 "normalizedSha256": sha256(output),
                 "width": SIZE[0], "height": SIZE[1]}
        entries.append(entry)
        print(f"[{scene['scene']:02d}/60] {entry.get('nasaId') or 'golden'} {entry['sourceTitle'] or entry['title']}")
    manifest = {
        "projectId": "cosmic-random-brush-v03-60",
        "version": "0.3-production",
        "canvas": {"width": SIZE[0], "height": SIZE[1]},
        "mediaUsageGuidelines": USAGE,
        "usageNote": "NASA source acknowledgement required; no NASA endorsement implied; verify third-party credits before public release.",
        "scenes": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_contact_sheet(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
