import React from "react";
import { Audio, interpolate, staticFile, useVideoConfig } from "remotion";
import { backgroundMusic } from "./data/audio";

/**
 * Background music bed for the whole composition, at a low fixed volume with
 * a short fade in and out. Renders nothing if no music is configured.
 */
export const AudioTrack: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const { fps } = useVideoConfig();
  if (!backgroundMusic) return null;

  const fade = Math.round(fps * 1.0);
  const base = backgroundMusic.volume;

  return (
    <Audio
      src={staticFile(backgroundMusic.src)}
      loop
      volume={(f) =>
        interpolate(
          f,
          [0, fade, durationInFrames - fade, durationInFrames],
          [0, base, base, 0],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        )
      }
    />
  );
};
