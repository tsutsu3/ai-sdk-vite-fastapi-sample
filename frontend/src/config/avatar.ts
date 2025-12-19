import { toMonotone } from "@/lib/color";

/**
 * Base palette used by the sidebar avatar.
 */
export const avatarColors = [
  "#92A1C6",
  "#146A7C",
  "#F0AB3D",
  "#C271B4",
  "#C20D90",
];

/**
 * Monotone avatar colors for the neutral sidebar look.
 */
export const monotoneAvatarColors = avatarColors.map((color) =>
  toMonotone(color, 0.65)
);