import { describe, expect, it } from 'vitest';
import {
  DEFAULT_SPIN,
  JITTER_RATIO,
  MAX_LABELS_ON_WHEEL,
  POINTER_ANGLE,
  TAU,
  easeOut,
  isValidSlot,
  normalizeAngle,
  pegIndex,
  planSpin,
  rotationAt,
  segmentCenter,
  segmentEnd,
  segmentStart,
  sliceAngle,
  slotOfStudent,
  rotationForSlot,
} from './wheelGeometry';

/** Deterministic stand-in for Math.random so the edge cases are reproducible. */
const fixed = (value) => () => value;

/** Deterministic values in [0, 1) with no magic constants: a sine hash. */
function spread(i) {
  const x = Math.sin(i * 1.0001) * 1e4;
  return x - Math.floor(x);
}

/** Slice counts that matter: prototype's 8, our label cap, and both real ends. */
const SLICE_COUNTS = [2, 3, 5, 8, 12, 24, 25, 50, 137, 500, 1000];

describe('sliceAngle', () => {
  it('divides a full turn into equal slices', () => {
    expect(sliceAngle(8)).toBeCloseTo(TAU / 8, 12);
    expect(sliceAngle(1)).toBeCloseTo(TAU, 12);
  });

  it('sums to exactly one full turn', () => {
    for (const n of SLICE_COUNTS) {
      expect(n * sliceAngle(n)).toBeCloseTo(TAU, 12);
    }
  });

  it('rejects a non-positive or fractional slice count', () => {
    expect(() => sliceAngle(0)).toThrow(RangeError);
    expect(() => sliceAngle(-3)).toThrow(RangeError);
    expect(() => sliceAngle(2.5)).toThrow(RangeError);
    expect(() => sliceAngle(NaN)).toThrow(RangeError);
  });
});

describe('pegIndex — cross-checked against the painting model', () => {
  // Independent reference, written the way the canvas actually works
  // (`wheel-v4.html:297` paints, `:319` turns):
  //   - slice i is painted from segmentStart(i) clockwise by one slice;
  //   - turning the wheel adds `rotation` to every painted angle;
  //   - the pointer never moves, it is always at POINTER_ANGLE.
  // So the answer is whichever rotated interval contains the pointer. No
  // `floor`, no closed-form quotient — a linear scan, so the two can disagree.
  // The pointer has to be tried at every whole-turn offset that could possibly
  // fall inside the rotated face; a finished spin sits ~8-10 turns out, so the
  // window is derived from the rotation rather than hard-coded.
  function bruteForceSliceUnderPointer(rotation, slices) {
    const fromTurn = Math.floor(rotation / TAU) - 1;
    const toTurn = Math.ceil(rotation / TAU) + 1;
    for (let k = fromTurn; k <= toTurn; k += 1) {
      const pointer = POINTER_ANGLE + k * TAU;
      for (let i = 0; i < slices; i += 1) {
        const from = segmentStart(i, slices) + rotation;
        const to = segmentEnd(i, slices) + rotation;
        if (pointer >= from && pointer < to) return i;
      }
    }
    return -1;
  }

  const wrapped = (value, n) => ((value % n) + n) % n;

  it('matches the independent model at every slice count and rotation', () => {
    // Probe the *interior* of every slice, walked by whole turns and by a
    // spread of sub-slice offsets. Two rules make this exact:
    //   - offsets stay below 0.5, because a positive offset walks the pointer
    //     *towards the next slice* (r = POINTER - segmentCenter(i) + f*SLICE
    //     gives -r/SLICE = i + 0.5 - f, which floors to i-1 once f > 0.5);
    //   - interiors only. On an exact boundary the two can legitimately differ
    //     by one, because `pointer >= from && pointer < to` and `Math.floor`
    //     round differently once the sums are ~30 radians. That case is pinned
    //     down separately, against pegIndex alone.
    const offsets = [0.05, 0.17, 0.29, 0.41];
    for (const n of SLICE_COUNTS) {
      const sl = sliceAngle(n);
      for (let i = 0; i < n; i += 1) {
        const centreUp = POINTER_ANGLE - segmentCenter(i, n);
        for (const f of offsets) {
          for (const turns of [-3, 0, 2, 9]) {
            const r = centreUp + sl * f + turns * TAU;
            expect(pegIndex(r, n)).toBe(i);
            expect(bruteForceSliceUnderPointer(r, n)).toBe(i);
          }
        }
      }
    }
  });

  it('resolves an exact boundary to the later slice when the arithmetic is exact', () => {
    // A spin never lands on an edge — jitter keeps every landing at least
    // `JITTER_RATIO/2 = 0.25` of a slice away from either edge. So this is not
    // a case the product can hit; it is pinned only where float64 arithmetic is
    // exact, to document the convention: a leading edge under the pointer
    // reports that slice, not the previous one.
    //
    // For large `slices` the boundary is genuinely ill-conditioned and is NOT
    // asserted: `segmentStart(i)` is `i*SLICE - PI/2`, so recovering `i` means
    // subtracting two nearly equal numbers, and `-r/SLICE` can land a few
    // 1e-13 below the integer and floor to the previous slice. Any floor-based
    // lookup has that tie; the safety margin above is what keeps it unreachable.
    for (const n of [2, 4, 8]) {
      for (let i = 0; i < n; i += 1) {
        expect(pegIndex(POINTER_ANGLE - segmentStart(i, n), n)).toBe(i);
      }
    }
  });

  it('stays correct near a boundary on a large wheel, given a hair of clearance', () => {
    // The realistic worst case: 1000 slices, pointer sitting just inside the
    // edge of the winning slice rather than in its middle.
    for (const n of [137, 500, 1000]) {
      const sl = sliceAngle(n);
      for (let i = 0; i < n; i += 1) {
        const centreUp = POINTER_ANGLE - segmentCenter(i, n);
        for (const clearance of [0.26, 0.25, 0.24]) {
          const r = centreUp + sl * (0.5 - clearance);
          expect(pegIndex(r, n)).toBe(i);
        }
      }
    }
  });

  it('lands on the winner for a wheel spun by planSpin + rotationAt', () => {
    for (const n of SLICE_COUNTS) {
      for (let i = 0; i < n; i += 1) {
        const plan = planSpin({ startRotation: 0, winnerSlot: i, slices: n, rng: () => spread(i) });
        expect(pegIndex(rotationAt(plan, 1), n)).toBe(
          bruteForceSliceUnderPointer(rotationAt(plan, 1), n)
        );
      }
    }
  });

  it('puts segment 0 under the pointer at rest', () => {
    for (const n of SLICE_COUNTS) {
      expect(pegIndex(0, n)).toBe(0);
    }
  });

  it('always returns a valid slot for any rotation', () => {
    for (const n of SLICE_COUNTS) {
      for (let k = 0; k < 500; k += 1) {
        const idx = pegIndex((k / 500) * TAU * 7 - 3, n);
        expect(idx).toBeGreaterThanOrEqual(0);
        expect(idx).toBeLessThan(n);
      }
    }
  });

  it('does not reproduce the prototype sign bug (wheel-v4.html:362)', () => {
    // The prototype computes floor((r + PI/2) / SLICE). That is a different
    // question (it only drives the tick sound), so it is wrong for us: it maps
    // rotation to the *mirror* slice. Pin the disagreement down so that anyone
    // who copies the prototype line back in fails this test instead of
    // shipping an arrow that points at the wrong student.
    const prototypePegIndex = (r, slice) => Math.floor((r + Math.PI / 2) / slice);
    let disagreements = 0;
    for (const n of [2, 8, 24, 137]) {
      const sl = sliceAngle(n);
      for (let k = 1; k < 200; k += 1) {
        const r = (k / 200) * TAU;
        if (pegIndex(r, n) !== wrapped(prototypePegIndex(r, sl), n)) disagreements += 1;
      }
    }
    expect(disagreements).toBeGreaterThan(0);
  });
});

describe('segment boundaries', () => {
  it('lays slices out contiguously with no gap and no overlap', () => {
    for (const n of SLICE_COUNTS) {
      for (let i = 0; i < n - 1; i += 1) {
        expect(segmentEnd(i, n)).toBeCloseTo(segmentStart(i + 1, n), 12);
      }
    }
  });

  it('closes the circle: the last slice ends where slice 0 begins', () => {
    for (const n of SLICE_COUNTS) {
      expect(segmentEnd(n - 1, n)).toBeCloseTo(segmentStart(0, n) + TAU, 12);
    }
  });

  it('starts segment 0 at the pointer', () => {
    expect(segmentStart(0, 8)).toBeCloseTo(POINTER_ANGLE, 12);
  });

  it('centres every slice inside that slice', () => {
    for (const n of [2, 8, 24, 137]) {
      const sl = sliceAngle(n);
      for (let i = 0; i < n; i += 1) {
        const c = segmentCenter(i, n);
        expect(c).toBeGreaterThan(segmentStart(i, n));
        expect(c).toBeLessThan(segmentEnd(i, n));
        expect(c - segmentStart(i, n)).toBeCloseTo(sl / 2, 12);
      }
    }
  });
});

describe('normalizeAngle', () => {
  it('wraps into [0, TAU) from both directions', () => {
    expect(normalizeAngle(0)).toBe(0);
    expect(normalizeAngle(TAU)).toBe(0);
    expect(normalizeAngle(TAU * 3)).toBe(0);
    expect(normalizeAngle(-Math.PI)).toBeCloseTo(Math.PI, 12);
    expect(normalizeAngle(-TAU * 2.5)).toBeCloseTo(TAU * 0.5, 12);
  });

  it('stays in range for extreme inputs', () => {
    for (const r of [-1e6, -123.456, 0, 123.456, 1e6]) {
      const v = normalizeAngle(r);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(TAU);
    }
  });
});

describe('easeOut', () => {
  it('pins both endpoints exactly', () => {
    expect(easeOut(0)).toBe(0);
    expect(easeOut(1)).toBe(1);
  });

  it('never decreases and stays inside [0, 1]', () => {
    let prev = -1;
    for (let t = 0; t <= 1.0001; t += 0.01) {
      const v = easeOut(t);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
      expect(v).toBeGreaterThanOrEqual(prev);
      prev = v;
    }
  });

  it('is front-loaded: past halfway before t reaches 0.5', () => {
    expect(easeOut(0.5)).toBeGreaterThan(0.9);
  });
});

describe('rotationForSlot — THE guarantee', () => {
  it('lands on the requested slice for every slice and every count', () => {
    for (const n of SLICE_COUNTS) {
      for (let i = 0; i < n; i += 1) {
        const target = rotationForSlot(i, n, () => spread(i * 7919 + n));
        expect(pegIndex(target, n)).toBe(i);
      }
    }
  });

  it('survives the extreme rng values, not just the happy middle', () => {
    for (const n of SLICE_COUNTS) {
      for (const value of [0, 1e-9, 0.5, 0.999999, 1]) {
        for (let i = 0; i < n; i += 1) {
          const target = rotationForSlot(i, n, fixed(value));
          expect(pegIndex(target, n)).toBe(i);
        }
      }
    }
  });

  it('keeps the offset inside the slice, as a fraction of its width', () => {
    // rng = 0.5 makes the jitter exactly zero, so it doubles as the unjittered
    // landing angle the offset must be measured from.
    const n = 12;
    const sl = sliceAngle(n);
    for (let i = 0; i < n; i += 1) {
      const base = rotationForSlot(i, n, fixed(0.5));
      const offset = Math.abs(rotationForSlot(i, n, () => spread(i)) - base);
      expect(offset).toBeLessThanOrEqual((sl * JITTER_RATIO) / 2 + 1e-12);
    }
  });

  it('keeps a comfortable margin away from the slice edges', () => {
    // The safety argument for JITTER_RATIO = 0.5: we must never approach
    // 50% of the slice, where floor() could tip into the neighbour.
    const n = 7;
    const sl = sliceAngle(n);
    for (let i = 0; i < n; i += 1) {
      const base = rotationForSlot(i, n, fixed(0.5));
      for (let k = 0; k < 300; k += 1) {
        const offset = Math.abs(rotationForSlot(i, n, () => spread(k * 31 + i)) - base);
        expect(offset).toBeLessThan(sl * 0.5 - sl * 0.01);
      }
    }
  });

  it('rejects the naive "spin to segmentCenter" shortcut', () => {
    // segmentCenter is where slice i is PAINTED, not how far to TURN the wheel.
    // Spinning to it parks the pointer on some other slice entirely, which is
    // the exact failure the prototype shipped with.
    let wrong = 0;
    for (const n of [3, 5, 8, 12, 24]) {
      for (let i = 0; i < n; i += 1) {
        if (pegIndex(segmentCenter(i, n), n) !== i) wrong += 1;
      }
    }
    expect(wrong).toBeGreaterThan(0);
  });
});

describe('planSpin', () => {
  it('ends exactly on the winner when progress reaches 1', () => {
    for (const n of SLICE_COUNTS) {
      for (let i = 0; i < n; i += 1) {
        const plan = planSpin({ startRotation: 0, winnerSlot: i, slices: n, rng: () => spread(i + n) });
        expect(pegIndex(rotationAt(plan, 1), n)).toBe(i);
      }
    }
  });

  it('ends on the winner regardless of where the wheel was left', () => {
    const starts = [0, 0.5, 2.1, 5.9, -3.3, TAU * 4 + 1.1, 63.7];
    for (const startRotation of starts) {
      for (const n of [5, 24, 1000]) {
        for (let i = 0; i < n; i += 1) {
          const plan = planSpin({ startRotation, winnerSlot: i, slices: n, rng: () => spread(i) });
          expect(pegIndex(rotationAt(plan, 1), n)).toBe(i);
        }
      }
    }
  });

  it('gives the same landing angle no matter how many turns were added', () => {
    // turns is a whole number of rotations, so it must not move the target.
    const n = 24;
    const targets = [0, 0.5, 1].map((turns) =>
      planSpin({ startRotation: 1.7, winnerSlot: 9, slices: n, minTurns: turns, maxTurns: turns, rng: () => spread(42) })
        .target
    );
    for (const t of targets) expect(t).toBeCloseTo(targets[0], 12);
  });

  it('spins forward only — delta is always positive', () => {
    for (const n of [2, 24, 1000]) {
      for (let i = 0; i < n; i += 1) {
        for (const startRotation of [0, 3, 5.5, 6.2]) {
          const plan = planSpin({ startRotation, winnerSlot: i, slices: n, rng: () => spread(i + startRotation) });
          expect(plan.delta).toBeGreaterThan(0);
        }
      }
    }
  });

  it('honours the requested turn range', () => {
    for (let k = 0; k < 200; k += 1) {
      const plan = planSpin({ startRotation: 0, winnerSlot: 1, slices: 8, rng: () => spread(k) });
      expect(plan.turns).toBeGreaterThanOrEqual(DEFAULT_SPIN.minTurns);
      expect(plan.turns).toBeLessThanOrEqual(DEFAULT_SPIN.maxTurns);
    }
  });

  it('covers at least the minimum number of turns', () => {
    for (let k = 0; k < 200; k += 1) {
      const plan = planSpin({ startRotation: 0, winnerSlot: 0, slices: 8, rng: () => spread(k) });
      expect(plan.turns).toBeGreaterThanOrEqual(DEFAULT_SPIN.minTurns);
    }
  });

  it('always picks a whole number of turns', () => {
    // Not cosmetic: rotationAt(plan, 1) is `target + turns * TAU` exactly, and
    // pegIndex divides by TAU/slices. A fractional count shifts that quotient
    // fractionally and floor() tips onto the neighbouring slice.
    for (let k = 0; k < 500; k += 1) {
      for (const n of [3, 8, 24, 137]) {
        const plan = planSpin({ startRotation: spread(k), winnerSlot: k % n, slices: n, rng: () => spread(k * 13 + n) });
        expect(Number.isInteger(plan.turns)).toBe(true);
        expect(plan.delta / TAU).toBeCloseTo(
          plan.turns + (plan.target - plan.start) / TAU,
          12
        );
      }
    }
  });

  it('cannot be pushed past maxTurns by a misbehaving rng', () => {
    for (const value of [0, 1, 1.5, 99]) {
      const plan = planSpin({ startRotation: 0, winnerSlot: 0, slices: 8, rng: fixed(value) });
      expect(plan.turns).toBeGreaterThanOrEqual(DEFAULT_SPIN.minTurns);
      expect(plan.turns).toBeLessThanOrEqual(DEFAULT_SPIN.maxTurns);
    }
  });

  it('rejects a winner slot that is not on the wheel', () => {
    expect(() => planSpin({ startRotation: 0, winnerSlot: 8, slices: 8 })).toThrow(RangeError);
    expect(() => planSpin({ startRotation: 0, winnerSlot: -1, slices: 8 })).toThrow(RangeError);
    expect(() => planSpin({ startRotation: 0, winnerSlot: 1.5, slices: 8 })).toThrow(RangeError);
  });

  it('rejects an inverted turn range', () => {
    expect(() =>
      planSpin({ startRotation: 0, winnerSlot: 0, slices: 8, minTurns: 10, maxTurns: 5 })
    ).toThrow(RangeError);
  });
});

describe('rotationAt across the animation', () => {
  it('starts exactly at the resting rotation', () => {
    const plan = planSpin({ startRotation: 2.4, winnerSlot: 5, slices: 24, rng: () => spread(3) });
    expect(rotationAt(plan, 0)).toBeCloseTo(plan.start, 12);
  });

  it('moves monotonically from start to target', () => {
    const plan = planSpin({ startRotation: 0, winnerSlot: 6, slices: 12, rng: () => spread(11) });
    let prev = rotationAt(plan, 0);
    for (let t = 0.02; t <= 1.0001; t += 0.02) {
      const v = rotationAt(plan, t);
      expect(v).toBeGreaterThanOrEqual(prev);
      prev = v;
    }
  });

  it('never leaves the winner during the final approach', () => {
    // easeOut is front-loaded, so by 98% of the run the wheel is already
    // parked on the winner and only creeps. That is what makes the name
    // readable while it is still visibly decelerating. The margin is real:
    // the target sits at least 0.25 * sliceAngle away from either edge, and
    // the angle still left to travel at t = 0.98 is under 1e-5 rad.
    for (const n of [2, 5, 24, 137, 1000]) {
      for (let i = 0; i < n; i += 1) {
        const plan = planSpin({ startRotation: 0, winnerSlot: i, slices: n, rng: () => spread(i) });
        for (let t = 0.98; t <= 1.0001; t += 0.005) {
          expect(pegIndex(rotationAt(plan, t), n)).toBe(i);
        }
      }
    }
  });

  it('does cross other slices on the way, which is what makes it read as a spin', () => {
    const n = 24;
    const plan = planSpin({ startRotation: 0, winnerSlot: 0, slices: n, rng: () => spread(5) });
    const seen = new Set();
    for (let t = 0; t <= 1; t += 0.01) seen.add(pegIndex(rotationAt(plan, t), n));
    expect(seen.size).toBeGreaterThan(1);
  });
});

describe('isValidSlot', () => {
  it('accepts only in-range integers', () => {
    expect(isValidSlot(0, 8)).toBe(true);
    expect(isValidSlot(7, 8)).toBe(true);
    expect(isValidSlot(8, 8)).toBe(false);
    expect(isValidSlot(-1, 8)).toBe(false);
    expect(isValidSlot(1.5, 8)).toBe(false);
    expect(isValidSlot('3', 8)).toBe(false);
  });
});

describe('slotOfStudent', () => {
  const board = [
    { student_id: 101, full_name: 'Dana' },
    { student_id: 102, full_name: 'Omar' },
    { student_id: 103, full_name: 'Lina' },
  ];

  it('finds the student the backend picked', () => {
    expect(slotOfStudent(board, 101)).toBe(0);
    expect(slotOfStudent(board, 102)).toBe(1);
    expect(slotOfStudent(board, 103)).toBe(2);
  });

  it('returns -1 when the winner is not on this board', () => {
    expect(slotOfStudent(board, 999)).toBe(-1);
  });

  it('returns -1 for a missing or malformed input instead of throwing', () => {
    expect(slotOfStudent(board, null)).toBe(-1);
    expect(slotOfStudent(board, undefined)).toBe(-1);
    expect(slotOfStudent(null, 101)).toBe(-1);
    expect(slotOfStudent([], 101)).toBe(-1);
  });

  it('matches by strict id — string ids must not match numeric ids', () => {
    expect(slotOfStudent([{ student_id: 1 }], '1')).toBe(-1);
  });

  it('still handles a board containing holes', () => {
    expect(slotOfStudent([null, { student_id: 5 }, undefined], 5)).toBe(1);
  });
});

describe('label threshold', () => {
  it('is the documented cap', () => {
    expect(MAX_LABELS_ON_WHEEL).toBe(24);
  });
});
