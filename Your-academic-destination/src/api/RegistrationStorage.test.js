import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearRegistrationData,
  getRegistrationData,
  updateRegistrationData,
} from './RegistrationStorage';

const STORAGE_KEY = 'registrationData';

describe('RegistrationStorage', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-01-01T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
    localStorage.clear();
  });

  it('returns empty object when nothing is stored', () => {
    expect(getRegistrationData()).toEqual({});
  });

  it('returns empty object for malformed JSON and does not throw', () => {
    localStorage.setItem(STORAGE_KEY, '{not-valid-json');
    expect(getRegistrationData()).toEqual({});
  });

  it('clears stored data if updatedAt is missing (old-format data)', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ fullName: 'خالد' }));
    expect(getRegistrationData()).toEqual({});
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('strips updatedAt from returned data', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ fullName: 'خالد', updatedAt: Date.now() })
    );
    expect(getRegistrationData()).toEqual({ fullName: 'خالد' });
  });

  it('treats expired data as empty and clears it', () => {
    const now = Date.now();
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ fullName: 'قديم', updatedAt: now - 25 * 60 * 60 * 1000 })
    );
    expect(getRegistrationData()).toEqual({});
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('keeps fresh data inside the 24h window', () => {
    const now = Date.now();
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ fullName: 'خالد', updatedAt: now - 60 * 60 * 1000 })
    );
    expect(getRegistrationData()).toEqual({ fullName: 'خالد' });
  });

  it('merges fields cumulatively on update', () => {
    updateRegistrationData({ fullName: 'خالد' });
    updateRegistrationData({ phone: '0912345678' });

    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
    expect(stored).toMatchObject({ fullName: 'خالد', phone: '0912345678' });
    expect(stored.updatedAt).toBeTypeOf('number');
  });

  it('update returns the merged data without updatedAt', () => {
    const result = updateRegistrationData({ fullName: 'خالد' });
    expect(result).toEqual({ fullName: 'خالد' });
    expect(result.updatedAt).toBeUndefined();
  });

  it('override wins over existing value when keys collide', () => {
    updateRegistrationData({ fullName: 'خالد' });
    const result = updateRegistrationData({ fullName: 'سارا' });
    expect(result).toEqual({ fullName: 'سارا' });
  });

  it('clear removes the stored key entirely', () => {
    updateRegistrationData({ fullName: 'خالد' });
    clearRegistrationData();
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    expect(getRegistrationData()).toEqual({});
  });
});