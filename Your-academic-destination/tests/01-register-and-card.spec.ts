import { test, expect } from '@playwright/test';
import { fetchOtpForPhone, fillOtp, registerStudent } from './e2e-helpers';

test.describe('F1: student registration journey', () => {
  test('register step1->otp->my-card with real OTP from queue', async ({ page }) => {
    const stamp = Date.now().toString().slice(-4);
    const fullName = 'طالب اختبار تجريبي';
    const phone = `09${stamp}${stamp}`;

    const code = await registerStudent(page, { fullName, phone });

    await expect(page).toHaveURL(/\/otp/);

    const otp = await fetchOtpForPhone(phone);
    await fillOtp(page, otp);

    await page.waitForURL('**/my-card', { timeout: 20000 });
    await expect(page.locator('.mc-status-badge')).toHaveText('بطاقتك جاهزة');
    await expect(page.locator('.mc-user-code')).toContainText(code);
    await expect(page.locator('.mc-user-name')).toContainText(fullName.split(' ')[0]);
    await expect(page.locator('.mc-qr-wrapper svg').first()).toBeVisible();

    await page.locator('.mc-btn-logout').click();
    await page.waitForURL('**/');
  });
});