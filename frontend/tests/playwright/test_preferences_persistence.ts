// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

async function findAlternateOption(selectLocator) {
  const currentValue = await selectLocator.inputValue();
  const options = await selectLocator
    .locator('option')
    .evaluateAll((nodes) =>
      nodes.map((node) => ({ value: node.value, label: node.textContent ?? '' }))
    );
  return options.find((option) => option.value && option.value !== currentValue) ?? null;
}

test.describe('Preferences persistence', () => {
  test('saves selections, restores on reload, and supports import/export', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/`);

    const controlsCard = page.getByTestId('selection-controls');
    await expect(controlsCard).toBeVisible();

    const classSelect = page.getByTestId('class-select');
    const variantSelect = page.getByTestId('variant-select');

    const alternateVariant = await findAlternateOption(variantSelect);
    const targetVariantValue = alternateVariant
      ? alternateVariant.value
      : await variantSelect.inputValue();

    const selectionRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/selection/controls') && response.request().method() === 'GET'
    );
    const summaryRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/variant/') && !response.url().endsWith('.json')
    );

    if (alternateVariant) {
      await variantSelect.selectOption(alternateVariant.value);
    } else {
      const alternateClass = await findAlternateOption(classSelect);
      expect(alternateClass, 'expected at least one alternate class option').toBeTruthy();
      await classSelect.selectOption(alternateClass.value);
    }

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
    await expect(page.getByTestId('variant-select')).toHaveValue(targetVariantValue);

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
    await expect(page.getByTestId('variant-select')).toHaveValue(targetVariantValue);

    await page.getByTestId('preferences-close-button').click();
  });
});
