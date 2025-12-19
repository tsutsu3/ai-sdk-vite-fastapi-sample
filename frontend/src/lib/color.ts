/**
 * Converts a hex color to an RGB object.
 */
export const hexToRgb = (hex: string) => {
  const normalized = hex.replace("#", "");
  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  return { r, g, b };
};

/**
 * Converts RGB values to a hex color string.
 */
export const rgbToHex = (r: number, g: number, b: number) =>
  "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");

/**
 * Produces a monotone variant of a hex color.
 */
export const toMonotone = (hex: string, amount = 0.75): string => {
  const { r, g, b } = hexToRgb(hex);
  const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
  const mix = (c: number) => Math.round(c * (1 - amount) + gray * amount);

  return rgbToHex(mix(r), mix(g), mix(b));
};