import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "./theme";

/**
 * Wraps every graphic with a consistent dimmed backdrop + fade in/out, so
 * individual graphic components only worry about their own content.
 * A graphic lives inside a <Sequence>, so `useCurrentFrame` here is 0 at the
 * moment the graphic appears and counts up over its lifetime.
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

  return (
    <AbsoluteFill style={{ opacity, background: theme.bg, backdropFilter: "blur(6px)" }}>
      {children}
    </AbsoluteFill>
  );
};
