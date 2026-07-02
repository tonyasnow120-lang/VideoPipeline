import React from "react";
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { Backdrop } from "./Backdrop";
import { theme } from "../theme";

export type ComparisonCardProps = {
  title?: string;
  left: { heading: string; points: string[] };
  right: { heading: string; points: string[] };
};

const Column: React.FC<{
  heading: string;
  points: string[];
  accent: string;
  progress: number;
  dir: number;
}> = ({ heading, points, accent, progress, dir }) => (
  <div
    style={{
      flex: 1,
      background: theme.card,
      borderRadius: theme.radius,
      padding: 40,
      transform: `translateX(${interpolate(progress, [0, 1], [dir * 80, 0])}px)`,
      opacity: progress,
      boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
    }}
  >
    <div
      style={{
        color: "#fff",
        background: accent,
        borderRadius: 14,
        padding: "14px 22px",
        fontSize: 40,
        fontWeight: 800,
        textAlign: "center",
        marginBottom: 28,
      }}
    >
      {heading}
    </div>
    {points.map((p, i) => (
      <div
        key={i}
        style={{
          color: theme.text,
          fontSize: 36,
          fontWeight: 500,
          padding: "12px 0",
          borderBottom: i < points.length - 1 ? "1px solid rgba(255,255,255,0.08)" : "none",
        }}
      >
        {p}
      </div>
    ))}
  </div>
);

/** Two cards side by side — a vs. b, before vs. after, etc. */
export const ComparisonCard: React.FC<ComparisonCardProps> = ({ title, left, right }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame, fps, config: { damping: 200 } });

  return (
    <Backdrop>
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: theme.pad * 1.4,
        boxSizing: "border-box",
        fontFamily: theme.font,
      }}
    >
      {title ? (
        <h1
          style={{
            color: theme.text,
            fontSize: 68,
            fontWeight: 800,
            margin: "0 0 36px",
            textAlign: "center",
          }}
        >
          {title}
        </h1>
      ) : null}
      <div style={{ display: "flex", gap: 32 }}>
        <Column heading={left.heading} points={left.points} accent={theme.bad} progress={progress} dir={-1} />
        <Column heading={right.heading} points={right.points} accent={theme.good} progress={progress} dir={1} />
      </div>
    </div>
    </Backdrop>
  );
};
