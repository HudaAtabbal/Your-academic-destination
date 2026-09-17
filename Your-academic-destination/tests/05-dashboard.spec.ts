import { test, expect } from '@playwright/test';
import { SEED, apiLogin, teamLogin } from './e2e-helpers';

test.describe('F5: super admin dashboard', () => {
  test('dashboard renders metric cards, team table, sms status & rooms', async ({ page }) => {
    await teamLogin(page, SEED.superAdmin.username, SEED.superAdmin.password);
    await page.waitForURL('**/dashboard');

    await expect(page.getByText('المدير العام')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.gd-dash-metric-card').first()).toBeVisible();

    await expect(page.locator('.gd-dash-sms-worker-state, .gd-dash-empty-note').first()).toBeVisible(
      { timeout: 10000 },
    );

    await expect(page.locator('.gd-dash-td-user').first()).toBeVisible({ timeout: 10000 });

    await page.locator('.gd-dash-create-btn').click();
    await page.waitForURL('**/create-team-account');
  });
});