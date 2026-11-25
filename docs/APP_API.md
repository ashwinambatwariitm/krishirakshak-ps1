# KrishiRakshak device API

The C++ program on the Raspberry Pi 5 serves the farmer app and a small JSON API over the Pi's own Wi-Fi hotspot
(no internet). The farmer app (app/web) and the Android app (app/android) use only the calls below. The source of
truth is the code: `cpp/src/web_server.hpp` (endpoints), `cpp/src/pipeline.cpp` (answer fields) and
`app/web/js/api.js` (the app's client).

Start (as the Pi service does, `cpp/pi/kr_pi.sh`):

```
./krishirakshak --root . --serve 8080 --web app/web
```

The phone joins the `KrishiRakshak` Wi-Fi and opens `http://10.42.0.1:8080`. Every reply carries
`Access-Control-Allow-Origin: *`, so the Android app (pages inside the APK) can call the Pi. Requests are answered
one at a time, so each model can use all four Cortex-A76 cores.

## Endpoints

| Call | Request | Reply |
|---|---|---|
| `GET /` and other GET paths | | the farmer app from `--web app/web` (`/demo.html` = judge screen with the live log) |
| `GET /basic` | | a minimal built-in page (always available) |
| `GET /api/info` | | models, runtime, languages, knowledge-base version ([info.json](api_examples/info.json)) |
| `POST /api/analyse?lang=en&translate=mr` | body = raw JPEG or PNG bytes (up to 15 MB) | diagnosis, severity, pests, advice ([examples](api_examples/)) |
| `POST /api/ask` | JSON `{"question", "topic", "lang", "translate"}` | Kisan AI answer to a typed question ([example](api_examples/ask_en_harvest_after_spraying.json)) |

## Languages

- `lang=en` with `translate=<code>` is what the app sends for the 10 languages. `translate` is empty for English or
  one of `hi te mr kn ta bn gu or pa` (Hindi, Telugu, Marathi, Kannada, Tamil, Bengali, Gujarati, Odia, Punjabi).
- Names, messages and the verified knowledge-base extracts come in the display language (`display_lang`), with the
  English text kept beside them (`text_en`, `note_en`, and the `en` block).
- Llama writes in English only. Its accepted (grounded and checked) text is translated on the Pi by IndicTrans2
  (CTranslate2 INT8) and returned in `translation`. Spray products and doses are never rewritten or translated.
- `lang=hi` without `translate` is an older path kept for the command line: the Hindi page shows the reviewed Hindi
  extracts and Llama is not run.

## `POST /api/analyse` answer

`status` decides the screen:

| `status` | Meaning | Example |
|---|---|---|
| `answered` | a tomato disease above the 0.85 confidence threshold, or insects found (also on other plants) | [early blight](api_examples/analyse_en_early_blight.json), [healthy](api_examples/analyse_en_healthy_leaf.json), [aphids](api_examples/analyse_en_pest_aphids.json), [Marathi](api_examples/analyse_mr_early_blight.json) |
| `uncertain` | a tomato leaf, but no class reaches the threshold: no disease is named | [uncertain](api_examples/analyse_en_uncertain.json) (a leaf-mould photo, a disease outside the 6 classes) |
| `not_tomato` | not a tomato plant and no insect found | [not tomato](api_examples/analyse_en_not_tomato.json) |
| `retake_photo` | photo too small, too dark, too bright or blurred (`quality.issues`) | [retake](api_examples/analyse_en_retake_photo.json) |

Fields (a `retake_photo` answer has only `status`, `messages`, `quality`, `timings_ms` and the language fields):

| Field | Content |
|---|---|
| `messages` | short texts for the farmer (not a tomato plant, uncertain, confirm with an expert, spray safety) |
| `quality` | `ok`, `issues`, `metrics` (brightness, sharpness, width, height) of the OpenCV photo check |
| `leaf_check` | `is_tomato_leaf`, `p_other`, `threshold`, `model` of the tomato-leaf check |
| `crop` | `{"name": "tomato", "source": "leaf_check"}` or null, and `supported_crops` |
| `disease` | `answered`, `name`, `topic`, `top` (classes with probabilities), `reliability`, `urgent`, `not_tomato_leaf` |
| `severity` | for a diagnosed disease: `level` = `low` / `moderate` / `high` (lesions under 10%, 10-25%, at least 25% of the leaf), `not_applicable` (virus diseases) or `unknown` (no leaf found), with `lesion_share`, `leaf_share`, `method`, `model`, `validated` |
| `pests` | one entry per insect: `name`, `species`, `topic` (advice group), `confidence`, `box_xyxy` (pixels of the sent photo), `species_reliable` |
| `pest_severity` | one entry per pest topic: `level`, `count`, `group`, `basis` (`insects_in_this_photo`), the published scouting method (`scouting`) and threshold |
| `refer_to_expert` | true for an urgent disease (late blight), a virus disease, severity `high` or a `high` pest level: the app shows the KVK / Kisan Call Centre alert |
| `advice_blocks` | per topic: `name`, `topic`, `chunks` = verified extracts with `section` (symptoms, spread, cultural, biological, chemical, safety), `text`, `product`, `dose`, `note` and the source (`source_org`, `source_title`, `url`) |
| `llama` | `text` (accepted sentences) or null, `accepted`, `grounded_sentences`, `dropped_sentences`, `rejected_reasons`, `raw_text`, `stats` (tokens, tokens/s, time to first token) |
| `translation` | null, or `lang`, `text`, `sentences` (each with `english`, `text`, `ok`), `withheld`, `reviewed` (false: machine translation), `ms` |
| `en` | the English names, messages and advice when another display language is used |
| `lang`, `display_lang` | requested language and the language of the shown texts |
| `device` | CPU temperature at start and end, CPU frequency, `llama_skipped_hot` (Llama is skipped when the CPU is too hot) |
| `timings_ms` | per stage: quality, leaf_check, disease, pest, vision_wall, severity, retrieval, llama, translation, total |
| `demo_log` | step-by-step log for the judge screen (only in builds with `KR_DEMO_LOGS`, as in the examples) |

When Llama's text fails the grounding check (in the final test this happened for the healthy leaf), when a topic
has too few source extracts (Llama is then not run) or when the CPU is too hot, `llama.text` is null and the
verified extracts are the advice. `rejected_reasons` says why.

Time on the Pi 5 (final test, 23-24 Nov 2026, [results/e2e_pi5](../results/e2e_pi5/README.md)): whole answer with
Llama and translation median 8.36 s (4.72-20.13 s), vision 114 ms, "not a tomato plant" 118 ms. The app waits up to
60 s.

## `POST /api/ask` answer

`question`, `answer` (accepted text or null), `accepted`, `facts` (the verified extracts used), `raw_text`,
`dropped_sentences`, `rejected_reasons`, `stats` and `translation` (when `translate` is set). The same grounding
check applies as for photos: the [example](api_examples/ask_en_harvest_after_spraying.json) shows a rejected answer,
because Llama claimed a 5-day waiting period that no source extract gives. The app then shows the source extracts.

## Examples and the mock server

[api_examples/](api_examples/) holds real answers of the Pi: the analyse answers are from the final end-to-end test
(`_seconds`, the client-side time, removed), `info.json`, the uncertain answer and the ask answer were captured from
the Pi on 25 Nov 2026 with the same build. For work on the app without a Pi, `python tools/mock_api_server.py`
serves app/web and answers with these files (`?example=pest`, `uncertain`, `not_tomato`, `retake`, `healthy`, or
any `translate` value for the Marathi answer).
