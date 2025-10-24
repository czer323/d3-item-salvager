// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_VARIANT_ID = process.env.FRONTEND_DEFAULT_VARIANT ?? 'demo-variant';

test.describe('Variant summary dashboard', () => {
  test('renders used and salvage sections for selected variants', async ({ page }) => {
    await page.goto(`/?variant=${TEST_VARIANT_ID}`);
    await expect(page.getByTestId('variant-summary-used')).toBeVisible();
    await expect(page.getByTestId('variant-summary-salvage')).toBeVisible();
    await expect(page.getByTestId('variant-summary')).toContainText('Used by selected builds');
    await expect(page.getByTestId('variant-summary')).toContainText('Not used / Salvage candidates');
  });
});
