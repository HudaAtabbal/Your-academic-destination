/**
 * wheel.test.js
 *
 * The point of this suite is the wire format, not the happy path: the exact
 * method, path and body each helper produces, plus the two places where a
 * careless implementation would silently change meaning - the optional
 * prospective-freeze query and the optional audit reason.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const apiGet = vi.fn(() => Promise.resolve({}));
const apiPost = vi.fn(() => Promise.resolve({}));
const apiPut = vi.fn(() => Promise.resolve({}));

vi.mock('./api', () => ({ apiGet, apiPost, apiPut }));

const {
  WHEEL_TABS,
  WHEEL_ERRORS,
  getWheelTabs,
  getWheelSettings,
  updateWheelSettings,
  drawWheel,
  decideWheelDraw,
  getWheelArchive,
  getCeremonySnapshot,
  getWheelLive,
  newIdempotencyKey,
  isWheelError,
} = await import('./wheel');

describe('wheel api — read endpoints', () => {
  it('lists the tabs', async () => {
    await getWheelTabs();
    expect(apiGet).toHaveBeenCalledWith('/admin/wheel/tabs');
  });

  it('reads the archive', async () => {
    await getWheelArchive();
    expect(apiGet).toHaveBeenCalledWith('/admin/wheel/archive');
  });

  it('reads the ceremony snapshot once for all four tabs', async () => {
    await getCeremonySnapshot();
    expect(apiGet).toHaveBeenCalledWith('/admin/wheel/ceremony-snapshot');
  });

  it('reads the public live feed', async () => {
    await getWheelLive();
    expect(apiGet).toHaveBeenCalledWith('/wheel/live');
  });
});

describe('wheel api — settings', () => {
  it('omits the query entirely when no preview is requested', async () => {
    await getWheelSettings();
    expect(apiGet).toHaveBeenCalledWith('/admin/wheel/settings');
  });

  it('treats an empty string as no preview', async () => {
    await getWheelSettings('');
    expect(apiGet).toHaveBeenCalledWith('/admin/wheel/settings');
  });

  it('encodes the prospective timestamp so colons cannot break the URL', async () => {
    await getWheelSettings('2026-03-15T18:30:00Z');
    expect(apiGet).toHaveBeenCalledWith(
      '/admin/wheel/settings?prospective_freeze_at=2026-03-15T18%3A30%3A00Z',
    );
  });

  it('writes the freeze time on its own', async () => {
    await updateWheelSettings('2026-03-15T18:30:00Z');
    expect(apiPut).toHaveBeenCalledWith('/admin/wheel/settings', {
      freeze_at: '2026-03-15T18:30:00Z',
    });
  });

  it('includes the audit reason when there is one', async () => {
    await updateWheelSettings('2026-03-15T18:30:00Z', 'moved earlier');
    expect(apiPut).toHaveBeenCalledWith('/admin/wheel/settings', {
      freeze_at: '2026-03-15T18:30:00Z',
      reason: 'moved earlier',
    });
  });

  it('drops a blank reason instead of sending an empty string', async () => {
    for (const blank of ['', null, undefined]) {
      apiPut.mockClear();
      await updateWheelSettings('2026-03-15T18:30:00Z', blank);
      expect(apiPut).toHaveBeenCalledWith('/admin/wheel/settings', {
        freeze_at: '2026-03-15T18:30:00Z',
      });
    }
  });
});

describe('wheel api — drawing', () => {
  it('sends the tab and the caller-supplied idempotency key', async () => {
    await drawWheel('final_prize', 'key-123');
    expect(apiPost).toHaveBeenCalledWith('/admin/wheel/draws', {
      tab: 'final_prize',
      idempotency_key: 'key-123',
    });
  });

  it('resends the very same key when asked twice, which is the whole point', async () => {
    await drawWheel('first_prize', 'key-123');
    await drawWheel('first_prize', 'key-123');
    const [, first] = apiPost.mock.calls[0];
    const [, second] = apiPost.mock.calls[1];
    expect(first.idempotency_key).toBe(second.idempotency_key);
  });
});

describe('wheel api — decisions', () => {
  it('posts to the draw-specific path and passes the body through', async () => {
    const decision = { decision: 'accept', presence_verified: true, confirmed: false };
    await decideWheelDraw(42, decision);
    expect(apiPost).toHaveBeenCalledWith('/admin/wheel/draws/42/decision', decision);
  });

  it('sends the flags the backend asked for, not hard-coded ones', async () => {
    await decideWheelDraw(7, { decision: 'reject', presence_verified: false, confirmed: true });
    expect(apiPost).toHaveBeenCalledWith('/admin/wheel/draws/7/decision', {
      decision: 'reject',
      presence_verified: false,
      confirmed: true,
    });
  });
});

describe('wheel api — constants', () => {
  it('lists the four tabs in ceremony order', () => {
    expect(WHEEL_TABS).toEqual([
      'first_prize',
      'second_prize',
      'third_prize',
      'final_prize',
    ]);
  });

  it('exposes the backend error codes verbatim', () => {
    expect(WHEEL_ERRORS).toEqual({
      tabEmpty: 'wheel_tab_empty',
      pendingDraw: 'wheel_pending_draw_exists',
      presenceRequired: 'wheel_presence_verification_required',
      rejectionNeedsConfirmation: 'wheel_reject_confirmation_required',
    });
  });
});

describe('wheel api — idempotency keys', () => {
  it('produces a non-empty key every time', () => {
    const keys = new Set(Array.from({ length: 200 }, newIdempotencyKey));
    expect(keys.size).toBe(200);
    for (const key of keys) expect(key.length).toBeGreaterThan(0);
  });

  it('uses crypto.randomUUID when it exists', () => {
    const spy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('11111111-2222-3333-[REDACTED]');
    expect(newIdempotencyKey()).toBe('11111111-2222-3333-[REDACTED]');
    spy.mockRestore();
  });

  it('still returns a key on an insecure origin with no randomUUID', () => {
    const original = globalThis.crypto.randomUUID;
    globalThis.crypto.randomUUID = undefined;
    try {
      const key = newIdempotencyKey();
      expect(typeof key).toBe('string');
      expect(key.length).toBeGreaterThan(8);
    } finally {
      globalThis.crypto.randomUUID = original;
    }
  });
});

describe('wheel api — isWheelError', () => {
  it('matches on errorCode', () => {
    expect(isWheelError({ errorCode: 'wheel_tab_empty' }, WHEEL_ERRORS.tabEmpty)).toBe(true);
    expect(isWheelError({ errorCode: 'other' }, WHEEL_ERRORS.tabEmpty)).toBe(false);
  });

  it('is safe with a missing error', () => {
    expect(isWheelError(null, WHEEL_ERRORS.tabEmpty)).toBe(false);
    expect(isWheelError(undefined, WHEEL_ERRORS.tabEmpty)).toBe(false);
  });
});

describe('wheel api — plumbing', () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = globalThis.fetch;
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ ok: true }),
      }),
    );
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('really reaches the network with the expected method and path', async () => {
    // Guards against the mock above hiding a wrong path: unmock the helper and
    // let the real apiRequest run against a stubbed fetch.
    vi.doUnmock('./api');
    vi.resetModules();
    const real = await vi.importActual('./wheel');

    await real.getWheelLive();
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = globalThis.fetch.mock.calls[0];
    expect(String(url)).toMatch(/\/wheel\/live$/);
    expect(init.method).toBe('GET');
  });
});
