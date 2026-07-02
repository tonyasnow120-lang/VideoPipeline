import React from "react";
import { AbsoluteFill } from "remotion";
import { theme } from "../theme";

/**
 * Dimmed, blurred full-screen backdrop used by "takeover" graphics
 * (lists, stats, comparisons, flows). Overlay-style graphics such as a
 * lower third deliberately do NOT use this — they sit on top of the video.
 */
export const Backdrop: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: theme.bg, backdropFilter: "blur(6px)" }}>
    {children}
  </AbsoluteFill>
);
