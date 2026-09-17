import { test, expect } from '@playwright/test';
import { SEED, teamLogin } from './e2e-helpers';

test.describe('F4: walkin codes lifecycle', () => {
  let walkinCode = '';

  test('admin generates walkin codes and they appear in incomplete list', async ({ page }) => {
    await teamLogin(page, SEED.superAdmin.username, SEED.superAdmin.password);
    await page.waitForURL('**/dashboard');

    await page.goto('/generate-walkin-code');
    await page.locator('#gwic-count-input').fill('3');
    await page.locator('.gwic-submit-btn').click();

    await expect(page.locator('.gwic-qr-code-text').first()).toBeVisible({ timeout: 15000 });
    const first = await page.locator('.gwic-qr-code-text').first().textContent();
    walkinCode = (first ?? '').trim();
    expect(walkinCode).toMatch(/^W-\d{6}$/);
    await expect(page.locator('.gwic-batch-title')).toContainText('دفعة اليوم');

    await page.goto('/gate-incomplete');
    await expect(page.getByRole('tab', { name: 'غير مكتملة', exact: true })).toHaveCount(1);
    await page.locator('.code-cell', { hasText: walkinCode }).first().waitFor({ timeout: 15000 });
  });

  test('walkin row opens data manager and completing data moves it to complete tab', async ({
    page,
  }) => {
    if (!walkinCode) test.skip();
    await teamLogin(page, SEED.studentsAdmin.username, SEED.studentsAdmin.password);
    await page.waitForURL('**/gate');
    await page.goto('/gate-incomplete');
    await page.locator('.code-cell', { hasText: walkinCode }).first().waitFor({ timeout: 15000 });

    await page
      .locator('.walkin-row, tbody tr', { hasText: walkinCode })
      .first()
      .locator('.btn-action')
      .click();
    await page.waitForURL('**/gate-manage');

    await expect(page.locator('#fullName')).toBeVisible();
    await page.locator('#fullName').fill('طالب مشي تجريبي');
    await page.locator('#phoneNumber').fill('0977777777');
    await page.locator('#birthDate').fill('2005-05-05');
    await page.locator('#certificateYear').fill('2024');
    await page.locator('#certificateType').selectOption('scientific');
    await page.locator('#baccalaureateScore').fill('85');
    await page.locator('.btn-save').click();

    await expect(page.locator('.save-feedback-message')).toContainText('تم حفظ التعديلات بنجاح', {
      timeout: 10000,
    });

    await page.goto('/gate-incomplete');
    await page.getByRole('tab', { name: 'مكتملة', exact: true }).click();
    await page.locator('.code-cell', { hasText: walkinCode }).first().waitFor({ timeout: 15000 });
  });
});