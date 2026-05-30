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
DST_DIR = ROOT / "media"

# Is kurio aplanko (-u) imti nuotraukas. Galimos reiksmes per SOURCE_DIR:
#   "source"   -> tik pirmas aplankas
#   "source2"  -> tik antras aplankas
#   "both"     -> abu aplankai sujungiami
#   arba keli, atskirti kableliais, pvz. "source,source2"
def resolve_source_dirs() -> list:
    raw = os.environ.get("SOURCE_DIR", "source").strip().lower()
    if raw == "both":
        names = ["source", "source2"]
    else:
        names = [n.strip() for n in raw.split(",") if n.strip()]
    return [ROOT / n for n in names]


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
    DST_DIR.mkdir(exist_ok=True)
    src_dirs = resolve_source_dirs()
    print(f"Naudojami aplankai: {', '.join(d.name + '/' for d in src_dirs)}")

    # Surenkam (aplankas, failas) poras is visu nurodytu aplanku
    jobs = []  # [(src_dir, src_path), ...]
    for d in src_dirs:
        if not d.is_dir():
            print(f"DEMESIO: aplanko {d.name}/ nera - praleidziu.")
            continue
        found = [p for p in d.iterdir() if p.is_file() and p.suffix.lower() in EXTS]
        if not found:
            print(f"DEMESIO: {d.name}/ aplanke nera paveiksleliu - praleidziu.")
        jobs.extend((d, p) for p in sorted(found))

    if not jobs:
        print("Nei viename nurodytame aplanke nera paveiksleliu - nieko neapdorota.")
        return

    # Issvalom senus apdorotus (kad neliktu naslaiciu), .gitkeep paliekam
    for old in DST_DIR.iterdir():
        if old.is_file() and old.suffix.lower() in EXTS:
            old.unlink()

    for src_dir, src in jobs:
        # Vardas su aplanko priesdeliu, kad vienodi pavadinimai skirtinguose
        # aplankuose (pvz. source/1.jpg ir source2/1.jpg) nepersirasytu.
        out = DST_DIR / f"{src_dir.name}__{src.stem}.jpg"
        with Image.open(src) as im:
            story = make_story(im)
        story.save(out, "JPEG", quality=90)
        print(f"OK: {src_dir.name}/{src.name} -> media/{out.name}")

    print(f"Apdorota: {len(jobs)} paveiksleliu.")


if __name__ == "__main__":
    main()
