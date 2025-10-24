// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

async function ensureAlternateOption(selectLocator) {
  const currentValue = await selectLocator.inputValue();
  const options = await selectLocator.locator('option').evaluateAll((nodes) =>
    nodes.map((node) => ({ value: node.value, label: node.textContent ?? '' }))
  );
  return options.find((option) => option.value && option.value !== currentValue);
}

test.describe('Selection controls integration', () => {
  test('changing selection refreshes the summary', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/`);

    const summaryHeading = page.getByTestId('variant-summary').locator('text=Showing results for');
    await expect(summaryHeading).toBeVisible();
    const initialSummaryText = (await summaryHeading.first().textContent())?.trim();

    const controlsCard = page.getByTestId('selection-controls');
    await expect(controlsCard).toBeVisible();

    const classSelect = page.getByTestId('class-select');
    const variantSelect = page.getByTestId('variant-select');

    const alternateVariant = await ensureAlternateOption(variantSelect);

    const selectionRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/selection/controls') && response.request().method() === 'GET'
    );
    const summaryRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/variant/') && !response.url().endsWith('.json')
    );

    if (alternateVariant) {
      await variantSelect.selectOption(alternateVariant.value);
    } else {
      const alternateClass = await ensureAlternateOption(classSelect);
      expect(alternateClass, 'expected at least one alternate class option').toBeDefined();
      await classSelect.selectOption(alternateClass.value);
    }

    await Promise.all([selectionRequest, summaryRequest]);

    await expect(summaryHeading).toBeVisible();
    await expect(summaryHeading.first()).not.toHaveText(initialSummaryText ?? '');
  });
});
