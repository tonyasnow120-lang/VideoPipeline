import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop } from "./Backdrop";
import { theme } from "../theme";

export type BulletListProps = {
  title?: string;
  items: string[];
};

/** A full-screen animated list — items stagger in one after another. */
export const BulletList: React.FC<BulletListProps> = ({ title, items }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

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
            fontSize: 76,
            fontWeight: 800,
            margin: "0 0 40px",
            letterSpacing: -1,
          }}
        >
          {title}
        </h1>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {items.map((item, i) => {
          const enter = spring({
            frame: frame - i * 6,
            fps,
            config: { damping: 200 },
          });
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 28,
                background: theme.card,
                borderRadius: theme.radius,
                padding: "26px 34px",
                transform: `translateX(${interpolate(enter, [0, 1], [-60, 0])}px)`,
                opacity: enter,
                boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
              }}
            >
              <div
                style={{
                  minWidth: 56,
                  height: 56,
                  borderRadius: 16,
                  background: theme.accent,
                  color: "#fff",
                  fontSize: 30,
                  fontWeight: 800,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {i + 1}
              </div>
              <span style={{ color: theme.text, fontSize: 44, fontWeight: 600 }}>
                {item}
              </span>
            </div>
          );
        })}
      </div>
    </div>
    </Backdrop>
  );
};
