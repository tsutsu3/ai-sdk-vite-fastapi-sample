import { toMonotone } from "@/lib/color";

/**
 * Base palette used by the sidebar avatar.
 *
 * These colors are used to generate consistent user avatar accents.
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
 *
 * Used when the UI is set to a muted palette.
 */
export const monotoneAvatarColors = avatarColors.map((color) =>
  toMonotone(color, 0.65),
);
