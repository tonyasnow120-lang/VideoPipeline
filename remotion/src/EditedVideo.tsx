import React from "react";
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile, useVideoConfig } from "remotion";
import { graphics } from "./data/graphics";
import { graphicRegistry } from "./graphics/registry";
import { GraphicOverlay } from "./GraphicOverlay";

export const SOURCE_VIDEO = "source.mp4"; // lives in remotion/public/

/**
 * Step 3: the composition. The source video is the full-screen background,
 * and each cue in src/data/graphics.ts is overlaid inside a <Sequence> placed
 * at its word-level timestamp.
 */
export const EditedVideo: React.FC = () => {
  const { fps } = useVideoConfig();
  const sec = (s: number) => Math.round(s * fps);

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <OffthreadVideo src={staticFile(SOURCE_VIDEO)} />

      {graphics.map((cue, i) => {
        const from = sec(cue.start);
        const durationInFrames = Math.max(1, sec(cue.end) - from);
        // Registry lookup; props are validated in graphics.ts against the type.
        const Graphic = graphicRegistry[cue.type] as React.FC<typeof cue.props>;
        return (
          <Sequence key={i} from={from} durationInFrames={durationInFrames}>
            <GraphicOverlay durationInFrames={durationInFrames}>
              <Graphic {...cue.props} />
            </GraphicOverlay>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
