// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

test.describe('Preferences persistence', () => {
  test('saves selections, restores on reload, and supports import/export', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/`);

    const controlsCard = page.getByTestId('selection-controls');
    await expect(controlsCard).toBeVisible();

    const variantCheckboxes = page.getByTestId('variant-checkbox');
    const checkboxCount = await variantCheckboxes.count();
    expect(checkboxCount, 'expected at least one variant checkbox').toBeGreaterThan(0);

    let toggleIndex = -1;
    for (let i = 0; i < checkboxCount; i += 1) {
      if (!(await variantCheckboxes.nth(i).isChecked())) {
        toggleIndex = i;
        break;
      }
    }
    test.skip(toggleIndex === -1, 'All variants already selected; unable to validate preference toggling.');

    const targetIndex = toggleIndex >= 0 ? toggleIndex : 0;
    const targetVariant = variantCheckboxes.nth(targetIndex);
    const targetVariantValue = await targetVariant.getAttribute('value');
    expect(targetVariantValue, 'variant checkbox should expose a value').toBeTruthy();

    const selectionRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/selection/controls') && response.request().method() === 'GET'
    );
    const summaryRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/variant/') && !response.url().endsWith('.json')
    );

    await targetVariant.check();

    await Promise.all([selectionRequest, summaryRequest]);

    await page.getByTestId('preferences-open-button').click();
    const modal = page.getByTestId('preferences-modal');
    await expect(modal).toBeVisible();

    await page.getByTestId('preferences-save-button').click();
    await expect(page.getByTestId('preferences-toast')).toContainText('Preferences saved');

    await page.getByTestId('preferences-close-button').click();
    await expect(modal).not.toBeVisible();

    await page.reload();
    await expect(page.getByTestId('selection-controls')).toBeVisible();
    const restoredLocator = page.locator(
      `input[type="checkbox"][name="variant_ids"][value="${targetVariantValue}"]`
    );
    await expect(restoredLocator).toBeChecked();

    await page.getByTestId('preferences-open-button').click();
    await expect(page.getByTestId('preferences-modal')).toBeVisible();
    await page.getByTestId('preferences-export-button').click();
    const editor = page.getByTestId('preferences-json-editor');
    const exportedJson = await editor.inputValue();
    expect(exportedJson.length).toBeGreaterThan(0);

    const storageKey = await page.evaluate(() => window.d3Preferences?.storageKey ?? '');
    expect(storageKey, 'preferences storage key should be defined').not.toEqual('');
    await page.evaluate((key) => localStorage.removeItem(key), storageKey);

    await page.reload();
    await expect(page.getByTestId('selection-controls')).toBeVisible();

    await page.getByTestId('preferences-open-button').click();
    await expect(page.getByTestId('preferences-modal')).toBeVisible();

    const importEditor = page.getByTestId('preferences-json-editor');
    await importEditor.fill(exportedJson);

    const importSummaryRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/variant/') && !response.url().endsWith('.json')
    );

    await page.getByTestId('preferences-import-button').click();
    await importSummaryRequest;

    await expect(page.getByTestId('preferences-toast')).toContainText('Preferences imported');
    const postImportLocator = page.locator(
      `input[type="checkbox"][name="variant_ids"][value="${targetVariantValue}"]`
    );
    await expect(postImportLocator).toBeChecked();

    await page.getByTestId('preferences-close-button').click();
  });
});
