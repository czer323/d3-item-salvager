// @ts-nocheck
import { test, expect } from '@playwright/test';

test.describe('Item summary dashboard', () => {
  test('renders item usage table after applying selections', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Load builds' }).click();
    await page.getByRole('button', { name: 'Apply filter' }).click();
    await expect(page.getByTestId('item-summary')).toBeVisible();
    await expect(page.getByTestId('item-summary')).toContainText('Item Usage Overview');
  });
});
