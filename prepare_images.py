#!/usr/bin/env python3
"""
Paruosia story paveikslelius: bet kokio formato nuotrauka is `source/` paverciama
1080x1920 (9:16) story remu ir issaugoma i `media/`.

- Tikras vaizdas itelpa be iskraipymo ir be apkarpymo (contain).
- Likes remas uzpildomas suliejus (blurred) ta pacia nuotrauka -> uzpildomas VISAS remas.

Paleidziama automatiskai per GitHub Actions; gali paleisti ir lokaliai:
    python prepare_images.py
"""

import os
import pathlib

from PIL import Image, ImageOps, ImageFilter

TARGET_W, TARGET_H = 1080, 1920   # Instagram/Facebook story drobe (9:16)
BLUR_RADIUS = 40
EXTS = {".jpg", ".jpeg", ".png"}

# contain = visas vaizdas matosi (didinamas) + sulietas fonas uzpildo likuti
# cover   = nuotrauka uzpildo VISA rema iki krastu (perteklius apkarpomas, be fono)
FILL_MODE = os.environ.get("IMAGE_FILL_MODE", "contain").lower()

ROOT = pathlib.Path(__file__).parent
# Is kurio aplanko imti nuotraukas (numatyta "source"; galima keisti per SOURCE_DIR)
SRC_DIR = ROOT / os.environ.get("SOURCE_DIR", "source")
DST_DIR = ROOT / "media"


def make_story(img: Image.Image) -> Image.Image:
    """Sukuria 1080x1920 story is bet kokio formato paveikslelio."""
    img = img.convert("RGB")

    # cover: nuotrauka uzpildo visa rema iki krastu (perteklius apkarpomas)
    if FILL_MODE == "cover":
        return ImageOps.fit(img, (TARGET_W, TARGET_H), method=Image.LANCZOS)

    # contain: sulietas fonas + visas vaizdas, DIDINAMAS kad uzpildytu kuo daugiau
    bg = ImageOps.fit(img, (TARGET_W, TARGET_H), method=Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))

    # Mastelis: itelpa i drobe (be apkarpymo), bet ir DIDINA mazas nuotraukas
    scale = min(TARGET_W / img.width, TARGET_H / img.height)
    new_w = max(1, round(img.width * scale))
    new_h = max(1, round(img.height * scale))
    fg = img.resize((new_w, new_h), Image.LANCZOS)

    x = (TARGET_W - new_w) // 2
    y = (TARGET_H - new_h) // 2
    bg.paste(fg, (x, y))
    return bg


def main() -> None:
    SRC_DIR.mkdir(exist_ok=True)
    DST_DIR.mkdir(exist_ok=True)
    print(f"Naudojamas aplankas: {SRC_DIR.name}/")

    sources = [
        p for p in SRC_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in EXTS
    ]
    if not sources:
        print(f"{SRC_DIR.name}/ aplanke nera paveiksleliu - nieko neapdorota.")
        return

    # Issvalom senus apdorotus (kad neliktu naslaiciu), .gitkeep paliekam
    for old in DST_DIR.iterdir():
        if old.is_file() and old.suffix.lower() in EXTS:
            old.unlink()

    for src in sorted(sources):
        out = DST_DIR / (src.stem + ".jpg")
        with Image.open(src) as im:
            story = make_story(im)
        story.save(out, "JPEG", quality=90)
        print(f"OK: source/{src.name} -> media/{out.name}")

    print(f"Apdorota: {len(sources)} paveiksleliu.")


if __name__ == "__main__":
    main()
