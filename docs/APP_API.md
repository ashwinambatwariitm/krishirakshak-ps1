# KrishiRakshak device API - for building the farmer app

The analysis runs on the Raspberry Pi 5 inside one C++ program (`krishirakshak --serve 8080`): photo quality check,
tomato disease classifier, insect pest detector, severity estimate, knowledge base retrieval (ICAR, NIPHM, TNAU) and
Llama 3.2 through ExecuTorch. The app does not do any analysis. It only:

1. lets the farmer take or choose a leaf photo and pick a language (English / Hindi),
2. sends the photo to the device and shows the JSON answer described here,
3. optionally sends a follow-up question.

Because the app only talks to this API, it can be built and tested with the mock server and example answers below,
and later pointed at the Pi without changes.

```
 phone / browser app  --HTTP (Pi Wi-Fi hotspot or same LAN, no internet)-->  Raspberry Pi 5: krishirakshak --serve 8080
```

## Example answers and mock server

Real answers saved from the device program are in `docs/api_examples/`:

| File | Case |
|---|---|
| `info.json` | `GET /api/info` |
| `analyse_en_early_blight.json` | disease found, Llama explanation accepted |
| `analyse_en_healthy_leaf.json` | healthy leaf, no Llama text (falls back to the extracts) |
| `analyse_hi_late_blight.json` | Hindi answer (names and extracts in Hindi; no Llama text in Hindi by design) |
| `analyse_en_uncertain.json` | the model is not sure (`status: "uncertain"`) |
| `analyse_en_retake_photo.json` | photo too dark / blurred (`status: "retake_photo"`) |
| `analyse_en_pest_CONSTRUCTED.json` | insect pest detected (constructed from the real format; no insect photo was available) |
| `ask_en_harvest_after_spraying.json` | follow-up question; here the Llama answer was rejected (it invented "5 days") |

Mock server (Python standard library only, allows CORS):

```
python tools/mock_api_server.py                  # http://localhost:8080
curl --data-binary @leaf.jpg "http://localhost:8080/api/analyse?lang=en&example=uncertain"
```
`example` = `early_blight` (default), `healthy`, `hindi`, `uncertain`, `retake`, `pest`; `lang=hi` returns the Hindi
example. The mock waits 2 s (`--delay`); the real device needs 10-20 s with Llama 1B and about 45 s with Llama 3B, so
the app must show a clear "checking..." state and must not time out before 60 s.

## Calls

### `GET /api/info`
Model and knowledge base versions, for an "about" screen. Fields: `disease_model`, `pest_model`, `llama` (model file),
`kb_version`, `kb_reviewed` (false = draft under expert review: show "draft"), `runtime`, `load_ms`.
Show the line "Advice is taken from ICAR, NIPHM and TNAU publications. Built with Llama." (required by the Llama
licence).

### `POST /api/analyse?lang=en|hi`
Body: the raw image bytes (JPEG or PNG, as taken by the camera; no multipart form, no base64).
Answer: one JSON object. **Start from `status`:**

| `status` | Meaning | What the app shows |
|---|---|---|
| `answered` | a disease (or healthy) and/or a pest was identified | result screen (below) |
| `uncertain` | photo is fine but the model is not sure | `messages` + advice to retake or ask the local KVK; no diagnosis |
| `retake_photo` | photo is too dark, bright, blurred or small | `messages` (one line per problem) and a "take another photo" button |
| `not_tomato` | no crop leaf and no insect pest in the photo (the name is kept for compatibility) | `messages` ("No crop leaf and no insect pest was found in this photo. Take a photo of the affected leaf, or of the insect on the plant, in daylight.") and a "take another photo" button; no diagnosis |

Leaf disease and pest detection are equal tasks. When the photo shows no leaf of a supported crop but an insect is found, `status` is `answered` with `disease.not_tomato_leaf: true`, no disease name, confidence or severity, the pest result as usual, and the message "No crop leaf is visible in the photo, so no leaf disease was checked." The app shows it as a pest result ("Pest detected"). `leaf_check` (`is_tomato_leaf`, `p_other`, `threshold`, `model`) is in every result when the model is installed.

`crop`: the crop detected in the photo, e.g. `{"name": "tomato", "source": "leaf_check"}`, or `null` when no leaf of a supported crop was found. The farmer never selects the crop. `supported_crops` (also in `/api/info`): crops whose leaf diseases are checked, `["tomato"]` in Phase 1; a crop-identification model fills `crop` in Phase 2.

`refer_to_expert` (true / false): the case should go to an extension worker - lesions on at least 25% of the leaf (severity `high`), an urgent disease (late blight), a virus disease (leaf curl, mosaic: severity `not_applicable`) or
a `high` pest level for the photo. `messages` then contains "This looks serious. Show the affected leaves to your local KVK or agriculture officer soon, or call the Kisan Call Centre on 1800-180-1551 (free)." in the display language.

Fields of an `answered` result:

| Field | Content | How to show it |
|---|---|---|
| `disease.name` | disease name in the chosen language (null if not answered) | title |
| `disease.top[0].probability` | confidence 0-1 of the top class | "Model confidence 94%" |
| `disease.urgent` | true for fast-spreading diseases | red "Urgent - act today" |
| `disease.reliability` | `good` / `medium` / `low` | for `low` a message asks to confirm with the KVK |
| `disease.topic` | internal id (`early_blight` ...) | keep it: needed for `/api/ask` |
| `severity.level` | `low` / `medium` / `high` / `unknown`; may be missing | "Estimated spread on this leaf: high (rough estimate)"; hide if `unknown` |
| `pests[]` | one entry per detected insect: `name`, `species`, `species_reliable`, `confidence`, `topic`, `box_xyxy` (pixels of the sent image) | "Insect found: Whitefly"; give the species only if `species_reliable` is true (`name` / `topic` can still be a group such as Caterpillars or Thrips when the species is uncertain); boxes may be drawn on the photo |
| `messages[]` | short sentences the farmer must see (spray rule, uncertainty, KVK) | show all, as notes, above the advice |
| `llama.text` | Llama's explanation, already checked against the sources; **null** when the check rejected it | if not null: an "Advice" card; if null: show nothing (the extracts below are the advice) |
| `advice_blocks[]` | one block per diagnosed topic: `name`, `chunks[]` | main content (below) |
| `quality`, `timings_ms`, `llama.stats` | photo checks and timings | optional "technical details" section |

Each `advice_blocks[].chunks[]` entry is one verified extract:
`section` (`symptoms`, `spread`, `cultural`, `mechanical`, `biological`, `chemical`, `monitoring`, `safety`, ...),
`text`, `source_org`, `source_title`, `url`, and for `section == "chemical"` also `product`, `dose`, `note`.

Display rules (these are safety rules, not style):
- Every extract is shown with its source (`source_org`), e.g. "... yellow margin. [TNAU]".
- Spray advice (`section == "chemical"`) goes in a separate table: product, dose and source exactly as given, with
  `note` under the product. Never shorten or rephrase product names or doses; the `messages` entry about sprays must
  be visible next to the table.
- The Llama text is shown only when `llama.text` is not null, and always together with the extracts.
- In Hindi (`lang=hi`) the names, extracts and messages are already in Hindi; there is no Llama text.

### `POST /api/ask`
Body (JSON): `{"question": "when can I harvest after spraying?", "topic": "late_blight", "lang": "en"}`
(`topic` from the last `disease.topic`, may be null).
Answer: `answer` (Llama's answer, already checked; **null** if rejected), `facts[]` (the extracts used, same fields as
the chunks above), `accepted`, `rejected_reasons`, `stats`. Show `answer` if not null, then always the `facts` with
their sources.

## Moving from the mock to the Pi

- Run on the Pi: `./krishirakshak --root . --serve 8080` (it prints `serving on http://0.0.0.0:8080/`).
- Point the app at `http://<pi-ip>:8080` instead of `http://localhost:8080`. Nothing else changes.
- A native Android/Flutter app needs no extra setting. A web app served from another address needs CORS headers from
  the device server; the current C++ server does not send them yet (it serves its own page). Tell the team if your
  app is a separate web app and they will be added.
- The device handles one request at a time (requests wait); show the waiting state until the answer arrives.
