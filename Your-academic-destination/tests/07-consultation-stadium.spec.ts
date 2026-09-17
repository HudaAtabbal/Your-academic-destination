import { test, expect } from '@playwright/test';
import { SEED, teamLogin } from './e2e-helpers';

test.describe('F7: stadium (gate_scanner) + consultation (staff)', () => {
  test('gate scanner lands on stadium and scans lecture', async ({ page }) => {
    await teamLogin(page, SEED.gate.username, SEED.gate.password);
    await page.waitForURL('**/team-stadium');

    await expect(page.getByRole('heading', { name: 'مسح عند المدرج' })).toBeVisible();
    await page.locator('.lecture-select').selectOption('lecture_1');

    await page.locator('.manual-code-input').fill(SEED.student.code);
    await page.locator('.manual-code-btn, button:has-text("تحقق")').click();

    await expect(page.locator('.scan-result-card').first()).toContainText(SEED.student.code, {
      timeout: 10000,
    });
  });

  test('staff scans consultation for R-9001', async ({ page }) => {
    await teamLogin(page, SEED.staff.username, SEED.staff.password);
    await page.waitForURL('**/select-staff');
    await page.locator('.ssp-option-card', { hasText: 'باب الاستشارة' }).click();
    await page.waitForURL('**/team-consultation');

    await expect(page.getByRole('heading', { name: 'استشارة فردية' })).toBeVisible();

    await page.locator('.manual-code-input').fill(SEED.student.code);
    await page.locator('.manual-code-btn, button:has-text("تحقق")').click();

    await expect(page.locator('.scan-result-card').first()).toContainText(SEED.student.code, {
      timeout: 10000,
    });
  });
});