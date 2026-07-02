import React from "react";
import { Composition, getInputProps, staticFile } from "remotion";
import { getVideoMetadata } from "@remotion/media-utils";
import { EditedVideo, SOURCE_VIDEO } from "./EditedVideo";

const FPS = 30;

/**
 * Dimensions and duration are derived from the source video itself via
 * calculateMetadata, so the same composition handles both 16:9 and 9:16 —
 * no manual width/height. If the source is missing (e.g. first run before
 * you've added a video), fall back to a 1080p landscape placeholder.
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
      calculateMetadata={async () => {
        try {
          const meta = await getVideoMetadata(staticFile(SOURCE_VIDEO));
          return {
            durationInFrames: Math.max(1, Math.round(meta.durationInSeconds * FPS)),
            width: meta.width,
            height: meta.height,
            fps: FPS,
          };
        } catch {
          // No source video yet — keep the placeholder so Studio still opens.
          return { durationInFrames: FPS * 10, width: 1920, height: 1080, fps: FPS };
        }
      }}
    />
  );
};
