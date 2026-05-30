#!/usr/bin/env python3
"""
Kasdien paskelbia story i Instagram (Professional paskyra) ir/arba i Facebook
puslapi (Page) per oficialu Meta Graph API.

Skirta paleisti per GitHub Actions cron - tad veikia DEBESYJE, nepriklausomai
nuo to, ar tavo kompiuteris ijungtas, ar ne.

Konfiguracija perduodama per aplinkos kintamuosius (zr. README.md).
"""

import os
import sys
import time
import random
import datetime
import pathlib

import requests

GRAPH_VERSION = os.environ.get("GRAPH_VERSION", "v23.0")
HTTP_TIMEOUT = 60  # sekundes
STORIES_PER_RUN = int(os.environ.get("STORIES_PER_RUN", "50"))   # kiek nuotrauku per paleidima
DELAY_BETWEEN = int(os.environ.get("DELAY_BETWEEN", "5"))         # pauze (s) tarp paskelbimu


# --------------------------------------------------------------------------
# Bendros pagalbines funkcijos
# --------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def env(name: str, default=None, required: bool = False):
    val = os.environ.get(name, default)
    if required and not val:
        log(f"KLAIDA: truksta privalomo kintamojo {name}")
        sys.exit(1)
    return val


def pick_media_files(count: int) -> list:
    """Atsitiktinai parenka iki `count` paveiksleliu is media/ aplanko (be pasikartojimu)."""
    media_dir = pathlib.Path(__file__).parent / "media"
    exts = {".jpg", ".jpeg", ".png"}
    files = [
        p.name for p in media_dir.iterdir()
        if p.is_file() and p.suffix.lower() in exts
    ]
    if not files:
        log("KLAIDA: media/ aplanke nera paveiksleliu (.jpg/.jpeg/.png).")
        sys.exit(1)
    n = min(count, len(files))
    if len(files) < count:
        log(f"DEMESIO: media/ yra tik {len(files)} paveiksleliu (prasyta {count}). Keliami visi.")
    # random.sample parenka ATSITIKTINIUS failus; po to dar permaisom, kad ir
    # PASKELBIMO TVARKA butu atsitiktine (NE pagal pavadinima), net keliant visus.
    chosen = random.sample(files, n)
    random.shuffle(chosen)
    log(f"Atsitiktinai parinkta {n} paveiksleliu atsitiktine tvarka (is {len(files)} esanciu).")
    return chosen


def media_url(filename: str) -> str:
    """Sukonstruoja VIESAI pasiekiama paveikslelio URL.

    - Jei nustatytas MEDIA_BASE_URL -> naudoja ji.
    - Kitaip (GitHub Actions) -> sukuria GitHub raw URL. SVARBU: tam repozitorija
      turi buti VIESA, kitaip IG/FB nesugebes parsisiusti paveikslelio.
    """
    base = os.environ.get("MEDIA_BASE_URL")
    if base:
        return f"{base.rstrip('/')}/{filename}"
    repo = env("GITHUB_REPOSITORY", required=True)        # "savininkas/repas"
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/media/{filename}"


# --------------------------------------------------------------------------
# Instagram Stories
# --------------------------------------------------------------------------

def post_instagram_story(image_url: str) -> bool:
    token = env("IG_ACCESS_TOKEN", required=True)
    ig_user_id = env("IG_USER_ID", required=True)
    host = os.environ.get("IG_GRAPH_HOST", "graph.facebook.com")
    base = f"https://{host}/{GRAPH_VERSION}"

    # 1) Sukuriame media konteineri (STORIES)
    log("IG: kuriamas media konteineris (media_type=STORIES)...")
    r = requests.post(
        f"{base}/{ig_user_id}/media",
        data={
            "image_url": image_url,
            "media_type": "STORIES",
            "access_token": token,
        },
        timeout=HTTP_TIMEOUT,
    )
    data = r.json()
    if "id" not in data:
        log(f"IG KLAIDA kuriant konteineri: {data}")
        return False
    container_id = data["id"]

    # 2) Palaukiame, kol konteineris bus paruostas (FINISHED)
    for _ in range(10):
        status = requests.get(
            f"{base}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=HTTP_TIMEOUT,
        ).json().get("status_code")
        if status == "FINISHED":
            break
        if status == "ERROR":
            log("IG KLAIDA: konteineris grizo i ERROR busena.")
            return False
        log(f"IG: laukiama, kol pasiruos (status={status})...")
        time.sleep(3)

    # 3) Publikuojame
    log("IG: publikuojama...")
    r = requests.post(
        f"{base}/{ig_user_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=HTTP_TIMEOUT,
    )
    data = r.json()
    if "id" in data:
        log(f"IG: OK - paskelbta, media_id={data['id']}")
        return True
    log(f"IG KLAIDA publikuojant: {data}")
    return False


# --------------------------------------------------------------------------
# Facebook puslapio (Page) Stories
# --------------------------------------------------------------------------

def post_facebook_story(image_url: str) -> bool:
    token = env("FB_PAGE_ACCESS_TOKEN", required=True)
    page_id = env("FB_PAGE_ID", required=True)
    base = f"https://graph.facebook.com/{GRAPH_VERSION}"

    # 1) Ikeliame NEPUBLIKUOTA nuotrauka -> gauname photo_id
    log("FB: ikeliamas nepublikuotas paveikslelis...")
    r = requests.post(
        f"{base}/{page_id}/photos",
        data={"url": image_url, "published": "false", "access_token": token},
        timeout=HTTP_TIMEOUT,
    )
    data = r.json()
    if "id" not in data:
        log(f"FB KLAIDA ikeliant nuotrauka: {data}")
        return False
    photo_id = data["id"]

    # 2) Publikuojame photo_story
    log("FB: publikuojamas photo_story...")
    r = requests.post(
        f"{base}/{page_id}/photo_stories",
        data={"photo_id": photo_id, "access_token": token},
        timeout=HTTP_TIMEOUT,
    )
    data = r.json()
    if data.get("success") or "post_id" in data or "id" in data:
        log(f"FB: OK - paskelbta: {data}")
        return True
    log(f"FB KLAIDA publikuojant story: {data}")
    return False


# --------------------------------------------------------------------------
# Pagrindinis srautas
# --------------------------------------------------------------------------

def main() -> None:
    enable_ig = os.environ.get("ENABLE_IG", "true").lower() == "true"
    enable_fb = os.environ.get("ENABLE_FB", "true").lower() == "true"

    files = pick_media_files(STORIES_PER_RUN)

    ig_ok = ig_fail = fb_ok = fb_fail = 0

    for idx, filename in enumerate(files, start=1):
        url = media_url(filename)
        log(f"===== [{idx}/{len(files)}] {filename} =====")

        if enable_ig:
            if post_instagram_story(url):
                ig_ok += 1
            else:
                ig_fail += 1

        if enable_fb:
            if post_facebook_story(url):
                fb_ok += 1
            else:
                fb_fail += 1

        # Pauze tarp paskelbimu (svelnesnis tempas, mazesne spam-detekcijos rizika)
        if idx < len(files) and DELAY_BETWEEN > 0:
            time.sleep(DELAY_BETWEEN)

    log("==================== SUVESTINE ====================")
    if enable_ig:
        log(f"IG: pavyko {ig_ok}, nepavyko {ig_fail}")
    if enable_fb:
        log(f"FB: pavyko {fb_ok}, nepavyko {fb_fail}")

    # Klaida tik jei NIEKAS nepavyko; dalines nesekmes nenutraukia darbo.
    if (ig_ok + fb_ok) == 0 and (ig_fail + fb_fail) > 0:
        log("Nepavyko paskelbti nei vieno.")
        sys.exit(1)
    log("Baigta.")


if __name__ == "__main__":
    main()
