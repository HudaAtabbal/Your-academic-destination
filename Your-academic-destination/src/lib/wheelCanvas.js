/**
 * wheelCanvas.js — draws the wheel face onto a canvas.
 *
 * Ported from docs/dashboard-reference/wheel-v4.html (renderWheelFace, lines
 * 290-308, and drawWheel, lines 309-314) with two deliberate changes:
 *
 *   1. The DOM is injected, never reached for. Every function that needs a
 *      canvas, a 2d context or measureText takes it as an argument, so this
 *      module is testable under Node without a browser.
 *   2. Labels are optional. The prototype always drew a label inside every
 *      slice because it had exactly 8 slices. We render the full pool, which
 *      can be several hundred students, so past MAX_LABELS_ON_WHEEL the slice
 *      is still painted but the text is dropped. At 1000 slices one slice is
 *      0.0063 rad wide, which is smaller than a single pixel; drawing a name
 *      there produces a grey smear, not a label.
 *
 * The pointer is NOT drawn here. In the prototype it is a positioned <svg>
 * that CSS places above the canvas and JS kicks via a style transform, so it
 * survives a redraw of the face for free.
 */

import {
  MAX_LABELS_ON_WHEEL,
  POINTER_ANGLE,
  TAU,
  segmentStart,
  sliceAngle,
} from './wheelGeometry';

/** The four site colours, in the prototype's order (wheel-v4.html:207). */
export const WHEEL_PALETTE = Object.freeze([
  '#134f47', // teal
  '#E85B0D', // orange
  '#3D0F28', // plum
  '#FFF4E0', // ivory
]);

/** Ink that reads on top of the ivory slice (wheel-v4.html:300). */
export const INK_ON_IVORY = '#3D0F28';
/** Ink that reads on top of teal, orange and plum. */
export const INK_ON_DARK = '#FFF4E0';

/** Radius of the drawn face as a fraction of the canvas half-size. */
export const FACE_RATIO = 0.97;

/**
 * Should slice text be painted at all?
 *
 * `slices <= MAX_LABELS_ON_WHEEL` is the only case where a name is legible
 * inside a wedge. Callers still list every name in the side panel, so no
 * student is ever hidden by this.
 */
export function shouldShowLabels(slices) {
  return Number.isInteger(slices) && slices > 0 && slices <= MAX_LABELS_ON_WHEEL;
}

/**
 * Greedy word wrap. Port of wrapLabel (wheel-v4.html:285-289).
 *
 * A single word longer than `maxWidth` is never split, so a long unbroken
 * name overflows rather than disappearing.
 */
export function wrapLabel(measure, text, maxWidth) {
  const words = String(text ?? '').split(' ').filter((w) => w.length > 0);
  if (words.length === 0) return [];

  const lines = [];
  let current = '';
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (current && measure(candidate) > maxWidth) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
}

/** Normalise a segment to something drawable and labelable. */
function toSegments(segments) {
  if (!Array.isArray(segments)) return [];
  return segments.map((raw) => {
    if (typeof raw === 'string') return { label: raw };
    if (raw && typeof raw === 'object') {
      return {
        label: raw.label ?? raw.full_name ?? '',
        color: typeof raw.color === 'string' ? raw.color : null,
      };
    }
    return { label: '' };
  });
}

/** Measure the label width of a rendered face, given a measuring function. */
function measureWidthFactory(ctx) {
  return (text) => {
    const width = ctx.measureText(text).width;
    return Number.isFinite(width) ? width : 0;
  };
}

/**
 * Paint the face once and return the canvas holding it.
 *
 * The result is a static image: it depends only on (size, segments), never on
 * rotation. Callers cache it and blit it with a rotation, which is what keeps
 * a 1000-slice wheel at 60fps — re-filling a thousand wedges every frame is
 * what would drop it.
 *
 * @param {object} options
 * @param {Document} options.document      used only to create the canvas
 * @param {number}  options.size           pixel size of the square canvas
 * @param {Array}   options.segments       strings, or {label, color?}
 * @param {string[]} [options.palette]     defaults to WHEEL_PALETTE
 * @param {boolean} [options.showLabels]   force labels on/off
 * @returns {HTMLCanvasElement|null} null when size is unusable
 */
export function renderWheelFace({
  document: doc,
  size,
  segments,
  palette = WHEEL_PALETTE,
  showLabels,
} = {}) {
  if (!doc || typeof doc.createElement !== 'function') return null;
  if (!Number.isFinite(size) || size <= 0) return null;

  const items = toSegments(segments);
  if (items.length === 0) return null;

  const colours = palette && palette.length > 0 ? palette : WHEEL_PALETTE;
  const side = Math.round(size);
  const canvas = doc.createElement('canvas');
  canvas.width = side;
  canvas.height = side;

  const ctx = canvas.getContext && canvas.getContext('2d');
  if (!ctx) return canvas;

  const radius = side / 2;
  const face = radius * FACE_RATIO;
  const n = items.length;
  const angle = sliceAngle(n);
  const labels = showLabels === undefined ? shouldShowLabels(n) : Boolean(showLabels);
  const measure = measureWidthFactory(ctx);

  ctx.translate(radius, radius);

  for (let i = 0; i < n; i += 1) {
    const start = segmentStart(i, n);
    const colour = items[i].color || colours[i % colours.length];

    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.arc(0, 0, face, start, start + angle);
    ctx.closePath();
    ctx.fillStyle = colour;
    ctx.fill();
    ctx.strokeStyle = INK_ON_DARK;
    ctx.lineWidth = Math.max(1, side * 0.004);
    ctx.stroke();

    if (!labels) continue;

    ctx.save();
    ctx.rotate(start + angle / 2);
    ctx.fillStyle = colour === colours[3] ? INK_ON_IVORY : INK_ON_DARK;
    ctx.font = `800 ${Math.round(side * 0.026)}px Ghroob, Tahoma, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    const lines = wrapLabel(measure, items[i].label, face * 0.4);
    const lineHeight = side * 0.032;
    lines.forEach((line, lineIndex) => {
      const y = (lineIndex - (lines.length - 1) / 2) * lineHeight;
      ctx.fillText(line, face * 0.62, y);
    });
    ctx.restore();
  }

  ctx.lineWidth = side * 0.01;
  ctx.strokeStyle = INK_ON_IVORY;
  ctx.beginPath();
  ctx.arc(0, 0, face, 0, TAU);
  ctx.stroke();

  return canvas;
}

/**
 * Blit a cached face onto the live canvas at a given rotation.
 * Port of drawWheel (wheel-v4.html:309-314).
 *
 * @returns {boolean} false when there is nothing to draw yet
 */
export function drawWheelFrame(ctx, face, rotation, size) {
  if (!ctx || !face) return false;

  // "size omitted" means "use whatever the cached face is", but an explicit
  // size of 0 or NaN is a bug worth reporting rather than papering over with
  // the fallback, so the two cases are kept apart.
  const omitted = size === undefined || size === null;
  if (!omitted && (!Number.isFinite(size) || size <= 0)) return false;

  const side = omitted ? face.width : size;
  if (!Number.isFinite(side) || side <= 0) return false;

  const radius = side / 2;
  ctx.clearRect(0, 0, side, side);
  ctx.save();
  ctx.translate(radius, radius);
  ctx.rotate(Number.isFinite(rotation) ? rotation : 0);
  ctx.drawImage(face, -radius, -radius);
  ctx.restore();
  return true;
}

/** Where the pointer sits, exported so a caller can draw a test marker. */
export const POINTER_RADIUS = POINTER_ANGLE;
