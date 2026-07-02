import React from "react";
import { Composition, staticFile } from "remotion";
import { getVideoMetadata } from "@remotion/media-utils";
import { EditedVideo, SOURCE_VIDEO } from "./EditedVideo";
import { buildTimeline } from "./data/timeline";

const FPS = 30;

/**
 * Dimensions come from the source video (so 16:9 and 9:16 both work with no
 * manual sizing) and duration is the source length plus any spliced-in ads.
 * If the source is missing (e.g. first run before you've added a video), fall
 * back to a 1080p landscape placeholder so Studio still opens.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="EditedVideo"
      component={EditedVideo}
      durationInFrames={FPS * 10}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{ sourceDurationSec: 10 }}
      calculateMetadata={async () => {
        try {
          const meta = await getVideoMetadata(staticFile(SOURCE_VIDEO));
          const { totalSec } = buildTimeline(meta.durationInSeconds);
          return {
            durationInFrames: Math.max(1, Math.round(totalSec * FPS)),
            width: meta.width,
            height: meta.height,
            fps: FPS,
            props: { sourceDurationSec: meta.durationInSeconds },
          };
        } catch {
          // No source video yet — keep the placeholder so Studio still opens.
          return {
            durationInFrames: FPS * 10,
            width: 1920,
            height: 1080,
            fps: FPS,
            props: { sourceDurationSec: 10 },
          };
        }
      }}
    />
  );
};
