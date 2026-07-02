# Video Graphics Pipeline (Remotion + FFmpeg + Whisper)

Overlay animated, on-brand graphics onto a talking-head video — placed exactly
when you say the thing they illustrate. This is the pipeline from the walkthrough:

1. **Transcribe** — FFmpeg extracts the audio, OpenAI Whisper returns a
   word-level timestamped transcript.
2. **Map graphics to speech** — you pick moments (lists, stats, comparisons)
   and use the word timings to place each graphic.
3. **Build** — the source video is the background; graphics are React
   components layered on top at the right timestamps via `<Sequence>`.
4. **Preview** — Remotion Studio lets you scrub the timeline and tweak.
5. **Render** — the Remotion CLI renders the final MP4.

Everything is code, so it's versioned and the graphic components are reusable
across videos.

## Prerequisites

- **Node.js 20.6+** (uses `--env-file`; 22+ recommended) — `node -v`
- **FFmpeg** on your PATH — `ffmpeg -version`
  - macOS: `brew install ffmpeg` · Debian/Ubuntu: `sudo apt install ffmpeg`
  - Windows: https://ffmpeg.org/download.html
- **OpenAI API key** with Whisper access — https://platform.openai.com/api-keys

## Setup

```bash
cd remotion
npm install
cp .env.example .env      # then paste your real OPENAI_API_KEY
```

## Easiest way: the GUI

**Windows:** just double-click **`Pipeline.bat`** in the repo root. It checks
for Node/FFmpeg, installs dependencies on first run, prompts for your API key
if `.env` doesn't exist yet, then starts the dashboard and opens your browser.
(Right-click → Create shortcut to put it on your Desktop.)

**Mac/Linux (or any terminal):**

```bash
npm run gui
```

Open **http://localhost:4000**. The dashboard walks you through the whole
pipeline with no terminal or code editing:

1. **Upload** your video (saved as `public/source.mp4`) and any music/SFX/ad files
2. **Transcribe** with one click
3. **Find moments** — search for a phrase, or click words in the transcript to
   select a time range
4. **Graphics** — add/edit graphics with forms; “Use selection” copies the
   timestamps from step 3
5. **Music, SFX & ad breaks** — simple form fields
6. **Preview** — launches Remotion Studio (http://localhost:3000); saving in
   the GUI hot-reloads it
7. **Render** — one click, then download `video.mp4`

The GUI reads and writes `src/data/*.json` — the same files Studio uses — so
you can mix GUI editing and hand editing freely.

## Same thing from the command line

### 1. Add your video and transcribe

Drop your recording in `public/source.mp4` (any FFmpeg-readable format works —
just name it `source.mp4`, or pass a path):

```bash
npm run transcribe               # reads public/source.mp4
# or: npm run transcribe -- public/my-clip.mov
```

This writes `src/data/transcript.json` with `{ word, start, end }` for every word.

### 2. Find timestamps and map graphics

Locate where you say something:

```bash
npm run find -- "the process"
#  Found "the process" 1 time(s):
#    start 2.14s  →  end 2.73s
```

Then edit **`src/data/graphics.json`** — add a cue with `start`/`end` (seconds)
and the graphic's content. Built-in graphics:

| `type`        | Component          | Props | Style |
|---------------|--------------------|-------|-------|
| `bulletList`  | `BulletList`       | `{ title?, items[] }` | takeover (dims video) |
| `stat`        | `StatCallout`      | `{ value, label }` | takeover |
| `comparison`  | `ComparisonCard`   | `{ title?, left, right }` | takeover |
| `processFlow` | `ProcessFlow`      | `{ title?, steps[] }` | takeover |
| `lowerThird`  | `LowerThird`       | `{ title, subtitle? }` | overlay (video stays visible) |

### 3. Preview in Studio

```bash
npm run studio
```

Opens Remotion Studio (http://localhost:3000). Scrub the timeline, watch each
graphic land, and adjust timing/content in `src/data/graphics.json` — it hot-reloads.
Dimensions and duration come from the source video, so 16:9 and 9:16 both work
automatically.

### 4. Render

```bash
npm run render                   # → out/video.mp4
```

## Background music & sound effects

Configured in **`src/data/audio.json`** (via the GUI or by hand); files go in
`public/`.

```json
{
  "backgroundMusic": { "src": "music-lofi.mp3", "volume": 0.12 },
  "soundEffects": [{ "src": "whoosh.mp3", "at": 2, "volume": 0.8 }]
}
```

Music loops under the whole video with a fade in/out. For SFX, set `at` to a
graphic's `start` to sync with its animation.

SFX timestamps use source time (same clock as graphics), so they stay synced
even when ad breaks shift the timeline.

## Ad insertion

Configured in **`src/data/ads.json`** (via the GUI or by hand). An ad break
*splices* a clip into the timeline at a natural pause — everything after it
(footage, graphics, SFX) shifts later automatically.

```json
[{ "at": 45, "src": "ad-sponsor.mp4", "durationInSeconds": 12, "label": "Sponsored" }]
```

- `at` is seconds into the *source* video — pick a sentence boundary
  (`npm run find` helps locate one).
- Put the ad clip in `public/` and state its length in `durationInSeconds`.
- The optional `label` renders a small badge in the corner while the ad plays.

## Adding a new graphic type

1. Create `src/graphics/MyGraphic.tsx` exporting a component + its props type.
   Wrap it in `<Backdrop>` (see `ProcessFlow.tsx`) for a takeover graphic, or
   skip the backdrop for an overlay like `LowerThird.tsx`.
2. Register it in `src/graphics/registry.ts` (add to `graphicRegistry` and
   `GraphicPropsMap`).
3. Use `type: "myGraphic"` in `src/data/graphics.json`. (To make it editable
   in the GUI too, add a matching entry to `GRAPHIC_DEFS` in `gui/index.html`.)

Shared branding lives in `src/theme.ts` — change it once, everything follows.

## Project layout

```
remotion/
├── gui/
│   ├── server.mjs          # npm run gui → dashboard at localhost:4000
│   └── index.html          # the dashboard UI
├── scripts/
│   ├── transcribe.mjs      # FFmpeg + Whisper → transcript.json
│   └── find-phrase.mjs     # locate a phrase's timestamp
├── src/
│   ├── index.ts            # registerRoot
│   ├── Root.tsx            # composition + size/duration from source (+ ads)
│   ├── EditedVideo.tsx     # video segments + ads + graphics + audio
│   ├── GraphicOverlay.tsx  # shared fade wrapper
│   ├── AudioTrack.tsx      # background music bed
│   ├── theme.ts            # branding tokens
│   ├── graphics/           # reusable graphic components + registry
│   │   └── Backdrop.tsx    # dimmed backdrop for takeover graphics
│   └── data/
│       ├── graphics.json   # ← your timeline of graphics (GUI-editable)
│       ├── audio.json      # ← background music + sound effects (GUI-editable)
│       ├── ads.json        # ← ad breaks spliced at natural pauses (GUI-editable)
│       ├── timeline.ts     # splices ads, maps source→composition time
│       └── transcript.json # generated by transcribe
└── public/                 # source.mp4, music, sfx, ad clips
```

**Vertical (9:16)**: just feed a 9:16 source; sizing is automatic.
