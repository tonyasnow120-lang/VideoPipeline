import { GraphicPropsMap, GraphicType } from "../graphics/registry";
import cues from "./graphics.json";

/**
 * Step 2 output: which graphic shows, when, and with what content.
 *
 * The cues themselves live in graphics.json so both the GUI (npm run gui)
 * and Remotion Studio share them — saving in the GUI hot-reloads Studio.
 * You can still edit graphics.json by hand; `start`/`end` are seconds in the
 * source video, taken from the word-level transcript
 * (`npm run find -- "some phrase"` or the GUI's transcript panel).
 */
export type GraphicCue<T extends GraphicType = GraphicType> = {
  [K in GraphicType]: {
    type: K;
    start: number;
    end: number;
    props: GraphicPropsMap[K];
  };
}[T];

export const graphics = cues as unknown as GraphicCue[];
