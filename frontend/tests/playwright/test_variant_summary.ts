// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

/**
 * Load builds, apply the selection, and return the item summary locator.
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<import('@playwright/test').Locator>}
 */
async function loadItemSummary(page) {
  await page.goto(`${TEST_BASE_URL}/`);
  await expect(page.getByTestId('selection-controls')).toBeVisible();

  const classSelect = page.getByTestId('class-multiselect');
  const firstClassValue = await classSelect.locator('option').first().getAttribute('value');
  if (firstClassValue) {
    await classSelect.selectOption(firstClassValue);
  }

  const loadRequest = page.waitForResponse(
    (response) =>
      response.url().includes('/frontend/selection/controls') &&
      response.request().method() === 'POST'
  );
  await page.getByTestId('load-builds-button').click();
  await loadRequest;

  const buildSelect = page.getByTestId('build-multiselect');
  const buildOptions = buildSelect.locator('option');
  await expect.poll(async () => await buildOptions.count(), { timeout: 10000 }).toBeGreaterThan(0);

  const buildValues = await buildOptions.evaluateAll((options) =>
    options.slice(0, Math.min(3, options.length)).map((option) => option.value)
  );
  if (buildValues.length > 0) {
    await buildSelect.selectOption(buildValues);
  }

  await page.getByTestId('apply-filter-button').click();

  const summary = page.getByTestId('item-summary');
  await expect(summary).toBeVisible({ timeout: 30000 });
  return summary;
}

test.describe('Item summary dashboard', () => {
  test('renders item usage table after applying selections', async ({ page }) => {
    const summary = await loadItemSummary(page);
    await expect(summary).toContainText('Item Usage Overview');
  });
});
