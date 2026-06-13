# Auto Stories — kasdienis story kėlimas į Instagram + Facebook puslapį

Skriptas kiekvieną dieną automatiškai paskelbia story į tavo **Instagram Professional**
paskyrą ir/arba **Facebook puslapį (Page)** per oficialų **Meta Graph API**.

Sukasi **GitHub Actions cron** debesyje — tad veikia **nepriklausomai nuo to, ar tavo
kompiuteris įjungtas**. Nemokama, be banų rizikos, be naršyklės automatizavimo.

> ⚠️ **Svarbu žinoti iš anksto:**
> - FB story keliauja į **puslapį**, NE į tavo asmeninį profilį (kito kelio per API nėra).
> - IG story keliauja į tavo **tikrą** IG Professional paskyrą.
> - IG **Stories** publikavimas per API yra mažiausiai stabili API dalis — pirma pasitestuok.

---

## Kas yra šiame projekte

```
auto-stories/
├─ post_stories.py                  # pagrindinis skriptas (kelia story)
├─ prepare_images.py                # paverčia source/ nuotraukas į 1080x1920 → media/
├─ sync_from_cloud.sh               # rclone mirror: Google Drive aplankas → source/
├─ requirements.txt                 # Python priklausomybės (requests, Pillow)
├─ source/                          # AUTOMATIŠKAI sinchronizuojamas iš telefono (per Drive)
├─ media/                           # automatiškai sugeneruoti 1080x1920 story paveikslėliai
├─ .github/workflows/sync-from-phone.yml # cron (kas 6 h) — Google Drive → source/
├─ .github/workflows/daily-stories.yml   # cron — kasdien paruošia + kelia
├─ .env.example                     # pavyzdys lokaliam testavimui
└─ README.md
```

> 📱 **`source/` pildosi PATS iš telefono.** Telefono galerijos albumas per
> „Autosync for Google Drive" (dvikryptis, su trynimu) keliauja į Google Drive aplanką,
> o `sync-from-phone.yml` workflow kas 6 h veidrodiškai (`rclone sync`) perkelia jį į
> `source/`. **Ištrini nuotrauką telefone → ji dingsta ir iš `source/`, ir iš story.**
> Ranka į `source/` nieko dėti nereikia.

> 📐 Workflow automatiškai paverčia `source/` nuotraukas 1080×1920 (9:16) story rėmu
> (vaizdas centre be iškraipymo, fonas užpildytas suliejus) ir įrašo į `media/`.

Skriptas kiekvieną paleidimą **atsitiktinai parenka iki `STORIES_PER_RUN` paveikslėlių**
(numatyta 50) iš `media/` ir paskelbia kiekvieną kaip atskirą story. Jei `media/` yra
mažiau nei prašyta — keliami visi turimi.

> ⚠️ **Instagram limitas:** ~25–100 paskelbimų / 24 h vienai paskyrai (daugeliui — 25).
> Jei `STORIES_PER_RUN=50`, dalis IG story gali nepavykti pasiekus ribą — skriptas tai
> aprašo suvestinėje ir nenutraukia darbo. Facebook fiksuoto kiekio limito neturi.
> Realią IG kvotą tikrini: `GET /{IG_USER_ID}/content_publishing_limit`.

---

## Reikalavimai

1. **Instagram Professional** paskyra (Business arba Creator) — nemokama, perjungi IG
   nustatymuose.
2. **Facebook puslapis (Page)** — nemokamas (jei nori FB dalies; kitaip darai vien IG).
3. **GitHub** paskyra — nemokama.

---

## Setup žingsnis po žingsnio

### 1. Susiek IG su FB puslapiu (paprasčiausias kelias)

Kadangi vis tiek kuri ir FB puslapį, ir Meta app — paprasčiausia IG Professional
paskyrą **susieti su tuo puslapiu** (Meta Business Suite → Settings → Linked accounts,
arba IG → Settings → „Page"). Tada **viena** Meta app valdo abu.

> Nenori sieti? Galima ir taip: IG dirbk per „Instagram Login" (žr. žemiau „Be susiejimo").

### 2. Sukurk Meta Developer app

1. Eik į **developers.facebook.com** → *My Apps* → **Create App**.
2. Tipas: **Business**.
3. App viduje pridėk produktus: **Facebook Login** ir **Instagram** (Instagram Graph API).
4. **Palik app „Development" režime.** Kol publikuoji tik į **savo paties** paskyras
   (esi app administratorius), pilno **App Review** NEREIKIA. Tai sutaupo daug laiko.

### 3. Reikalingi leidimai (permissions)

Naudok **Graph API Explorer** (developers.facebook.com/tools/explorer), pasirink savo app
ir sugeneruok **User Token** su šiais leidimais:

- `pages_show_list`
- `pages_read_engagement`
- `pages_manage_posts`
- `instagram_basic`
- `instagram_content_publish`

### 4. Gauk ID ir tokenus

Su tuo pačiu Graph API Explorer:

**Facebook puslapio ID + token:**
```
GET /me/accounts
```
Atsakyme rasi savo puslapio `id` (= **FB_PAGE_ID**) ir `access_token`
(= **FB_PAGE_ACCESS_TOKEN**).

**Instagram user ID** (kai IG susietas su puslapiu):
```
GET /{FB_PAGE_ID}?fields=instagram_business_account
```
Grąžintas `instagram_business_account.id` = **IG_USER_ID**. Kaip **IG_ACCESS_TOKEN**
gali naudoti tą **patį puslapio tokeną** (`FB_PAGE_ACCESS_TOKEN`) — jis tinka ir IG
publikavimui per `graph.facebook.com`.

> 💡 **Kad tokenas nenustotų galioti po 60 d.** — vietoj asmeninio tokeno susikurk
> **System User** tokeną per **business.facebook.com → Business Settings → System Users**.
> Jo tokenas gali būti **nesibaigiantis** — idealu „nustatyk ir pamiršk" automatizacijai.
> Antraip tokeną teks atnaujinti maždaug kas 60 dienų.

### 5. Sukurk GitHub repozitoriją ir įkelk šiuos failus

- Sukurk **viešą (Public)** repozitoriją. *Vieša reikalinga todėl, kad IG/FB galėtų
  parsisiųsti paveikslėlį per `raw.githubusercontent.com`. Paveikslėliai vis tiek bus
  vieši — juk juos skelbi kaip story. Slapti tokenai NEbus repe (jie eina į Secrets).*
- Įkelk visus šio aplanko failus.
- Į `media/` įdėk savo story paveikslėlius (geriausia 1080×1920 px).

> Jei nori laikyti repą **privatų**, paveikslėlius hostink kitur (savo serveris, S3,
> Cloudflare R2 ir pan.) ir workflow faile nustatyk `MEDIA_BASE_URL`.

### 6. Įdėk Secrets į GitHub

Repozitorijoje: **Settings → Secrets and variables → Actions → New repository secret**.
Sukurk šiuos keturis:

| Secret pavadinimas      | Reikšmė                          |
|-------------------------|----------------------------------|
| `IG_USER_ID`            | Instagram user ID                |
| `IG_ACCESS_TOKEN`       | Instagram (ar System User) tokenas |
| `FB_PAGE_ID`            | Facebook puslapio ID             |
| `FB_PAGE_ACCESS_TOKEN`  | Facebook puslapio tokenas        |

### 7. Pasitestuok RANKINIU būdu

Repozitorijoje: **Actions → „Daily Stories" → Run workflow**. Tai paleidžia iškart
(nelaukiant ryto). Atidaryk paleidimą ir žiūrėk logą — turi matytis `IG: OK` / `FB: OK`.

Po to cron pats suks kasdien (numatyta **09:00 Lietuvos laiku**).

---

## Telefono sinchronizacija (Google Drive → `source/`)

Kad nuotraukos automatiškai keliautų iš telefono galerijos į `source/` (ir ištrynimai
propaguotųsi), reikia dviejų dalykų: **telefono pusės** (Autosync) ir **GitHub pusės**
(rclone tokeno Secret'e).

### Telefono pusė (Android)
1. Galerijoje pasidaryk vieną albumą (= aplanką), kuriame laikysi story nuotraukas.
2. Įdiek **„Autosync for Google Drive"** (MetaCtrl).
3. Sukurk sync porą: tas galerijos albumas ⇄ tavo Google Drive aplankas.
4. **Sync method = Two-way**, įjunk **„Sync deletions"** (kad ištrynimas telefone
   ištrintų ir Drive). Įjunk autosync / instant sync.

### GitHub pusė (vienkartinai)
1. Lokaliai įdiek [rclone](https://rclone.org/install/) ir paleisk `rclone config`:
   sukurk remote, **pavadink jį `drive`**, tipas — *Google Drive*, autorizuokis savo
   Google paskyra. (Arba `rclone authorize drive`.)
2. Rask gautą `rclone.conf` (`rclone config file` parodo kelią) ir užkoduok base64:
   ```powershell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("$env:APPDATA\rclone\rclone.conf"))
   ```
3. Repozitorijoje: **Settings → Secrets and variables → Actions → New repository secret**,
   pavadinimas **`RCLONE_CONF_B64`**, reikšmė — nukopijuotas base64.
4. Drive aplanko ID jau įrašytas `sync_from_cloud.sh` (`DRIVE_FOLDER_ID`). Jei keisi
   aplanką — paimk naują ID iš nuorodos `.../folders/<ID>` ir atnaujink ten.
5. Pasitestuok: **Actions → „Sync from phone" → Run workflow**. Po jo `source/` turi
   atsispindėti tavo telefono albumą.

Po to cron'as kas 6 h pats laikys `source/` šviežią; kasdienis „Daily Stories" workflow
prieš kėlimą dar kartą sinchronizuoja, tad story visada atspindi naujausią telefono būklę.

---

## Dažni nustatymai

- **Pakeisti laiką:** redaguok `cron` eilutę `.github/workflows/daily-stories.yml`
  (laikas **UTC**: vasarą atimk 3 h, žiemą 2 h nuo norimo Lietuvos laiko).
- **Tik IG arba tik FB:** workflow faile nustatyk `ENABLE_IG` / `ENABLE_FB` į `"false"`.
- **Be IG↔FB susiejimo:** workflow faile pakeisk `IG_GRAPH_HOST` į `graph.instagram.com`
  ir kaip `IG_ACCESS_TOKEN` naudok „Instagram Login" tokeną.

---

## Apribojimai (gerai žinoti)

- **Dienos limitas:** IG iki ~100 paskelbimų / 24 h vienai paskyrai; FB puslapis fiksuoto
  įrašų limito neturi. 1 story/dieną — toli iki bet kokios ribos.
- **Tokeno galiojimas:** įprastas tokenas ~60 d. Nesibaigiančiam — naudok System User.
- **FB story:** be teksto/paminėjimų; video ≤ 60 s; ta pati nuotrauka neturi būti jau
  panaudota kitame įraše (skriptas kaskart įkelia naują, tad tvarkoj).
- **GitHub cron:** gali vėluoti kelias minutes; privačiame repe po 60 d. neaktyvumo cron
  gali būti sustabdytas (viešame — ne).
- **Vaizdo dydis:** rekomenduojama 1080×1920 px (9:16).

---

## Lokalus testavimas (nebūtina)

```powershell
# Windows / PowerShell
python -m pip install -r requirements.txt
Copy-Item .env.example .env   # užpildyk reikšmes; būtinai nurodyk MEDIA_BASE_URL
# Įkelk reikšmes į aplinką ir paleisk:
python post_stories.py
```
