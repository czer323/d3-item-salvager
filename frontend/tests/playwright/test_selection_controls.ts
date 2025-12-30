// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

test.describe('Selection controls integration', () => {
  test('loading builds populates the build selector', async ({ page }) => {
    await page.goto(`${TEST_BASE_URL}/`);

    const controlsCard = page.getByTestId('selection-controls');
    await expect(controlsCard).toBeVisible();

    const buildSelect = page.locator('select[name="build_ids"]');
    const initialOptionCount = await buildSelect.locator('option').count();

    const loadRequest = page.waitForResponse((response) =>
      response.url().includes('/frontend/selection/controls') && response.request().method() === 'POST'
    );

    await page.getByRole('button', { name: 'Load builds' }).click();
    await loadRequest;

    const populatedOptionCount = await buildSelect.locator('option').count();
    expect(populatedOptionCount).toBeGreaterThan(initialOptionCount);
  });
});
