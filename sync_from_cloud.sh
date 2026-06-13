#!/usr/bin/env bash
#
# Veidrodiskai (mirror) atsisiunciam Google Drive aplanka i ./source.
#
# `rclone sync` padaro PASKIRTI (source/) identiska SALTINIUI (Drive aplankui):
#   - naujos nuotraukos Drive   -> atsiranda source/
#   - istrintos nuotraukos Drive -> istrinamos ir is source/  (=> trynimas propaguojasi)
#
# Drive aplankas pildomas telefono "Autosync for Google Drive" programos, kuri
# dvikrypciai sinchronizuoja galerijos albuma <-> Drive (su trynimu).
#
# Paleidziama is GitHub Actions; konfiguracija (token'as) ateina is rclone.conf,
# kuris atkuriamas is GitHub Secret RCLONE_CONF_B64.

set -euo pipefail

# rclone remote pavadinimas (toks, kokiu pavadinai per `rclone config` / authorize).
REMOTE="${RCLONE_REMOTE:-drive}"

# Google Drive aplanko ID. Imamas is nuorodos:
#   https://drive.google.com/drive/.../folders/<ID>
DRIVE_FOLDER_ID="${DRIVE_FOLDER_ID:-1SxyXlFS1sOrfbomptJHtI8ExRoJHNrgp}"

# Paskirties aplankas repe.
DEST="${DEST:-source}"

mkdir -p "$DEST"

echo "Sinchronizuojama: ${REMOTE}: (folderId=${DRIVE_FOLDER_ID}) -> ${DEST}/"

rclone sync "${REMOTE}:" "$DEST" \
  --drive-root-folder-id "$DRIVE_FOLDER_ID" \
  --exclude ".gitkeep" \
  --fast-list \
  --verbose

echo "Sinchronizacija baigta."
