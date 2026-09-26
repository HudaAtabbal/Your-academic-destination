import { describe, expect, it } from 'vitest';

import {
  FACE_RATIO,
  INK_ON_DARK,
  INK_ON_IVORY,
  WHEEL_PALETTE,
  drawWheelFrame,
  renderWheelFace,
  shouldShowLabels,
  wrapLabel,
} from './wheelCanvas';

function makeFakeContext({ textWidth = (t) => t.length * 10 } = {}) {
  const calls = [];
  const fillStyles = [];
  const record = (name) => (...args) => {
    calls.push([name, ...args]);
  };

  const ctx = {
    calls,
    fillStyles,
    font: '',
    strokeStyle: '',
    lineWidth: 0,
    textAlign: '',
    textBaseline: '',
    beginPath: record('beginPath'),
    moveTo: record('moveTo'),
    arc: record('arc'),
    closePath: record('closePath'),
    fill: record('fill'),
    stroke: record('stroke'),
    save: record('save'),
    restore: record('restore'),
    translate: record('translate'),
    rotate: record('rotate'),
    fillText: record('fillText'),
    clearRect: record('clearRect'),
    drawImage: record('drawImage'),
    measureText: (t) => ({ width: textWidth(t) }),
  };

  Object.defineProperty(ctx, 'fillStyle', {
    get: () => ctx._fillStyle,
    set: (v) => {
      ctx._fillStyle = v;
      fillStyles.push(v);
    },
  });

  return ctx;
}

function makeFakeDocument(ctx) {
  const created = [];
  return {
    created,
    createElement(tag) {
      if (tag !== 'canvas') return null;
      const el = { tagName: 'CANVAS', width: 0, height: 0, getContext: () => ctx };
      created.push(el);
      return el;
    },
  };
}

const names = (n, prefix = 'S') =>
  Array.from({ length: n }, (_, i) => `${prefix}${i}`);

const count = (ctx, name) => ctx.calls.filter((c) => c[0] === name).length;

describe('shouldShowLabels', () => {
  it('is true only up to the label budget', () => {
    expect(shouldShowLabels(1)).toBe(true);
    expect(shouldShowLabels(8)).toBe(true);
    expect(shouldShowLabels(24)).toBe(true);
    expect(shouldShowLabels(25)).toBe(false);
    expect(shouldShowLabels(1000)).toBe(false);
  });

  it('rejects a pool that is not a positive integer', () => {
    expect(shouldShowLabels(0)).toBe(false);
    expect(shouldShowLabels(-3)).toBe(false);
    expect(shouldShowLabels(2.5)).toBe(false);
    expect(shouldShowLabels(NaN)).toBe(false);
    expect(shouldShowLabels(undefined)).toBe(false);
  });
});

describe('wrapLabel', () => {
  const measure = (t) => t.length * 10;

  it('returns nothing for empty input', () => {
    expect(wrapLabel(measure, '', 100)).toEqual([]);
    expect(wrapLabel(measure, '   ', 100)).toEqual([]);
    expect(wrapLabel(measure, null, 100)).toEqual([]);
    expect(wrapLabel(measure, undefined, 100)).toEqual([]);
  });

  it('keeps a short phrase on one line', () => {
    expect(wrapLabel(measure, 'Ahmad Khalil', 1000)).toEqual(['Ahmad Khalil']);
  });

  it('breaks before exceeding the budget', () => {
    expect(wrapLabel(measure, 'aaaa bbbb cccc', 90)).toEqual(['aaaa bbbb', 'cccc']);
  });

  it('never splits a single long word', () => {
    expect(wrapLabel(measure, 'Supercalifragilistic', 20)).toEqual(['Supercalifragilistic']);
  });
});

describe('renderWheelFace', () => {
  it('returns null instead of throwing when the environment is unusable', () => {
    expect(renderWheelFace()).toBeNull();
    expect(renderWheelFace({ segments: ['a'] })).toBeNull();
    expect(renderWheelFace({ document: {}, size: 100, segments: ['a'] })).toBeNull();

    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    expect(renderWheelFace({ document: doc, size: 0, segments: ['a'] })).toBeNull();
    expect(renderWheelFace({ document: doc, size: NaN, segments: ['a'] })).toBeNull();
    expect(renderWheelFace({ document: doc, size: 100, segments: [] })).toBeNull();
    expect(renderWheelFace({ document: doc, size: 100, segments: null })).toBeNull();
  });

  it('creates one canvas of the rounded size', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    const face = renderWheelFace({ document: doc, size: 300.4, segments: names(6) });

    expect(doc.created).toHaveLength(1);
    expect(face.width).toBe(300);
    expect(face.height).toBe(300);
  });

  it('paints one wedge per segment, plus the rim', () => {
    for (const n of [1, 3, 8, 24, 25, 500]) {
      const ctx = makeFakeContext();
      const doc = makeFakeDocument(ctx);
      renderWheelFace({ document: doc, size: 200, segments: names(n) });
      expect(count(ctx, 'arc')).toBe(n + 1);
      expect(count(ctx, 'fill')).toBe(n);
    }
  });

  it('centres the face and strokes it to FACE_RATIO', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    renderWheelFace({ document: doc, size: 200, segments: names(8) });

    expect(ctx.calls[0]).toEqual(['translate', 100, 100]);
    const rim = ctx.calls.filter((c) => c[0] === 'arc').at(-1);
    expect(rim[3]).toBeCloseTo(100 * FACE_RATIO, 6);
  });

  it('draws the text of every segment when labels are on', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    renderWheelFace({ document: doc, size: 200, segments: names(8) });

    // 8 segments, 8 one-line labels.
    expect(count(ctx, 'fillText')).toBe(8);
    expect(count(ctx, 'save')).toBe(8);
  });

  it('drops the text but keeps the wedges past the label budget', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    renderWheelFace({ document: doc, size: 200, segments: names(1000) });

    expect(count(ctx, 'arc')).toBe(1001);
    expect(count(ctx, 'fillText')).toBe(0);
  });

  it('honours an explicit showLabels override in both directions', () => {
    const on = makeFakeContext();
    renderWheelFace({
      document: makeFakeDocument(on),
      size: 200,
      segments: names(60),
      showLabels: true,
    });
    expect(count(on, 'fillText')).toBe(60);

    const off = makeFakeContext();
    renderWheelFace({
      document: makeFakeDocument(off),
      size: 200,
      segments: names(4),
      showLabels: false,
    });
    expect(count(off, 'fillText')).toBe(0);
  });

  it('splits a long name across several lines', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    renderWheelFace({
      document: doc,
      size: 300,
      segments: ['محمد عبد الرحمن الشامي'],
    });
    expect(count(ctx, 'fillText')).toBeGreaterThan(1);
  });

  it('flips the ink on the ivory wedge so the name stays readable', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    // WHEEL_PALETTE[3] is ivory, so the 4th segment is the light one.
    renderWheelFace({ document: doc, size: 200, segments: names(4) });

    expect(ctx.fillStyles).toContain(INK_ON_IVORY);
    expect(ctx.fillStyles).toContain(INK_ON_DARK);
  });

  it('wraps every segment in exactly one save/restore pair', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    renderWheelFace({ document: doc, size: 200, segments: names(24) });
    expect(count(ctx, 'save')).toBe(count(ctx, 'restore'));
  });

  it('cycles the palette and accepts a per-segment override', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    // Labels off, so fillStyles holds nothing but the wedge fills. With labels
    // on, the label ink also lands there and INK_ON_DARK is itself palette[3].
    renderWheelFace({
      document: doc,
      size: 200,
      segments: [...names(4), { label: 'pinned', color: '#00FF00' }],
      showLabels: false,
    });

    // The first four wedges take the palette in order, the fifth pins a colour.
    expect(ctx.fillStyles).toEqual([...WHEEL_PALETTE, '#00FF00']);
  });

  it('accepts plain strings and objects alike', () => {
    const ctx = makeFakeContext();
    const doc = makeFakeDocument(ctx);
    renderWheelFace({
      document: doc,
      size: 200,
      segments: ['A', { full_name: 'B' }, null],
    });
    // Three wedges, one line each (A, B, and an empty label that wraps to []).
    expect(count(ctx, 'arc')).toBe(4);
    expect(count(ctx, 'fillText')).toBe(2);
  });

  it('still returns the canvas when getContext is unavailable', () => {
    const doc = {
      createElement: () => ({ width: 0, height: 0, getContext: () => null }),
    };
    const face = renderWheelFace({ document: doc, size: 100, segments: names(4) });
    expect(face).not.toBeNull();
    expect(face.width).toBe(100);
  });
});

describe('drawWheelFrame', () => {
  const face = { width: 240, height: 240 };

  it('reports failure instead of throwing on a missing target', () => {
    expect(drawWheelFrame(null, face, 0, 240)).toBe(false);
    expect(drawWheelFrame(makeFakeContext(), null, 0, 240)).toBe(false);
    expect(drawWheelFrame(makeFakeContext(), face, 0, 0)).toBe(false);
    expect(drawWheelFrame(makeFakeContext(), face, 0, NaN)).toBe(false);
  });

  it('clears, then rotates the cached face about the centre', () => {
    const ctx = makeFakeContext();
    expect(drawWheelFrame(ctx, face, 1.25, 240)).toBe(true);

    const order = ctx.calls.map((c) => c[0]);
    expect(order).toEqual([
      'clearRect',
      'save',
      'translate',
      'rotate',
      'drawImage',
      'restore',
    ]);
    expect(ctx.calls[0]).toEqual(['clearRect', 0, 0, 240, 240]);
    expect(ctx.calls[2]).toEqual(['translate', 120, 120]);
    expect(ctx.calls[3]).toEqual(['rotate', 1.25]);
    expect(ctx.calls[4]).toEqual(['drawImage', face, -120, -120]);
  });

  it('falls back to the face size when no size is given', () => {
    const ctx = makeFakeContext();
    expect(drawWheelFrame(ctx, face, 0)).toBe(true);
    expect(ctx.calls[2]).toEqual(['translate', 120, 120]);
  });

  it('treats a non-finite rotation as zero rather than drawing NaN', () => {
    const ctx = makeFakeContext();
    drawWheelFrame(ctx, face, NaN, 240);
    expect(ctx.calls[3]).toEqual(['rotate', 0]);
  });
});
