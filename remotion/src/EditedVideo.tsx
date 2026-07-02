import React from "react";
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import { AudioTrack } from "./AudioTrack";
import { graphics } from "./data/graphics";
import { soundEffects } from "./data/audio";
import { buildTimeline, sourceToComp } from "./data/timeline";
import { graphicRegistry } from "./graphics/registry";
import { GraphicOverlay } from "./GraphicOverlay";
import { theme } from "./theme";

export const SOURCE_VIDEO = "source.mp4"; // lives in remotion/public/

/**
 * Step 3: the composition. The source video (split around any ad breaks) is the
 * background; ads are spliced in; graphics and SFX are overlaid at their
 * timestamps, shifted so anything after an ad lands in the right place.
 *
 * `sourceDurationSec` comes from calculateMetadata in Root.tsx.
 */
export const EditedVideo: React.FC<{ sourceDurationSec: number }> = ({ sourceDurationSec }) => {
  const { fps, durationInFrames } = useVideoConfig();
  const sec = (s: number) => Math.round(s * fps);
  const { videoSegments, adSegments } = buildTimeline(sourceDurationSec);

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Source footage, split around ad breaks */}
      {videoSegments.map((seg, i) => (
        <Sequence
          key={`v${i}`}
          from={sec(seg.fromSec)}
          durationInFrames={Math.max(1, sec(seg.trimAfterSec) - sec(seg.trimBeforeSec))}
        >
          <OffthreadVideo
            src={staticFile(SOURCE_VIDEO)}
            trimBefore={sec(seg.trimBeforeSec)}
            trimAfter={sec(seg.trimAfterSec)}
          />
        </Sequence>
      ))}

      {/* Spliced-in ads */}
      {adSegments.map((ad, i) => (
        <Sequence key={`ad${i}`} from={sec(ad.fromSec)} durationInFrames={Math.max(1, sec(ad.durationSec))}>
          <AbsoluteFill style={{ backgroundColor: "black" }}>
            <OffthreadVideo src={staticFile(ad.src)} />
            {ad.label ? (
              <div
                style={{
                  position: "absolute",
                  top: 32,
                  right: 32,
                  background: theme.accent,
                  color: "#fff",
                  fontFamily: theme.font,
                  fontSize: 30,
                  fontWeight: 800,
                  padding: "10px 22px",
                  borderRadius: 999,
                }}
              >
                {ad.label}
              </div>
            ) : null}
          </AbsoluteFill>
        </Sequence>
      ))}

      {/* Graphic overlays, shifted for any ads before them */}
      {graphics.map((cue, i) => {
        const from = sec(sourceToComp(cue.start));
        const dur = Math.max(1, sec(sourceToComp(cue.end)) - from);
        const Graphic = graphicRegistry[cue.type] as React.FC<typeof cue.props>;
        return (
          <Sequence key={`g${i}`} from={from} durationInFrames={dur}>
            <GraphicOverlay durationInFrames={dur}>
              <Graphic {...cue.props} />
            </GraphicOverlay>
          </Sequence>
        );
      })}

      {/* Sound effects synced to animations */}
      {soundEffects.map((s, i) => (
        <Sequence key={`s${i}`} from={sec(sourceToComp(s.at))}>
          <Audio src={staticFile(s.src)} volume={s.volume ?? 1} />
        </Sequence>
      ))}

      {/* Background music bed */}
      <AudioTrack durationInFrames={durationInFrames} />
    </AbsoluteFill>
  );
};
