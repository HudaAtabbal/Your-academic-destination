/**
 * wheelAudio.test.js
 *
 * The audio engine cannot be heard in CI, so the fake Web Audio context asserts
 * on structure instead: which nodes exist, which ones are started, when they
 * stop, and how the bus is wired.
 *
 * The fake deliberately throws on the mistakes a real browser throws on, so the
 * suite catches them here rather than mid-ceremony:
 *   - exponentialRampToValueAtTime(value) with value === 0 is illegal.
 *   - any scheduling call with a non-finite time is illegal.
 */

import { beforeEach, describe, expect, it } from 'vitest';
import {
  createWheelAudio,
  DEFAULT_MUTED,
  MUTE_STORAGE_KEY,
} from './wheelAudio';

/** Minimal AudioParam that remembers nothing but validates what it is given. */
class FakeParam {
  constructor(value, name) {
    this.value = value;
    this.name = name;
  }

  #check(value, when) {
    if (!Number.isFinite(value)) {
      throw new TypeError(`${this.name}: non-finite value at ${when}`);
    }
    if (!Number.isFinite(when)) {
      throw new TypeError(`${this.name}: non-finite time`);
    }
  }

  setValueAtTime(value, when) {
    this.#check(value, when);
    return this;
  }

  linearRampToValueAtTime(value, when) {
    this.#check(value, when);
    return this;
  }

  exponentialRampToValueAtTime(value, when) {
    this.#check(value, when);
    if (value === 0) {
      throw new RangeError(`${this.name}: exponential ramp cannot reach 0`);
    }
    return this;
  }
}

class FakeNode {
  constructor(kind, log) {
    this.kind = kind;
    this.log = log;
    this.outputs = [];
  }

  connect(target) {
    this.outputs.push(target);
    this.log.connects.push({ from: this, to: target });
    return target;
  }
}

function makeFake() {
  const log = {
    connects: [],
    starts: [],
    stops: [],
    created: [],
  };

  let clock = 0;

  const ctx = {
    currentTime: 0,
    sampleRate: 44100,
    state: 'running',
    destination: new FakeNode('destination', log),
    resume: () => {
      ctx.state = 'running';
      return Promise.resolve();
    },
    close: () => {
      ctx.state = 'closed';
      return Promise.resolve();
    },
    createGain: () => {
      const n = new FakeNode('gain', log);
      n.gain = new FakeParam(1, 'gain');
      log.created.push(n);
      return n;
    },
    createOscillator: () => {
      const n = new FakeNode('oscillator', log);
      n.type = 'sine';
      n.frequency = new FakeParam(440, 'frequency');
      n.detune = new FakeParam(0, 'detune');
      n.start = (when) => log.starts.push({ node: n, when });
      n.stop = (when) => log.stops.push({ node: n, when });
      log.created.push(n);
      return n;
    },
    createBufferSource: () => {
      const n = new FakeNode('bufferSource', log);
      n.buffer = null;
      n.loop = false;
      n.start = (when) => log.starts.push({ node: n, when });
      n.stop = (when) => log.stops.push({ node: n, when });
      log.created.push(n);
      return n;
    },
    createBiquadFilter: () => {
      const n = new FakeNode('filter', log);
      n.type = 'lowpass';
      n.frequency = new FakeParam(350, 'frequency');
      n.Q = new FakeParam(1, 'Q');
      log.created.push(n);
      return n;
    },
    createDynamicsCompressor: () => {
      const n = new FakeNode('compressor', log);
      n.threshold = new FakeParam(0, 'threshold');
      n.knee = new FakeParam(0, 'knee');
      n.ratio = new FakeParam(1, 'ratio');
      n.attack = new FakeParam(0, 'attack');
      n.release = new FakeParam(0, 'release');
      log.created.push(n);
      return n;
    },
    createBuffer: (channels, length) => {
      const data = new Float32Array(length);
      log.buffers = log.buffers || [];
      log.buffers.push({ channels, length });
      return { getChannelData: () => data };
    },
  };

  // Every cue reads currentTime at the moment it fires; keep it moving so a test
  // can prove the second call is scheduled after the first rather than at 0.
  const advance = (seconds) => {
    clock += seconds;
    ctx.currentTime = clock;
  };

  return { ctx, log, advance };
}

function memoryStorage(initial = {}) {
  const map = new Map(Object.entries(initial));
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => map.set(k, String(v)),
    removeItem: (k) => map.delete(k),
    get size() {
      return map.size;
    },
  };
}

const countCreated = (log, kind) =>
  log.created.filter((n) => n.kind === kind).length;

const started = (log, kind) =>
  log.starts.filter((s) => s.node.kind === kind).length;

describe('createWheelAudio — mute preference', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('is unmuted by default', () => {
    expect(DEFAULT_MUTED).toBe(false);
    const audio = createWheelAudio({ storage: memoryStorage() });
    expect(audio.isMuted()).toBe(false);
  });

  it('reads a stored preference', () => {
    const storage = memoryStorage({ [MUTE_STORAGE_KEY]: 'true' });
    expect(createWheelAudio({ storage }).isMuted()).toBe(true);
  });

  it('treats any value other than the exact string "true" as unmuted', () => {
    for (const stored of ['1', 'yes', 'TRUE', '', 'false', 'null']) {
      const storage = memoryStorage({ [MUTE_STORAGE_KEY]: stored });
      expect(createWheelAudio({ storage }).isMuted()).toBe(false);
    }
  });

  it('persists the choice under wheel:muted', () => {
    const storage = memoryStorage();
    const audio = createWheelAudio({ storage });
    audio.setMuted(true);
    expect(storage.getItem(MUTE_STORAGE_KEY)).toBe('true');
    audio.setMuted(false);
    expect(storage.getItem(MUTE_STORAGE_KEY)).toBe('false');
  });

  it('toggles and returns the new value', () => {
    const audio = createWheelAudio({ storage: memoryStorage() });
    expect(audio.toggleMuted()).toBe(true);
    expect(audio.isMuted()).toBe(true);
    expect(audio.toggleMuted()).toBe(false);
    expect(audio.isMuted()).toBe(false);
  });

  it('lets an explicit option win over storage, for tests and for a future server flag', () => {
    const storage = memoryStorage({ [MUTE_STORAGE_KEY]: 'true' });
    expect(createWheelAudio({ storage, muted: false }).isMuted()).toBe(false);
  });

  it('survives storage that throws on every call', () => {
    const hostile = {
      getItem() {
        throw new Error('blocked');
      },
      setItem() {
        throw new Error('blocked');
      },
    };
    const audio = createWheelAudio({ storage: hostile });
    expect(audio.isMuted()).toBe(false);
    expect(() => audio.setMuted(true)).not.toThrow();
    expect(audio.isMuted()).toBe(true);
  });

  it('survives no storage at all', () => {
    const audio = createWheelAudio({ storage: null });
    expect(audio.isMuted()).toBe(false);
    expect(() => audio.setMuted(true)).not.toThrow();
  });
});

describe('createWheelAudio — muting actually silences it', () => {
  it('never builds an AudioContext while muted', () => {
    const { ctx, log } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.setMuted(true);
    audio.sFanfare();
    audio.sCrash();
    expect(audio.hasContext()).toBe(false);
    expect(log.created).toHaveLength(0);
  });

  it('plays again as soon as it is unmuted', () => {
    const { ctx, log } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.setMuted(true);
    audio.sBoom();
    audio.setMuted(false);
    audio.sBoom();
    expect(audio.hasContext()).toBe(true);
    expect(started(log, 'oscillator')).toBe(1);
  });
});

describe('createWheelAudio — no Web Audio available', () => {
  it('turns every cue into a silent no-op instead of throwing', () => {
    const audio = createWheelAudio({
      storage: null,
      createContext: () => null,
    });
    const calls = [
      () => audio.sClick(0.5),
      () => audio.sWindUp(),
      () => audio.sWhoosh(),
      () => audio.sRiser(2),
      () => audio.sBoom(),
      () => audio.sDrumroll(1),
      () => audio.sCrash(),
      () => audio.sFanfare(),
    ];
    for (const call of calls) expect(call).not.toThrow();
    expect(audio.hasContext()).toBe(false);
    expect(audio.contextState()).toBe('uninitialised');
  });

  it('resolves false from resume instead of rejecting', async () => {
    const audio = createWheelAudio({ storage: null, createContext: () => null });
    await expect(audio.resume()).resolves.toBe(false);
  });
});

describe('createWheelAudio — the bus', () => {
  it('routes master gain through a compressor into the destination', () => {
    const { ctx, log } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.sBoom();

    expect(countCreated(log, 'compressor')).toBe(1);
    const comp = log.created.find((n) => n.kind === 'compressor');
    expect(comp.threshold.value).toBe(-14);
    expect(comp.ratio.value).toBe(6);

    const master = log.created.find((n) => n.kind === 'gain');
    expect(master.outputs).toContain(comp);
    expect(comp.outputs).toContain(ctx.destination);
  });

  it('creates the graph once, not once per cue', () => {
    const { ctx, log } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.sBoom();
    audio.sClick();
    audio.sFanfare();
    expect(countCreated(log, 'compressor')).toBe(1);
  });

  it('reuses one noise buffer for every noise cue', () => {
    const { ctx, log } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.sWhoosh();
    audio.sCrash();
    expect(log.buffers).toHaveLength(1);
    // Three seconds at the context sample rate.
    expect(log.buffers[0].length).toBe(ctx.sampleRate * 3);
  });

  it('stops every source it starts', () => {
    const { ctx, log } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.sFanfare();
    audio.sDrumroll(0.5);
    expect(log.starts.length).toBe(log.stops.length);
    for (const { when } of log.stops) {
      expect(Number.isFinite(when)).toBe(true);
    }
  });
});

describe('createWheelAudio — the cues', () => {
  let fake;
  let audio;

  beforeEach(() => {
    fake = makeFake();
    audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => fake.ctx,
      rng: () => 0.5,
    });
  });

  it('sClick is a noise tick plus a triangle body', () => {
    audio.sClick(0.6);
    expect(started(fake.log, 'bufferSource')).toBe(1);
    expect(started(fake.log, 'oscillator')).toBe(1);
    const osc = fake.log.starts.find((s) => s.node.kind === 'oscillator').node;
    expect(osc.type).toBe('triangle');
  });

  it('sWindUp is a single falling sawtooth', () => {
    audio.sWindUp();
    expect(started(fake.log, 'oscillator')).toBe(1);
    const osc = fake.log.starts.find((s) => s.node.kind === 'oscillator').node;
    expect(osc.type).toBe('sawtooth');
  });

  it('sWhoosh is one bandpassed noise burst', () => {
    audio.sWhoosh();
    expect(started(fake.log, 'bufferSource')).toBe(1);
    expect(started(fake.log, 'oscillator')).toBe(0);
  });

  it('sRiser layers a looping noise sweep with a rising sine', () => {
    audio.sRiser(2);
    expect(started(fake.log, 'bufferSource')).toBe(1);
    expect(started(fake.log, 'oscillator')).toBe(1);
    const src = fake.log.starts.find((s) => s.node.kind === 'bufferSource').node;
    expect(src.loop).toBe(true);
  });

  it('sCrash is a bright noise burst and drags the boom along', () => {
    audio.sCrash();
    expect(started(fake.log, 'bufferSource')).toBe(1);
    // sCrash calls sBoom internally, so there is exactly one oscillator.
    expect(started(fake.log, 'oscillator')).toBe(1);
  });

  it('sDrumroll accelerates: more hits the longer it runs', () => {
    audio.sDrumroll(0.4);
    const short = started(fake.log, 'bufferSource');
    fake.log.starts.length = 0;
    audio.sDrumroll(1.6);
    const long = started(fake.log, 'bufferSource');
    expect(short).toBeGreaterThan(0);
    expect(long).toBeGreaterThan(short);
  });

  it('sDrumroll with a zero duration schedules nothing', () => {
    audio.sDrumroll(0);
    expect(started(fake.log, 'bufferSource')).toBe(0);
    expect(started(fake.log, 'oscillator')).toBe(0);
  });

  it('sFanfare is seven chords of three detuned saws', () => {
    audio.sFanfare();
    expect(started(fake.log, 'oscillator')).toBe(21);
    const saws = fake.log.starts
      .map((s) => s.node)
      .filter((n) => n.type === 'sawtooth');
    expect(saws).toHaveLength(21);
    // Each chord is three saws detuned by -7, 0 and +7 cents.
    expect(saws.slice(0, 3).map((n) => n.detune.value)).toEqual([-7, 0, 7]);
  });

  it('schedules later cues after earlier ones, not all at time zero', () => {
    audio.sWindUp();
    fake.advance(1);
    audio.sFanfare();
    const times = fake.log.starts.map((s) => s.when);
    expect(times.some((t) => t > 0)).toBe(true);
  });
});

describe('createWheelAudio — lifecycle', () => {
  it('resume is a no-op when the context is already running', async () => {
    const { ctx } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    await expect(audio.resume()).resolves.toBe(true);
    expect(ctx.state).toBe('running');
  });

  it('resume unlocks a suspended context', async () => {
    const { ctx } = makeFake();
    ctx.state = 'suspended';
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    await expect(audio.resume()).resolves.toBe(true);
    expect(ctx.state).toBe('running');
  });

  it('dispose closes the context and forgets the graph', async () => {
    const { ctx } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.sBoom();
    expect(audio.hasContext()).toBe(true);
    audio.dispose();
    expect(audio.hasContext()).toBe(false);
    expect(audio.contextState()).toBe('uninitialised');
    await Promise.resolve();
    expect(ctx.state).toBe('closed');
  });

  it('survives disposing twice, and disposing a context that never started', () => {
    const audio = createWheelAudio({ storage: null, createContext: () => null });
    expect(() => audio.dispose()).not.toThrow();
    expect(() => audio.dispose()).not.toThrow();
  });

  it('rebuilds a fresh context after dispose', () => {
    const { ctx } = makeFake();
    const audio = createWheelAudio({
      storage: memoryStorage(),
      createContext: () => ctx,
    });
    audio.sBoom();
    audio.dispose();
    audio.sBoom();
    expect(audio.hasContext()).toBe(true);
  });
});
