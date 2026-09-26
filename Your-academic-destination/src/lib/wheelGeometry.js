/**
 * wheelGeometry.js — pure geometry for the Lucky Wheel. No React, no DOM, no canvas.
 *
 * WHY A STANDALONE MODULE
 * The single biggest risk in this feature is the drawing and the maths
 * disagreeing: the canvas paints N slices, and `pegIndex` decides which slice
 * sits under the pointer. If two places compute that independently they WILL
 * drift, and the symptom is the worst kind — the arrow lands on a slice that
 * does not match the student's name on the projector. So there is exactly one
 * definition of a slice here, and both consumers use it:
 *   - `WheelCanvas`   -> `segmentStart` / `segmentCenter`   (painting)
 *   - `useWheelSpin`  -> `planSpin` / `rotationAt`          (motion)
 *
 * Every function is pure: no imports, no shared state, no `Date`, no RNG unless
 * one is injected. That is what makes the guarantee in `rotationForSlot`
 * testable in isolation — and it is the entire reason this test file exists.
 *
 * ---------------------------------------------------------------------------
 * THE TWO ANGLES THAT ARE EASY TO CONFUSE (and the prototype confuses them)
 * ---------------------------------------------------------------------------
 * Canvas angles increase CLOCKWISE on screen, because the y axis points down.
 * The fixed pointer (the arrow above the wheel) sits at `-PI / 2`, i.e. noon.
 *
 * 1. WHERE A SLICE IS PAINTED — `segmentStart(i) = i * SLICE - PI / 2`.
 *    Slice `i` is drawn from 12 o'clock, going clockwise, by `SLICE` radians.
 *    This is the canvas's job. At zero rotation, slice 0 straddles noon.
 *
 * 2. HOW MUCH THE WHEEL IS TURNED — `rotation`.
 *    `ctx.rotate(rotation)` turns the painted face clockwise, so slice `i`
 *    ends up on screen at `[segmentStart(i) + rotation, ... + SLICE)`.
 *    Asking which slice is under the pointer at `-PI / 2`:
 *
 *      i * SLICE - PI/2 + rotation  <=  -PI/2  <  i * SLICE - PI/2 + rotation + SLICE
 *      i * SLICE + rotation         <=   0     <  i * SLICE + rotation + SLICE
 *      i = floor(-rotation / SLICE)
 *
 *    That is `pegIndex`, and note the MINUS sign. The prototype writes
 *    `Math.floor((r + Math.PI / 2) / SLICE)` (`wheel-v4.html:362`) which is a
 *    different function — it only governs when the tick sound fires, so the bug
 *    was harmless there. For us it would be fatal, so the sign is corrected
 *    here and pinned by a test.
 *
 * 3. THEREFORE, to bring slice `i` under the pointer you must turn the wheel to
 *    `-PI/2 - segmentCenter(i)`, NOT to `segmentCenter(i)`. See
 *    `rotationForSlot` — the single most important line in this file.
 */

export const TAU = Math.PI * 2;

/** The fixed pointer, 12 o'clock. Also where slice 0 is painted at rest. */
export const POINTER_ANGLE = -Math.PI / 2;

/**
 * Above this many slices, labels are dropped from the wheel face. Below it a
 * slice gets narrower than a pixel and the text turns into an unreadable smudge.
 * The wheel is NOT reduced — all N slices still exist and still land correctly.
 * The scrollable name list beside the wheel is the fallback (plan §4.1).
 */
export const MAX_LABELS_ON_WHEEL = 24;

/**
 * Jitter amplitude as a fraction of one slice.
 *
 * The landing rotation is the winner's exact slice centre plus a small offset,
 * so the arrow does not look mechanically parked. The offset is capped at 25%
 * of the slice per side. The reason is `floor`: at exactly 50% (the slice edge)
 * floating point noise tips the quotient into the neighbour. At 25% the margin
 * is permanent, which is what makes the guarantee in `rotationForSlot` a
 * guarantee and not a probability.
 */
export const JITTER_RATIO = 0.5;

/** Default spin envelope: 420ms windup, ~5.2s of motion, 8-10 turns. */
export const DEFAULT_SPIN = Object.freeze({
  minTurns: 8,
  maxTurns: 10,
  windupMs: 420,
  spinMs: 5200,
});

/** Wrap any angle into [0, TAU). Keeps the number small across many spins. */
export function normalizeAngle(radians) {
  const m = radians % TAU;
  return m < 0 ? m + TAU : m;
}

/** Angular width of one slice. */
export function sliceAngle(slices) {
  if (!Number.isInteger(slices) || slices < 1) {
    throw new RangeError(`slices must be an integer >= 1, received: ${slices}`);
  }
  return TAU / slices;
}

/**
 * Which slice is under the pointer, for a wheel turned by `rotation`.
 *
 * Returned value is always in `0 .. slices-1` — the modulo matters because
 * `rotation` grows by ~8-10 full turns every spin, so `-rotation / SLICE`
 * runs into large negative numbers. `planSpin` normalises the start angle, but
 * the accumulated total still climbs, and an unwrapped value would hand the
 * canvas a negative slice index.
 */
export function pegIndex(rotation, slices) {
  const n = slices;
  const raw = Math.floor(-rotation / sliceAngle(n));
  return ((raw % n) + n) % n;
}

/** First canvas angle of slice `index`, at zero rotation. (Painting.) */
export function segmentStart(index, slices) {
  return index * sliceAngle(slices) + POINTER_ANGLE;
}

/** End canvas angle of slice `index` (exclusive, matching `canvas.arc`). */
export function segmentEnd(index, slices) {
  return (index + 1) * sliceAngle(slices) + POINTER_ANGLE;
}

/** Centre of slice `index` as painted, at zero rotation. */
export function segmentCenter(index, slices) {
  return (index + 0.5) * sliceAngle(slices) + POINTER_ANGLE;
}

/** Is `index` a real slot on a wheel of `slices` slices? */
export function isValidSlot(index, slices) {
  return Number.isInteger(index) && index >= 0 && index < slices;
}

/**
 * Locate the winner's slot in the local board.
 *
 * The winner is chosen by the BACKEND (`POST /admin/wheel/draws` returns
 * `student_id`). This is the join between that server decision and our locally
 * ordered board: given the board we drew, where does that student sit?
 *
 * Returns -1 when not found — e.g. the pool changed in another session. That
 * is a real case the caller must handle, not an impossible one, so it is
 * returned rather than thrown.
 */
export function slotOfStudent(board, studentId) {
  if (!Array.isArray(board) || studentId === null || studentId === undefined) {
    return -1;
  }
  return board.findIndex((s) => s && s.student_id === studentId);
}

/**
 * The wheel rotation that lands slice `index` under the pointer.
 *
 * This is the fix for the prototype's core bug, and it is deliberately the
 * OPPOSITE sign to `segmentCenter`, which is the trap:
 *
 *   the prototype (`wheel-v4.html:369-376`) fetched the winner, then spun to an
 *   independently random angle, so the arrow stopped on an unrelated slice.
 *   Worse, the natural-looking formula — `segmentCenter(i) + jitter` — is also
 *   wrong: that is where slice i is PAINTED, not how far to turn. Using it
 *   lands the pointer on slice `n - 1 - i`, the mirror image.
 *
 * The correct value turns the wheel so that slice i's centre arrives at noon:
 *   rotation = POINTER_ANGLE - segmentCenter(i) = -(i + 0.5) * SLICE
 *
 * Proof of the guarantee. With `jitter / SLICE` confined to [-0.25, 0.25]:
 *   pegIndex(rotationForSlot(i)) = floor(-rotationForSlot(i) / SLICE)
 *                                = floor(i + 0.5 - jitter/SLICE)
 *   and `i + 0.5 - jitter/SLICE` lies in [i + 0.25, i + 0.75]
 *   so the floor is exactly `i`, for any `rng` returning values in [0, 1).
 * The arrow cannot leave the winner's slice.
 */
export function rotationForSlot(index, slices, rng = Math.random) {
  const sl = sliceAngle(slices);
  const jitter = (rng() - 0.5) * sl * JITTER_RATIO;
  return POINTER_ANGLE - segmentCenter(index, slices) + jitter;
}

/**
 * The prototype's easing (`wheel-v4.html:360`), with `t` clamped to [0, 1].
 * The clamp is not cosmetic: `(1 - t) ** 4.3` with `t` a hair over 1 is a
 * negative base to a fractional power, which is NaN, and one NaN frame freezes
 * the wheel mid-spin. `easeOut(1) === 1` exactly, which is what lets
 * `rotationAt` land precisely.
 */
export function easeOut(t) {
  const c = t < 0 ? 0 : t > 1 ? 1 : t;
  return 1 - (1 - c) ** 4.3;
}

/**
 * Build a spin plan: where we start, how many turns, and the total delta.
 *
 * The returned object is what the RAF loop consumes. `delta` is always
 * positive — `turns >= minTurns` (8) dwarfs the 1-turn spread of
 * `target - start` — so the wheel only ever moves forward and never makes a
 * backward jerk.
 */
export function planSpin({
  startRotation,
  winnerSlot,
  slices,
  minTurns = DEFAULT_SPIN.minTurns,
  maxTurns = DEFAULT_SPIN.maxTurns,
  rng = Math.random,
}) {
  if (!isValidSlot(winnerSlot, slices)) {
    throw new RangeError(
      `winnerSlot must be within 0..${slices - 1}, received: ${winnerSlot}`
    );
  }
  if (!(maxTurns >= minTurns)) {
    throw new RangeError(
      `maxTurns (${maxTurns}) must be >= minTurns (${minTurns})`
    );
  }

  // Normalise before doing arithmetic so precision does not decay over a long
  // ceremony: after 20 consecutive spins an un-normalised angle is ~1000 rad.
  const start = normalizeAngle(startRotation);

  // `turns` MUST be a whole number, and this is not cosmetic. `rotationAt(plan, 1)`
  // returns `target + turns * TAU` exactly, and `pegIndex` divides by SLICE, i.e.
  // it divides by `TAU / slices`. A fractional turn count therefore shifts the
  // quotient by a fractional amount and `floor()` can land on the neighbouring
  // slice — the arrow would stop next to the student instead of on them. An
  // integer count contributes an exact `turns * slices` to the quotient, which
  // `floor()` absorbs without moving the result. The range is inclusive.
  const span = maxTurns - minTurns + 1;
  // `rng()` is contractually [0, 1) — Math.random never returns 1 — but a
  // misbehaving or stubbed source must not push `turns` past maxTurns.
  const step = Math.min(span - 1, Math.floor(rng() * span));
  const turns = minTurns + Math.max(0, step);
  const target = rotationForSlot(winnerSlot, slices, rng);

  return {
    start,
    target,
    turns,
    delta: target - start + turns * TAU,
  };
}

/**
 * Wheel rotation at a point in the animation. `progress` runs 0 -> 1.
 * At `t === 1` this returns EXACTLY the target, because `easeOut(1) === 1`.
 * That exactness is the guarantee that the arrow stops on the announced student.
 */
export function rotationAt(plan, progress) {
  return plan.start + plan.delta * easeOut(progress);
}
