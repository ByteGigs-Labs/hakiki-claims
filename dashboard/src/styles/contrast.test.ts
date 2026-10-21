import { readFileSync } from "node:fs";

const css = readFileSync("src/styles/tokens.css", "utf8");
const [light, dark] = css.split("@media (prefers-color-scheme: dark)");

const tokens = (block: string) =>
  Object.fromEntries([...block.matchAll(/--([a-z-]+):\s*(#[0-9a-f]{6});/gi)].map(([, name, value]) => [name, value!]));

const channel = (value: number) => (value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
const luminance = (hex: string) => {
  const [r, g, b] = [1, 3, 5].map((i) => channel(parseInt(hex.slice(i, i + 2), 16) / 255));
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
};
const ratio = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi! + 0.05) / (lo! + 0.05);
};

const TEXT = ["ink", "graphite", "slate", "mute"];
const SURFACES = ["paper", "surface", "lift", "sunk"];

describe.each([
  ["light", tokens(light!)],
  ["dark", { ...tokens(light!), ...tokens(dark!) }],
])("%s theme text contrast", (_, palette) => {
  it.each(TEXT.flatMap((text) => SURFACES.map((surface) => [text, surface])))("%s on %s meets 4.5:1", (text, surface) => {
    expect(ratio(palette[text!]!, palette[surface!]!)).toBeGreaterThanOrEqual(4.5);
  });
});
