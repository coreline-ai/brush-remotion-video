"""background.py 테스트 — TC-3.E3(imagegen 폴백) + clean/user-images."""
import logging

import numpy as np
from PIL import Image

from brushvid.background import PAPER, clean, generate


def test_tc_3_e3_imagegen_fallback_to_preset(tmp_path, caplog):
    """TC-3.E3: codex exec 부재 → preset 폴백 + 경고 로그."""
    out = tmp_path / "bg.png"
    with caplog.at_level(logging.WARNING, logger="brushvid.background"):
        res = generate("imagegen", out, subject="winter pine", seed=3,
                       codex_bin=str(tmp_path / "no-such-codex"))
    assert res["strategy"] == "preset"
    assert out.is_file()
    img = Image.open(out)
    assert img.size == (1920, 1080)
    assert any("폴백" in r.message for r in caplog.records)


def test_preset_deterministic(tmp_path):
    """같은 시드의 preset 배경은 결정적(바이트 동일 픽셀)이다."""
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    generate("preset", a, seed=42)
    generate("preset", b, seed=42)
    assert np.array_equal(np.asarray(Image.open(a)), np.asarray(Image.open(b)))


def test_user_images_contain_fit(tmp_path):
    """user-images: 종이 캔버스에 contain-fit 배치, 1920×1080 출력."""
    src = tmp_path / "src.png"
    Image.new("RGB", (640, 640), (30, 60, 120)).save(src)
    out = tmp_path / "bg.png"
    res = generate("user-images", out, images=[src])
    assert res["strategy"] == "user-images"
    img = Image.open(out)
    assert img.size == (1920, 1080)
    arr = np.asarray(img)
    assert (arr[0, 0] == PAPER).all()  # 모서리는 종이색


def test_clean_replaces_near_paper(tmp_path):
    """clean: near-paper(밝고 채도 낮은) 픽셀이 종이색으로 치환된다."""
    img = Image.new("RGB", (200, 100), (243, 243, 243))  # 모눈 격자 톤
    for x in range(50):
        for y in range(100):
            img.putpixel((x, y), (60, 40, 30))  # 잉크
    src = tmp_path / "src.png"
    img.save(src)
    out = clean(src, tmp_path / "clean.png")
    arr = np.asarray(Image.open(out))
    assert (arr[50, 150] == PAPER).all()   # 격자 톤 → 종이색
    assert (arr[50, 10] == (60, 40, 30)).all()  # 잉크는 유지
