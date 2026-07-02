import React from "react";
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { theme } from "../theme";

export type StatCalloutProps = {
  value: string;
  label: string;
};

/** A single big number that pops in — good for a stat you call out. */
export const StatCallout: React.FC<StatCalloutProps> = ({ value, label }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 12, mass: 0.6 } });

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: theme.font,
      }}
    >
      <div
        style={{
          background: theme.card,
          borderRadius: theme.radius,
          padding: "64px 96px",
          textAlign: "center",
          transform: `scale(${interpolate(pop, [0, 1], [0.6, 1])})`,
          opacity: Math.min(1, pop * 1.4),
          boxShadow: "0 24px 60px rgba(0,0,0,0.4)",
          border: `2px solid ${theme.accentSoft}`,
        }}
      >
        <div style={{ color: theme.accentSoft, fontSize: 160, fontWeight: 900, lineHeight: 1 }}>
          {value}
        </div>
        <div style={{ color: theme.textDim, fontSize: 44, fontWeight: 600, marginTop: 12 }}>
          {label}
        </div>
      </div>
    </div>
  );
};
