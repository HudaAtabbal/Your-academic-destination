import { test, expect } from '@playwright/test';
import { SEED, teamLogin, ensureCampusEntry, ensureTourBooking } from './e2e-helpers';

test.describe('F3: college tour station', () => {
  test('staff arrives via select-staff, scans R-9001, result shown, second scan refused', async ({
    page,
  }) => {
    await teamLogin(page, SEED.staff.username, SEED.staff.password);
    await page.waitForURL('**/select-staff');

    await page.locator('.ssp-option-card', { hasText: 'باب الكلية' }).click();
    await page.waitForURL('**/team-tour');

    await expect(page.getByRole('heading', { name: 'جولة تعريفية' })).toBeVisible();

    await ensureCampusEntry(SEED.student.code);
    await ensureTourBooking(SEED.student.code);

    await page.locator('.manual-code-input').fill(SEED.student.code);
    await page.locator('.manual-code-btn, button:has-text("تحقق")').click();

    await expect(page.locator('.scan-result-card').first()).toBeVisible();
    await expect(page.locator('.scan-result-card').first()).toContainText(SEED.student.code);

    await page.locator('.manual-code-input').fill(SEED.student.code);
    await page.locator('.manual-code-btn, button:has-text("تحقق")').click();
    await expect(page.locator('.scan-result-card').first()).toContainText('مسبقاً', {
      timeout: 10000,
    });
  });
});