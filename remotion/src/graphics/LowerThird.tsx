import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { theme } from "../theme";

export type LowerThirdProps = {
  title: string;
  subtitle?: string;
};

/**
 * A name/title bar anchored to the lower-left third. Unlike takeover graphics
 * it does NOT dim the video — it slides in over it, so the speaker stays visible.
 */
export const LowerThird: React.FC<LowerThirdProps> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 200 } });

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "flex-start",
        padding: theme.pad,
        fontFamily: theme.font,
      }}
    >
      <div
        style={{
          transform: `translateX(${interpolate(enter, [0, 1], [-120, 0])}px)`,
          opacity: enter,
          display: "flex",
          flexDirection: "column",
          borderLeft: `10px solid ${theme.accent}`,
          background: theme.card,
          borderRadius: `0 ${theme.radius}px ${theme.radius}px 0`,
          padding: "26px 40px",
          boxShadow: "0 18px 50px rgba(0,0,0,0.4)",
        }}
      >
        <span style={{ color: theme.text, fontSize: 56, fontWeight: 800, lineHeight: 1.1 }}>
          {title}
        </span>
        {subtitle ? (
          <span style={{ color: theme.accentSoft, fontSize: 34, fontWeight: 600, marginTop: 6 }}>
            {subtitle}
          </span>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
