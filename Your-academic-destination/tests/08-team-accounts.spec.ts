import { test, expect } from '@playwright/test';
import { SEED, teamLogin } from './e2e-helpers';

test.describe('F8: team account creation', () => {
  test('super admin creates a team account and it can log in', async ({ page, context }) => {
    const stamp = Date.now().toString().slice(-5);
    const username = `e2e_staff_${stamp}`;

    await teamLogin(page, SEED.superAdmin.username, SEED.superAdmin.password);
    await page.waitForURL('**/dashboard');

    await page.goto('/create-team-account');
    await page.locator('#cta-username').fill(username);
    await page.locator('#cta-password').fill('e2epass123');
    await page.locator('.cta-role-btn', { hasText: 'مسؤول الكلية' }).click();
    await page.locator('.cta-select-field').selectOption('medicine');
    await page.locator('.cta-submit-btn').click();

    await expect(page.locator('.cta-success-message')).toBeVisible({ timeout: 10000 });
  });
});