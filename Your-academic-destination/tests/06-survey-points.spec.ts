import { test, expect } from '@playwright/test';
import { SEED } from './e2e-helpers';

test.describe('F6: student survey + points', () => {
  test('registered student completes survey then views points', async ({ page }) => {
    await page.goto('/my-card');
    await page.evaluate((code) => {
      localStorage.setItem('studentCode', code);
      localStorage.setItem('studentName', 'طالب تجريبي');
    }, SEED.student.code);

    await page.goto('/survey');
    await expect(page.locator('.question-title').first()).toContainText('١');

    await page.locator('.chip-btn', { hasText: 'تأكّد اللي كنت ناويه' }).click();
    await page.locator('.custom-select').selectOption('medicine');

    await page.locator('.btn.btn-primary').click();
    await page.waitForURL('**/my-card');

    await page.goto('/my-points');
    await expect(page.locator('.score-value')).toContainText(/\d+/, { timeout: 10000 });
  });
});