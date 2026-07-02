import { BulletList, BulletListProps } from "./BulletList";
import { ComparisonCard, ComparisonCardProps } from "./ComparisonCard";
import { LowerThird, LowerThirdProps } from "./LowerThird";
import { ProcessFlow, ProcessFlowProps } from "./ProcessFlow";
import { StatCallout, StatCalloutProps } from "./StatCallout";

/**
 * Maps a graphic `type` string (used in src/data/graphics.ts) to its
 * component. Add a new graphic by creating a component and registering it here.
 */
export const graphicRegistry = {
  bulletList: BulletList,
  comparison: ComparisonCard,
  stat: StatCallout,
  processFlow: ProcessFlow,
  lowerThird: LowerThird,
} as const;

export type GraphicType = keyof typeof graphicRegistry;

// Props for each graphic type, so src/data/graphics.ts is type-checked.
export type GraphicPropsMap = {
  bulletList: BulletListProps;
  comparison: ComparisonCardProps;
  stat: StatCalloutProps;
  processFlow: ProcessFlowProps;
  lowerThird: LowerThirdProps;
};
