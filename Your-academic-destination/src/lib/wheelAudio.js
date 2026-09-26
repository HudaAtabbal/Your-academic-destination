/**
 * wheelAudio.js
 *
 * The Lucky Wheel sound engine, lifted from
 * docs/dashboard-reference/wheel-v4.html and decoupled from the DOM.
 *
 * Everything is synthesised at runtime through the Web Audio API: no audio
 * files, no CDN, no new dependencies. The eight cues below are the exact ones
 * the prototype already ships, so the ceremony sounds the same as the mock-up
 * while the code stays testable.
 *
 * Why a factory instead of module-level functions:
 *   - An AudioContext is expensive and browsers want one created inside a user
 *     gesture, so the caller decides when to build the engine (lazily, on the
 *     first tap) and when to tear it down (on unmount).
 *   - Tests can inject a fake context and a fake storage, which is impossible
 *     with module-level singletons.
 *
 * The prototype keeps `muted` as a bare global read by every cue. Here it is
 * engine state, persisted to localStorage so the choice survives a reload.
 */

export const MUTE_STORAGE_KEY = 'wheel:muted';

/** Default is unmuted: the ceremony is the whole point, sound is on unless asked otherwise. */
export const DEFAULT_MUTED = false;

function defaultCreateContext() {
  if (typeof window === 'undefined') return null;
  const Ctor = window.AudioContext || window.webkitAudioContext;
  if (!Ctor) return null;
  return new Ctor();
}

function defaultStorage() {
  try {
    if (typeof localStorage === 'undefined') return null;
    return localStorage;
  } catch {
    // Safari private mode and similar throw on property access.
    return null;
  }
}

function readMuted(storage) {
  if (!storage) return DEFAULT_MUTED;
  try {
    return storage.getItem(MUTE_STORAGE_KEY) === 'true';
  } catch {
    return DEFAULT_MUTED;
  }
}

function writeMuted(storage, muted) {
  if (!storage) return;
  try {
    storage.setItem(MUTE_STORAGE_KEY, muted ? 'true' : 'false');
  } catch {
    // Quota exceeded or private mode: the preference simply will not survive a
    // reload. Losing it is not worth breaking the ceremony over.
  }
}

export function createWheelAudio(options = {}) {
  const {
    createContext = defaultCreateContext,
    storage = defaultStorage(),
    muted: initialMuted,
    volume = 0.9,
    rng = Math.random,
  } = options;

  let ctx = null;
  let master = null;
  let noiseBuffer = null;
  let muted =
    initialMuted === undefined ? readMuted(storage) : Boolean(initialMuted);

  /**
   * Build the graph on first use. Returns null when the environment has no Web
   * Audio (jsdom, old browsers, SSR), which is how every cue stays a no-op in
   * tests instead of throwing.
   */
  const ensure = () => {
    if (ctx) return ctx;
    const created = createContext();
    if (!created) return null;
    ctx = created;

    // A compressor on the bus keeps eight overlapping cues from clipping when
    // the drumroll, the crash and the fanfare land on top of each other.
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14;
    comp.knee.value = 6;
    comp.ratio.value = 6;
    comp.attack.value = 0.003;
    comp.release.value = 0.2;

    master = ctx.createGain();
    master.gain.value = volume;
    master.connect(comp);
    comp.connect(ctx.destination);
    return ctx;
  };

  /** Three seconds of white noise, generated once and reused by every noise cue. */
  const noise = () => {
    if (noiseBuffer) return noiseBuffer;
    const length = Math.floor(ctx.sampleRate * 3);
    noiseBuffer = ctx.createBuffer(1, length, ctx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < length; i += 1) data[i] = rng() * 2 - 1;
    return noiseBuffer;
  };

  /**
   * Percussive envelope. exponentialRampToValueAtTime cannot touch zero, so the
   * floor is 0.0001 rather than 0 - same trick the prototype uses.
   */
  const env = (gain, t, attack, peak, decay) => {
    gain.gain.setValueAtTime(0.0001, t);
    gain.gain.exponentialRampToValueAtTime(peak, t + attack);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  };

  const guard = () => {
    if (muted) return null;
    return ensure();
  };

  /** A peg passing the pointer. level scales it down for fast crossings. */
  const sClick = (level = 1) => {
    const c = guard();
    if (!c) return;
    const t = c.currentTime;

    const src = c.createBufferSource();
    src.buffer = noise();
    const bp = c.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = 2800 + rng() * 400;
    bp.Q.value = 4;
    const g = c.createGain();
    env(g, t, 0.001, 0.85 * level, 0.035);
    src.connect(bp);
    bp.connect(g);
    g.connect(master);
    src.start(t);
    src.stop(t + 0.06);

    const osc = c.createOscillator();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(900, t);
    osc.frequency.exponentialRampToValueAtTime(300, t + 0.04);
    const g2 = c.createGain();
    env(g2, t, 0.001, 0.32 * level, 0.04);
    osc.connect(g2);
    g2.connect(master);
    osc.start(t);
    osc.stop(t + 0.06);
  };

  /** The 420ms pull-back before release: a detuned saw sliding down through a lowpass. */
  const sWindUp = () => {
    const c = guard();
    if (!c) return;
    const t = c.currentTime;

    const osc = c.createOscillator();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(120, t);
    osc.frequency.linearRampToValueAtTime(70, t + 0.4);

    const lp = c.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 600;

    const g = c.createGain();
    env(g, t, 0.05, 0.22, 0.4);

    osc.connect(lp);
    lp.connect(g);
    g.connect(master);
    osc.start(t);
    osc.stop(t + 0.5);
  };

  /** Air moving over the rim as the wheel takes off. */
  const sWhoosh = () => {
    const c = guard();
    if (!c) return;
    const t = c.currentTime;

    const src = c.createBufferSource();
    src.buffer = noise();
    const bp = c.createBiquadFilter();
    bp.type = 'bandpass';
    bp.Q.value = 1.2;
    bp.frequency.setValueAtTime(300, t);
    bp.frequency.exponentialRampToValueAtTime(3000, t + 0.5);

    const g = c.createGain();
    env(g, t, 0.08, 0.55, 0.6);

    src.connect(bp);
    bp.connect(g);
    g.connect(master);
    src.start(t);
    src.stop(t + 0.8);
  };

  /** Rising tension through the spin, noise sweep plus a sub-octave sine. */
  const sRiser = (duration) => {
    const c = guard();
    if (!c) return;
    const t = c.currentTime;

    const src = c.createBufferSource();
    src.buffer = noise();
    src.loop = true;
    const bp = c.createBiquadFilter();
    bp.type = 'bandpass';
    bp.Q.value = 3;
    bp.frequency.setValueAtTime(400, t);
    bp.frequency.exponentialRampToValueAtTime(5000, t + duration);
    const g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.25, t + duration * 0.9);
    g.gain.exponentialRampToValueAtTime(0.0001, t + duration);
    src.connect(bp);
    bp.connect(g);
    g.connect(master);
    src.start(t);
    src.stop(t + duration + 0.05);

    const osc = c.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(55, t);
    osc.frequency.exponentialRampToValueAtTime(110, t + duration);
    const g2 = c.createGain();
    g2.gain.setValueAtTime(0.0001, t);
    g2.gain.exponentialRampToValueAtTime(0.32, t + duration * 0.9);
    g2.gain.exponentialRampToValueAtTime(0.0001, t + duration);
    osc.connect(g2);
    g2.connect(master);
    osc.start(t);
    osc.stop(t + duration + 0.05);
  };

  /** The wheel stops: a sine dropping from 140Hz to 40Hz. */
  const sBoom = () => {
    const c = guard();
    if (!c) return;
    const t = c.currentTime;

    const osc = c.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(140, t);
    osc.frequency.exponentialRampToValueAtTime(40, t + 0.5);

    const g = c.createGain();
    env(g, t, 0.005, 0.9, 0.7);

    osc.connect(g);
    g.connect(master);
    osc.start(t);
    osc.stop(t + 0.8);
  };

  /**
   * Accelerating drumroll. The gap shrinks linearly while the accents grow
   * quadratically, which is what makes it read as building pressure.
   */
  const sDrumroll = (duration) => {
    const c = guard();
    if (!c) return;
    const start = c.currentTime;
    let t = start;
    let i = 0;

    while (t < start + duration) {
      const p = (t - start) / duration;
      const gap = 0.055 - 0.02 * p;

      const src = c.createBufferSource();
      src.buffer = noise();
      const hp = c.createBiquadFilter();
      hp.type = 'highpass';
      hp.frequency.value = 1500;
      const g = c.createGain();
      env(g, t, 0.002, 0.12 + 0.55 * p * p * (i % 2 ? 0.8 : 1), 0.07);
      src.connect(hp);
      hp.connect(g);
      g.connect(master);
      src.start(t);
      src.stop(t + 0.1);

      const osc = c.createOscillator();
      osc.type = 'triangle';
      osc.frequency.value = 190;
      const g2 = c.createGain();
      env(g2, t, 0.002, 0.06 + 0.25 * p * p, 0.05);
      osc.connect(g2);
      g2.connect(master);
      osc.start(t);
      osc.stop(t + 0.08);

      t += gap;
      i += 1;
    }
  };

  /** Cymbal: bright noise burst, and it drags the boom along with it. */
  const sCrash = () => {
    const c = guard();
    if (!c) return;
    const t = c.currentTime;

    const src = c.createBufferSource();
    src.buffer = noise();
    const hp = c.createBiquadFilter();
    hp.type = 'highpass';
    hp.frequency.value = 4000;
    const g = c.createGain();
    env(g, t, 0.003, 0.85, 2.4);
    src.connect(hp);
    hp.connect(g);
    g.connect(master);
    src.start(t);
    src.stop(t + 2.6);

    sBoom();
  };

  /** One brass chord: three detuned saws through a swelling lowpass. */
  const brass = (freq, offset, dur, level) => {
    const t = ctx.currentTime + offset;
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.Q.value = 2;
    lp.frequency.setValueAtTime(500, t);
    lp.frequency.linearRampToValueAtTime(3200, t + 0.08);
    lp.frequency.exponentialRampToValueAtTime(1400, t + dur);

    const g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(level, t + 0.04);
    g.gain.setValueAtTime(level, t + dur * 0.7);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);

    lp.connect(g);
    g.connect(master);

    for (const detune of [-7, 0, 7]) {
      const osc = ctx.createOscillator();
      osc.type = 'sawtooth';
      osc.frequency.value = freq;
      osc.detune.value = detune;
      osc.connect(lp);
      osc.start(t);
      osc.stop(t + dur + 0.05);
    }
  };

  /** Three rising stabs into a held major chord. */
  const sFanfare = () => {
    const c = guard();
    if (!c) return;
    const level = 0.15;
    brass(392, 0, 0.18, level);
    brass(523.25, 0.16, 0.18, level);
    brass(659.25, 0.32, 0.18, level);
    brass(783.99, 0.48, 1.8, level);
    brass(659.25, 0.48, 1.8, level * 0.8);
    brass(523.25, 0.48, 1.8, level * 0.8);
    brass(261.63, 0.48, 1.8, level * 0.9);
  };

  /**
   * Unlock audio. Browsers create the context suspended outside a user gesture,
   * so the tap that starts the ceremony must call this before the first cue.
   */
  const resume = () => {
    const c = ensure();
    if (!c) return Promise.resolve(false);
    if (c.state !== 'suspended' || typeof c.resume !== 'function') {
      return Promise.resolve(true);
    }
    return Promise.resolve(c.resume())
      .then(() => true)
      .catch(() => false);
  };

  const setMuted = (next) => {
    muted = Boolean(next);
    writeMuted(storage, muted);
    return muted;
  };

  const dispose = () => {
    const c = ctx;
    ctx = null;
    master = null;
    noiseBuffer = null;
    if (c && typeof c.close === 'function') {
      try {
        c.close();
      } catch {
        // Already closed, or closing before it ever started. Nothing to do.
      }
    }
  };

  return {
    sClick,
    sWindUp,
    sWhoosh,
    sRiser,
    sBoom,
    sDrumroll,
    sCrash,
    sFanfare,
    resume,
    dispose,
    setMuted,
    isMuted: () => muted,
    toggleMuted: () => setMuted(!muted),
    hasContext: () => ctx !== null,
    contextState: () => (ctx ? ctx.state : 'uninitialised'),
  };
}
