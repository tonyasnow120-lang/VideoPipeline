import data from "./audio.json";

/**
 * Background music (with volume control) and sound effects synced to
 * animations. The values live in audio.json — edited via the GUI
 * (npm run gui) or by hand. All files live in remotion/public/.
 *
 * Timestamps are in SOURCE time (seconds) — the same clock you use for
 * graphics — so an SFX `at` can match a graphic's `start`. They're shifted
 * automatically if ad breaks push the timeline later.
 */

export type BackgroundMusic = { src: string; volume: number };

export type SoundEffect = {
  src: string; // filename in remotion/public/, e.g. "whoosh.mp3"
  at: number; // source-time seconds — align with a graphic's `start` to sync
  volume?: number; // 0..1, defaults to 1
};

// Low-volume bed under the whole video; null for no music.
// Example JSON: { "backgroundMusic": { "src": "music-lofi.mp3", "volume": 0.12 } }
export const backgroundMusic = data.backgroundMusic as unknown as BackgroundMusic | null;

// One-shot SFX. Example JSON entry: { "src": "whoosh.mp3", "at": 2, "volume": 0.8 }
export const soundEffects = data.soundEffects as unknown as SoundEffect[];
