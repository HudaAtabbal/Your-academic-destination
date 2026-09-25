import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import usePageVisit from './usePageVisit';
import { apiPost } from '../api/api';

vi.mock('../api/api', () => ({ apiPost: vi.fn() }));

const START = '/students/page-visit/start';
const END = '/students/page-visit/end';

function paths() {
  return apiPost.mock.calls.map((c) => c[0]);
}

function setVisible(state) {
  Object.defineProperty(document, 'visibilityState', {
    configurable: true,
    get: () => state,
  });
}

// المؤقتات مزوّرة، فلازم نلفّ التقدّم بـ act غير متزامن عشان الـ promises
// بتنفّذ — بدونها visit_id ما بيكون وصل بعد.
async function advance(ms) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}

describe('usePageVisit', () => {
  beforeEach(() => {
    localStorage.clear();
    apiPost.mockReset();
    apiPost.mockResolvedValue({ visit_id: 7, entered_at: '2026-09-26T10:00:00' });
    vi.useFakeTimers();
    setVisible('visible');
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('does nothing while the tab is inactive', async () => {
    renderHook(() => usePageVisit(false, 'academic-guide'));
    await advance(10_000);
    expect(apiPost).not.toHaveBeenCalled();
  });

  it('waits 3 seconds of visible time before starting a visit', async () => {
    renderHook(() => usePageVisit(true, 'academic-guide'));

    await advance(2000);
    expect(paths()).not.toContain(START);

    await advance(1500);
    expect(paths()).toContain(START);
  });

  it('never starts while the tab is hidden, however long it stays hidden', async () => {
    renderHook(() => usePageVisit(true, 'academic-guide'));
    setVisible('hidden');

    await advance(30_000);
    expect(paths()).not.toContain(START);
  });

  it('sends the page and a stable visitor id', async () => {
    renderHook(() => usePageVisit(true, 'academic-guide'));
    await advance(4000);

    const body = apiPost.mock.calls.find((c) => c[0] === START)[1];
    expect(body.page).toBe('academic-guide');
    expect(body.visitor_id).toBeTruthy();
    // نفس المعرّف بيتخزّن بالمتصفح وبيضل ثابت بين الفتحات.
    expect(localStorage.getItem('pageVisitVisitorId')).toBe(body.visitor_id);
  });

  it('starts only once no matter how long the student stays', async () => {
    renderHook(() => usePageVisit(true, 'academic-guide'));
    await advance(30_000);
    expect(paths().filter((p) => p === START)).toHaveLength(1);
  });

  it('ends the visit on unmount with no duration field', async () => {
    const { unmount } = renderHook(() => usePageVisit(true, 'academic-guide'));
    await advance(4000);

    await act(async () => {
      unmount();
    });
    const end = apiPost.mock.calls.find((c) => c[0] === END);
    expect(end).toBeTruthy();
    // المدّة ما بتيجي من المتصفح — المخطط ما بيقبل أصلاً هيك حقل.
    expect(end[1]).toEqual({ visit_id: 7 });
  });

  it('ends the visit when the tab is hidden, then starts a new one on return', async () => {
    renderHook(() => usePageVisit(true, 'academic-guide'));
    await advance(4000);

    setVisible('hidden');
    await act(async () => {
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect(paths().filter((p) => p === END)).toHaveLength(1);

    setVisible('visible');
    await advance(4000);
    expect(paths().filter((p) => p === START)).toHaveLength(2);
  });

  it('survives a failing backend without throwing', async () => {
    apiPost.mockRejectedValue(new Error('network'));
    const { unmount } = renderHook(() => usePageVisit(true, 'academic-guide'));
    await advance(4000);
    await expect(
      act(async () => {
        unmount();
      })
    ).resolves.toBeUndefined();
  });
});
