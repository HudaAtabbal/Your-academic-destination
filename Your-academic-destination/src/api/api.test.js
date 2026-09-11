import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  ApiError,
  apiGet,
  apiPatch,
  apiPost,
  apiPut,
  clearAuthToken,
  getAuthToken,
  setAuthToken,
} from './api.js';

const BASE = 'http://test-backend';

const okResponse = (body = {}) => ({
  ok: true,
  status: 200,
  json: async () => body,
});

const errorResponse = (status, body) => ({
  ok: false,
  status,
  json: async () => body,
});

describe('api wrapper', () => {
  beforeEach(() => {
    sessionStorage.clear();
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
    sessionStorage.clear();
  });

  it('sends Authorization Bearer header when a token is stored', async () => {
    setAuthToken('token-123');
    fetch.mockResolvedValue(okResponse({ status: 'ok' }));

    await apiGet('/admin/accounts');

    const [url, options] = fetch.mock.calls[0];
    expect(url).toBe(`${BASE}/admin/accounts`);
    expect(options.headers.Authorization).toBe('Bearer token-123');
  });

  it('omits Authorization header when no token is stored', async () => {
    fetch.mockResolvedValue(okResponse({}));

    await apiGet('/students/register');

    const options = fetch.mock.calls[0][1];
    expect(options.headers.Authorization).toBeUndefined();
  });

  it('apiPost sends a JSON stringified body with Content-Type', async () => {
    fetch.mockResolvedValue(okResponse({ id: 1 }));

    await apiPost('/students/lookup-by-contact', { phone: '0912345678' });

    const options = fetch.mock.calls[0][1];
    expect(options.method).toBe('POST');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(options.body)).toEqual({ phone: '0912345678' });
  });

  it('returns the parsed JSON body on success', async () => {
    fetch.mockResolvedValue(okResponse({ unique_code: 'R-123456' }));

    const body = await apiGet('/students/card/R-123456');
    expect(body).toEqual({ unique_code: 'R-123456' });
  });

  it('clears the token on a 401 response', async () => {
    setAuthToken('expired-token');
    fetch.mockResolvedValue(
      errorResponse(401, { error_code: 'invalid_credentials', message: 'لازم تسجلي دخول' })
    );

    await expect(apiGet('/admin/accounts')).rejects.toThrow(ApiError);
    expect(getAuthToken()).toBeNull();
  });

  it('throws ApiError carrying the backend error payload', async () => {
    fetch.mockResolvedValue(
      errorResponse(409, {
        error_code: 'duplicate_checkin',
        message: 'سجلت حضورك مسبقاً',
        details: { unique_code: 'R-1' },
      })
    );

    let caught = null;
    try {
      await apiPost('/checkins/campus-entry', {});
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught.name).toBe('ApiError');
    expect(caught.errorCode).toBe('duplicate_checkin');
    expect(caught.message).toBe('سجلت حضورك مسبقاً');
    expect(caught.details).toEqual({ unique_code: 'R-1' });
  });

  it('falls back to generic code and message when error body has no fields', async () => {
    fetch.mockResolvedValue(errorResponse(500, null));

    let caught = null;
    try {
      await apiGet('/some/endpoint');
    } catch (err) {
      caught = err;
    }

    expect(caught.errorCode).toBe('unknown_error');
    expect(caught.message).toContain('صار خطأ غير متوقع');
  });

  it('throws network_error ApiError when fetch rejects', async () => {
    fetch.mockRejectedValue(new TypeError('Failed to fetch'));

    let caught = null;
    try {
      await apiGet('/students/register');
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught.errorCode).toBe('network_error');
  });

  it('throws timeout ApiError when the transport aborts the request', async () => {
    fetch.mockRejectedValue(new DOMException('The user aborted a request.', 'AbortError'));

    let caught = null;
    try {
      await apiGet('/slow/endpoint');
    } catch (err) {
      caught = err;
    }

    expect(caught).toBeInstanceOf(ApiError);
    expect(caught.errorCode).toBe('timeout');
  });

  it('cannot read a token as empty even after clearing', () => {
    setAuthToken('token-abc');
    expect(getAuthToken()).toBe('token-abc');
    clearAuthToken();
    expect(getAuthToken()).toBeNull();
  });

  it('apiPut and apiPatch use the expected methods', async () => {
    fetch.mockResolvedValue(okResponse({}));
    await apiPut('/bookings/1', { a: 1 });
    expect(fetch.mock.calls[0][1].method).toBe('PUT');
    await apiPatch('/admin/students/1', { a: 2 });
    expect(fetch.mock.calls[1][1].method).toBe('PATCH');
  });
});