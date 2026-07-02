import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Backdrop } from "./Backdrop";
import { theme } from "../theme";

export type ProcessFlowProps = {
  title?: string;
  steps: string[];
};

/** Numbered steps connected by arrows — each step pops in one after another. */
export const ProcessFlow: React.FC<ProcessFlowProps> = ({ title, steps }) => {
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
              fontSize: 68,
              fontWeight: 800,
              margin: "0 0 44px",
              textAlign: "center",
            }}
          >
            {title}
          </h1>
        ) : null}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "stretch",
            justifyContent: "center",
            gap: 20,
          }}
        >
          {steps.map((step, i) => {
            const enter = spring({ frame: frame - i * 8, fps, config: { damping: 200 } });
            return (
              <React.Fragment key={i}>
                <div
                  style={{
                    flex: "1 1 0",
                    minWidth: 220,
                    background: theme.card,
                    borderRadius: theme.radius,
                    padding: "32px 26px",
                    textAlign: "center",
                    transform: `translateY(${interpolate(enter, [0, 1], [40, 0])}px)`,
                    opacity: enter,
                    boxShadow: "0 16px 44px rgba(0,0,0,0.35)",
                    borderTop: `6px solid ${theme.accent}`,
                  }}
                >
                  <div
                    style={{
                      color: theme.accentSoft,
                      fontSize: 30,
                      fontWeight: 800,
                      marginBottom: 12,
                    }}
                  >
                    STEP {i + 1}
                  </div>
                  <div style={{ color: theme.text, fontSize: 38, fontWeight: 600 }}>{step}</div>
                </div>
                {i < steps.length - 1 ? (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      color: theme.accentSoft,
                      fontSize: 56,
                      fontWeight: 800,
                      opacity: enter,
                    }}
                  >
                    →
                  </div>
                ) : null}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </Backdrop>
  );
};
