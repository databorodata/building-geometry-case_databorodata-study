export function fmt(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  const rounded = Number(value).toFixed(digits);
  return rounded.endsWith(".0") ? rounded.slice(0, -2) : rounded;
}

export function fmtDelta(value, digits = 1) {
  if (value === null || value === undefined) return "—";
  const text = fmt(Math.abs(value), digits);
  if (value > 0) return `+${text}`;
  if (value < 0) return `−${text}`;
  return "0";
}
