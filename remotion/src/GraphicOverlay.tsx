import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * Wraps every graphic with a consistent fade in/out. A graphic lives inside a
 * <Sequence>, so `useCurrentFrame` here is 0 at the moment the graphic appears
 * and counts up over its lifetime. The dimmed backdrop (for takeover graphics)
 * lives in Backdrop.tsx, so overlay graphics like a lower third can skip it.
 */
export const GraphicOverlay: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
}> = ({ durationInFrames, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fade = Math.round(fps * 0.35); // ~0.35s fade on each edge

  const opacity = interpolate(
    frame,
    [0, fade, durationInFrames - fade, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};
