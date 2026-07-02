import { adBreaks } from "./ads";

/**
 * Turns the source video + ad breaks into a concrete timeline.
 *
 * All values are in seconds. Ad breaks splice extra time into the middle, so
 * anything after a break shifts later. `sourceToComp` maps a source-time
 * moment (used by graphics and SFX) to its position in the final composition.
 */

export type VideoSegment = {
  fromSec: number; // where this segment starts in the FINAL composition
  trimBeforeSec: number; // where to start playing within the SOURCE
  trimAfterSec: number; // where to stop playing within the SOURCE
};

export type AdSegment = {
  fromSec: number;
  durationSec: number;
  src: string;
  label?: string;
};

const sortedBreaks = () => [...adBreaks].sort((a, b) => a.at - b.at);

export function buildTimeline(sourceDurationSec: number) {
  const breaks = sortedBreaks().filter((b) => b.at > 0 && b.at < sourceDurationSec);
  const videoSegments: VideoSegment[] = [];
  const adSegments: AdSegment[] = [];

  let sourceCursor = 0;
  let compCursor = 0;

  for (const b of breaks) {
    // Source footage up to the break point.
    videoSegments.push({
      fromSec: compCursor,
      trimBeforeSec: sourceCursor,
      trimAfterSec: b.at,
    });
    compCursor += b.at - sourceCursor;
    sourceCursor = b.at;

    // The spliced-in ad.
    adSegments.push({
      fromSec: compCursor,
      durationSec: b.durationInSeconds,
      src: b.src,
      label: b.label,
    });
    compCursor += b.durationInSeconds;
  }

  // Remaining source footage after the last break.
  videoSegments.push({
    fromSec: compCursor,
    trimBeforeSec: sourceCursor,
    trimAfterSec: sourceDurationSec,
  });
  compCursor += sourceDurationSec - sourceCursor;

  return { videoSegments, adSegments, totalSec: compCursor };
}

/** Map a source-time moment to composition time (accounts for earlier ads). */
export function sourceToComp(sourceSec: number): number {
  let added = 0;
  for (const b of sortedBreaks()) {
    if (b.at <= sourceSec) added += b.durationInSeconds;
  }
  return sourceSec + added;
}
