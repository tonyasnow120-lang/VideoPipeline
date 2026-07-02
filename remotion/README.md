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

## Use it

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

Then edit **`src/data/graphics.ts`** — add a cue with `start`/`end` (seconds)
and the graphic's content. Everything is type-checked. Built-in graphics:

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
graphic land, and adjust timing/content in `src/data/graphics.ts` — it hot-reloads.
Dimensions and duration come from the source video, so 16:9 and 9:16 both work
automatically.

### 4. Render

```bash
npm run render                   # → out/video.mp4
```

## Background music & sound effects

Configured in **`src/data/audio.ts`**; files go in `public/`.

```ts
// Low-volume bed under the whole video, with fade in/out (loops if shorter):
export const backgroundMusic = { src: "music-lofi.mp3", volume: 0.12 };

// One-shot SFX — set `at` to a graphic's `start` to sync with its animation:
export const soundEffects: SoundEffect[] = [
  { src: "whoosh.mp3", at: 2, volume: 0.8 },
];
```

SFX timestamps use source time (same clock as graphics), so they stay synced
even when ad breaks shift the timeline.

## Ad insertion

Configured in **`src/data/ads.ts`**. An ad break *splices* a clip into the
timeline at a natural pause — everything after it (footage, graphics, SFX)
shifts later automatically.

```ts
export const adBreaks: AdBreak[] = [
  { at: 45, src: "ad-sponsor.mp4", durationInSeconds: 12, label: "Sponsored" },
];
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
3. Use `type: "myGraphic"` in `src/data/graphics.ts`.

Shared branding lives in `src/theme.ts` — change it once, everything follows.

## Project layout

```
remotion/
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
│       ├── graphics.ts     # ← your timeline of graphics
│       ├── audio.ts        # ← background music + sound effects
│       ├── ads.ts          # ← ad breaks spliced at natural pauses
│       ├── timeline.ts     # splices ads, maps source→composition time
│       └── transcript.json # generated by transcribe
└── public/                 # source.mp4, music, sfx, ad clips
```

**Vertical (9:16)**: just feed a 9:16 source; sizing is automatic.
