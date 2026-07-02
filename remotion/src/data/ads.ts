import data from "./ads.json";

/**
 * Ad insertion at natural break points. The breaks live in ads.json —
 * edited via the GUI (npm run gui) or by hand.
 *
 * Each break SPLICES an ad clip into the timeline at `at` seconds (in source
 * time), pushing the rest of the video — and every graphic after it — later by
 * the ad's length. Put your ad clip in remotion/public/ and give its length in
 * `durationInSeconds` (kept explicit so Studio opens even before the file exists).
 *
 * Example JSON entry:
 *   { "at": 45, "src": "ad-sponsor.mp4", "durationInSeconds": 12, "label": "Sponsored" }
 */
export type AdBreak = {
  at: number; // seconds into the SOURCE video (a natural pause)
  src: string; // filename in remotion/public/, e.g. "ad-sponsor.mp4"
  durationInSeconds: number;
  label?: string; // optional caption shown while the ad plays
};

export const adBreaks = data as unknown as AdBreak[];
