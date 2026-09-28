# The Night Studio — how your brain makes dreams

A 59-second hand-made paper-collage animated short (1920×1080, 24 fps, H.264 + AAC).

**Final film:** `output/animated-short-final.mp4`

## What's in the film

| Time | Beat | Narration |
|---|---|---|
| 0–7.8s | Night village → push through the lit window → bedroom; a thought-cloud "movie" starts | "Tonight, while you sleep, your brain will make a movie… starring you." |
| 7.8–14.7s | A pencil draws a night of sleep cycles; rubber stamps mark each REM period; dreams bubble up | "Every ninety minutes or so, you drift into REM sleep, when the most vivid dreams happen." |
| 14.7–32.4s | Paper tears open onto the "brain studio": brainstem worker flips the REM switch, signals race up, the seahorse **hippocampus** files memory scraps, the almond **amygdala** lights its lantern, the **prefrontal cortex** director dozes off | "A switch in your brainstem flips on…" → "…dozes off." |
| 32.4–37.3s | Curtains open on the dream: the old school floating at sea | "So nobody asks why your school is floating at sea." |
| 37.3–41.8s | Pull back into the bedroom; the marionette strings go slack | "Meanwhile, your muscles go limp, so you don't act it out." |
| 41.8–49.2s | Theory board: scientists debate; memories get sorted; a torn heart is taped back together | "Scientists still debate why we dream. It may help sort memories and soothe feelings." |
| 49.2–59s | Iris into morning; the dream flies out of the window, toast pops; one paper fish is left in your hand | "Then morning comes… and most of the movie is gone by breakfast." |

Science notes: sleep cycles are roughly 90 minutes, and REM periods get longer toward morning while deep sleep shrinks (the chart shows both). REM is switched on by circuits in the pons, part of the brainstem. During REM the amygdala is highly active and the dorsolateral prefrontal cortex is relatively quiet. Brainstem circuits cause REM muscle atonia. Most dreams are forgotten. Dreaming's purpose is still debated, so the film says "may".

## How it was made (all code in `src/`)

* `engine.py` — the collage engine, built on Skia and NumPy. It generates procedural paper textures (fibres, tooth, mottling) and applies them with an overlay blend. Pieces get hand-cut or torn edges, plus a soft cast shadow and a contact shadow. Ink and pencil lines boil at 8 fps, crayon grain fills add colour, and there is washi tape and handwritten text with per-letter jitter. It also provides a parallax camera and the post pass (vignette, grain, exposure flicker).
* `chars.py`, `props.py` — the characters and props, all drawn in code: the dreamer, a person rig, the seahorse, the almond, the cabinet, memory scraps, the lever panel, the desk, the school-boat, the cat, fish, clouds and moon.
* `scenes.py`, `scenes2.py`, `scenes3.py` — the choreography. Every cue is keyed to phrase timings measured from the narration (`build/timeline.json`).
* `film.py` — the master timeline and handmade transitions: window push-in, paper tear, theatre curtains, pull-back into the thought cloud, page slide, and torn-paper iris.
* `render.py` — parallel frame rendering piped straight into ffmpeg.
* `audio.py` — all sound effects are synthesized in code (paper, pencil, stamps, chimes, sea, crickets, birds and more). It places them on the same cue times, pans them to where they happen on screen, ducks the music under the voice, and masters to -16 LUFS.
* `build_vo.py` / `vo_analyze.py` — cut the single narration take into lines, space them on the timeline, and export the cue sheet.
* `orclient.py` — OpenRouter client with a local spending log and budget guard (`build/openrouter_costs.jsonl`).
* `review.py` — sends a low-res copy to a cheap multimodal model for an automatic "director's notes" QA pass.

### Assets and services
* Narration: OpenRouter `openai/gpt-audio`, voice "ash". Picked from 9 test takes, each rated by Gemini listening to the audio.
* Music: OpenRouter `google/lyria-3-pro-preview`. An original instrumental cue whose bloom lands on the dream.
* Fonts: Kalam, Caveat and Caveat Brush (Google Fonts, SIL OFL), in `assets/fonts/`.
* Everything visual is procedural. No stock footage, images or local AI models were used.

### OpenRouter spend: $0.42 of the $5 cap
| What | Model | Cost |
|---|---|---|
| Voice casting: 9 short test takes | gpt-audio-mini and gpt-audio | $0.044 |
| Final narration (one take) | openai/gpt-audio (ash) | $0.070 |
| Music: 1 wasted non-streaming call, 1 test clip, 1 final track | google/lyria-3-* | $0.200 |
| QA "ears and eyes": voice casting, narration, music, mix (×2), video reviews (×4) | google/gemini-3.8-flash | $0.111 |

Per-call log: `docs/openrouter_costs.jsonl`. `src/orclient.py` also enforces its own $1.50 working budget.

### Quality control
* Automated checks: no decode errors, no black or frozen segments, and exactly 1416 frames (59.0s at 24 fps). The mix sits at -16.4 LUFS integrated with a true peak of -1.9 dBFS and no clipping. The final automated review scored it 9.2/10.
* Gemini listened to and watched review copies over several rounds. Every issue it found was either fixed or checked by hand against the frames and set aside when it wasn't real. Examples: a clipped label, a hidden "SCHOOL" sign, a black band during a push-in, a harsh lever sound, sea noise masking a line, and a morning scene that ended on "sweet dreams".

### Rebuild
```bash
pip install numpy scipy skia-python pillow pyloudnorm && apt-get install ffmpeg
./make_film.sh          # renders the master, builds the mix, encodes output/animated-short-final.mp4 (no API calls)
```
To regenerate the voice or score, run `python3 src/gen_narration.py` and `python3 src/gen_music.py`. These call OpenRouter and read the key from `.env`, which is not committed.
