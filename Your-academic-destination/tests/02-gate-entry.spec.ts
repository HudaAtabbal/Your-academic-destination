import { test, expect } from '@playwright/test';
import { SEED, apiLogin, clearSession, teamLogin } from './e2e-helpers';

test.describe('F2: gate entry with today-reset protection', () => {
  test('students_admin logs in, scans R-9001, sees success, duplicate blocked + logout', async ({
    page,
  }) => {
    await teamLogin(page, SEED.studentsAdmin.username, SEED.studentsAdmin.password);
    await page.waitForURL('**/gate');

    await expect(page.getByRole('heading', { name: 'بوابة الجامعة' })).toBeVisible();
    await expect(page.locator('.uniGate-statValue')).toContainText(/^\d+(\.\d+)?$/);

    await page.locator('.manual-code-input').fill(SEED.student.code);
    await page.locator('.manual-code-btn').click();
    await page.waitForURL('**/gate-entry-success');

    await expect(page.locator('.success-title')).toHaveText('تم تسجيل الدخول');
    await expect(page.locator('.meta-id')).toContainText(SEED.student.code);

    await page.locator('.gate-meta, .meta-id').getByText(SEED.student.code).isVisible();

    await page.goto('/gate');
    await page.waitForURL('**/gate');

    await page.locator('.manual-code-input').fill(SEED.student.code);
    await page.locator('.manual-code-btn').click();

    const toast = page.locator('.toast-item');
    await expect(toast.first()).toBeVisible({ timeout: 10000 });

    await page.locator('.uniGate-logoutBtn').click();
    await page.waitForURL('**/team-log');
  });

  test('gate_scanner gets stadium landing', async ({ page }) => {
    await teamLogin(page, SEED.gate.username, SEED.gate.password);
    await page.waitForURL('**/team-stadium');
  });
});