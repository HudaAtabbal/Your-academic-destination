/**
 * wheel.js
 *
 * Every Lucky Wheel endpoint in one place, so no page ever hand-builds a URL.
 *
 * The eight calls map one-to-one onto the backend routes:
 *
 *   getWheelTabs()                    GET  /admin/wheel/tabs
 *   getWheelSettings(prospectiveIso?) GET  /admin/wheel/settings
 *   updateWheelSettings(freezeAt, r?) PUT  /admin/wheel/settings
 *   drawWheel(tab, idempotencyKey)    POST /admin/wheel/draws
 *   decideWheelDraw(drawId, decision) POST /admin/wheel/draws/{id}/decision
 *   getWheelArchive()                 GET  /admin/wheel/archive
 *   getCeremonySnapshot()             GET  /admin/wheel/ceremony-snapshot
 *   getWheelLive()                    GET  /wheel/live
 *
 * Two deliberate choices worth knowing about:
 *
 * 1. `getCeremonySnapshot` replaces a per-tab pool call. The backend returns all
 *    four tabs in one response, so the page needs a single request instead of
 *    four, and switching tabs becomes instant.
 *
 * 2. `drawWheel` takes the idempotency key as a required argument rather than
 *    generating one internally. The caller has to hold that key in state for
 *    the whole in-flight draw: if the network drops and the operator presses
 *    again, resending the same key returns the same draw instead of quietly
 *    awarding a second student.
 */

import { apiGet, apiPost, apiPut } from './api';

/** Tab order is the ceremony order; never derive it from object key order. */
export const WHEEL_TABS = [
  'first_prize',
  'second_prize',
  'third_prize',
  'final_prize',
];

/**
 * Backend error codes the UI has to branch on. Imported instead of inlined so a
 * typo fails the build rather than silently falling into the generic handler.
 */
export const WHEEL_ERRORS = {
  tabEmpty: 'wheel_tab_empty',
  pendingDraw: 'wheel_pending_draw_exists',
  presenceRequired: 'wheel_presence_verification_required',
  rejectionNeedsConfirmation: 'wheel_reject_confirmation_required',
};

export const getWheelTabs = () => apiGet('/admin/wheel/tabs');

/**
 * `prospectiveFreezeAt` asks the backend what a freeze time *would* mean, so the
 * settings panel can preview the effect before committing. Omitted entirely when
 * not supplied, because sending `?prospective_freeze_at=` with an empty value
 * would be a different request with different meaning.
 */
export const getWheelSettings = (prospectiveFreezeAt) => {
  if (!prospectiveFreezeAt) return apiGet('/admin/wheel/settings');
  const query = `?prospective_freeze_at=${encodeURIComponent(prospectiveFreezeAt)}`;
  return apiGet(`/admin/wheel/settings${query}`);
};

/** `reason` is optional; the backend records it for the audit trail when present. */
export const updateWheelSettings = (freezeAt, reason) => {
  const body = { freeze_at: freezeAt };
  if (reason !== undefined && reason !== null && reason !== '') {
    body.reason = reason;
  }
  return apiPut('/admin/wheel/settings', body);
};

export const drawWheel = (tab, idempotencyKey) =>
  apiPost('/admin/wheel/draws', { tab, idempotency_key: idempotencyKey });

/**
 * `decision` is `{ decision, presence_verified, confirmed }`. The caller reads
 * the required flags from the `decision_requirements` that `getWheelTabs`
 * returned rather than hard-coding them, so the backend stays the single source
 * of truth about what each tab demands.
 */
export const decideWheelDraw = (drawId, decision) =>
  apiPost(`/admin/wheel/draws/${drawId}/decision`, decision);

export const getWheelArchive = () => apiGet('/admin/wheel/archive');

export const getCeremonySnapshot = () => apiGet('/admin/wheel/ceremony-snapshot');

/**
 * The display screen polls this. It answers 200 with all six fields null when
 * there is nothing to show, so callers must not treat "no card" as an error.
 */
export const getWheelLive = () => apiGet('/wheel/live');

/**
 * A fresh idempotency key per press. `crypto.randomUUID` needs a secure context,
 * which a LAN-served build over plain http is not, hence the fallback.
 */
export const newIdempotencyKey = () => {
  const webCrypto = globalThis.crypto;
  if (webCrypto && typeof webCrypto.randomUUID === 'function') {
    return webCrypto.randomUUID();
  }
  if (webCrypto && typeof webCrypto.getRandomValues === 'function') {
    const bytes = new Uint8Array(16);
    webCrypto.getRandomValues(bytes);
    return Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  }
  return `k-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
};

/** True when `error` is an ApiError carrying `code`, for readable branching. */
export const isWheelError = (error, code) =>
  Boolean(error) && error.errorCode === code;
