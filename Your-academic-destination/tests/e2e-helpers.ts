import fs from 'node:fs';
import path from 'node:path';
import { expect, request, type Page, type APIRequestContext } from '@playwright/test';

export const API_BASE = process.env.E2E_API_BASE ?? 'http://localhost:8000';

interface E2eSecrets {
  workerToken?: string;
  accounts?: Record<string, string>;
}

function loadSecrets(): E2eSecrets {
  const candidates = [
    '.e2e-secrets.json',
    path.join('Your-academic-destination', '.e2e-secrets.json'),
  ];
  for (const candidate of candidates) {
    try {
      return JSON.parse(fs.readFileSync(candidate, 'utf8')) as E2eSecrets;
    } catch {
      // try the next candidate
    }
  }
  return {};
}

const secrets = loadSecrets();

function accountPassword(username: string, envVar: string): string {
  return process.env[envVar] ?? secrets.accounts?.[username] ?? '';
}

export const SEED = {
  studentsAdmin: { username: 'sedra_admin', password: accountPassword('sedra_admin', 'E2E_STUDENTS_ADMIN_PASSWORD') },
  superAdmin: { username: 'taher_super', password: accountPassword('taher_super', 'E2E_SUPER_ADMIN_PASSWORD') },
  staff: { username: 'rima_staff', password: accountPassword('rima_staff', 'E2E_STAFF_PASSWORD') },
  gate: { username: 'hadi_gate', password: accountPassword('hadi_gate', 'E2E_GATE_PASSWORD') },
  student: { code: 'R-009001' },
};

const WORKER_TOKEN = process.env.E2E_WORKER_TOKEN ?? secrets.workerToken ?? '';

async function makeApi(): Promise<APIRequestContext> {
  return request.newContext({ baseURL: API_BASE });
}

export async function apiLogin(username: string, password: string): Promise<string> {
  if (!password) {
    throw new Error(
      `Missing password for ${username}: add it to .e2e-secrets.json or set the matching E2E_* env var`,
    );
  }
  const api = await makeApi();
  const res = await api.post('/auth/login', { data: { username, password } });
  expect(res.ok(), `login ${username} => ${res.status()}`).toBeTruthy();
  const body = await res.json();
  await api.dispose();
  return body.access_token as string;
}

export async function teamLogin(page: Page, username: string, password: string) {
  await page.goto('/team-log');
  await page.locator('#username').fill(username);
  await page.locator('#password').fill(password);
  await page.locator('.btn.btn-primary').click();
}

export async function apiPost(path: string, token: string, data: unknown): Promise<number> {
  const api = await makeApi();
  const res = await api.post(path, { data, headers: { Authorization: `Bearer ${token}` } });
  const status = res.status();
  await api.dispose();
  return status;
}

/** Ensure the student has a campus entry for today (idempotent; tolerates an existing one). */
export async function ensureCampusEntry(code: string): Promise<void> {
  const token = await apiLogin(SEED.studentsAdmin.username, SEED.studentsAdmin.password);
  const status = await apiPost('/checkins/campus-entry', token, { unique_code: code });
  expect([201, 409], `campus-entry => ${status}`).toContain(status);
}

/** Ensure the staff's college holds a tour booking for the student (idempotent; tolerates an existing one). */
export async function ensureTourBooking(code: string): Promise<void> {
  const token = await apiLogin(SEED.staff.username, SEED.staff.password);
  const status = await apiPost('/bookings/tour', token, { unique_code: code });
  expect([201, 409], `tour booking => ${status}`).toContain(status);
}

/** Fetch the newest pending OTP job from the internal SMS queue (simulates local sender). */
export async function fetchOtpForPhone(phone: string): Promise<string> {
  if (!WORKER_TOKEN) {
    throw new Error('Missing worker token: set E2E_WORKER_TOKEN or workerToken in .e2e-secrets.json');
  }
  const api = await makeApi();
  const res = await api.post('/internal/sms/dequeue?batch=10', {
    headers: { Authorization: `Bearer ${WORKER_TOKEN}` },
  });
  expect(res.ok(), `dequeue => ${res.status()}`).toBeTruthy();
  const items = (await res.json()) as Array<{ job_id: string; phone: string; otp_code: string }>;
  await api.dispose();
  const job = items.find((it) => it.phone === phone48(phone));
  expect(job, `no OTP job for ${phone} in queue`).toBeTruthy();
  return job?.otp_code ?? '';
}

function phone48(phone: string): string {
  return phone.replace(/^0/, '963');
}

export async function fillOtp(page: Page, otp: string) {
  for (let i = 0; i < 4; i++) {
    await page.locator('.otp-input').nth(i).fill(otp[i] ?? '0');
  }
}

export async function clearSession(page: Page, url = '/team-log') {
  await page.goto(url);
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/** Complete a forced registration for a fresh student code and return its unique code. */
export async function registerStudent(
  page: Page,
  opts: { fullName: string; phone: string; major?: string },
): Promise<string> {
  await clearSession(page);
  await page.goto('/register-step1');

  await page.locator('#fullName').fill(opts.fullName);
  const [day, month, year] = ['01', '12', '2005'];
  const dateInputs = page.locator('.date-input-small');
  await dateInputs.nth(0).fill(day);
  await dateInputs.nth(1).fill(month);
  await dateInputs.nth(2).fill(year);
  await page.locator('#certificateYear').fill('2024');
  await page.locator('.type-btn').first().click();
  await page.locator('#averageScore').fill('85');
  await page.locator('.btn.btn-primary').click();
  await page.waitForURL('**/register-step2');

  await page.locator('.major-search-input').fill(opts.major ?? 'هندسة اتصالات');
  await page.locator('.major-list-item').first().click();
  await page.locator('.btn.btn-primary').click();
  await page.waitForURL('**/register-step3');

  await page.locator('#phoneNumber').fill(opts.phone);
  await page.locator('.rs3-btn.rs3-btn-primary').click();
  await page.waitForURL('**/otp');

  const code = await page.evaluate(() => localStorage.getItem('studentCode'));
  expect(code, 'studentCode saved to localStorage').toBeTruthy();
  return code ?? '';
}