// @ts-nocheck
import { expect, test } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const BASE = `http://127.0.0.1:${TEST_PORT}`;

async function loadBuilds(page) {
    await page.goto(BASE);
    await page.evaluate(() => window.localStorage.clear());
    await page.reload();
    const controls = page.getByTestId('selection-controls');
    if ((await controls.count()) === 0) {
        const editBtn = page.getByTestId('selection-edit-button');
        await expect(editBtn).toBeVisible({ timeout: 5000 });
        await editBtn.click();
        await expect(controls).toBeVisible({ timeout: 5000 });
    } else {
        await expect(controls).toBeVisible();
    }

    const classSelect = page.getByTestId('class-multiselect');
    const firstClassValue = await classSelect.locator('option').first().getAttribute('value');
    if (firstClassValue) {
        await classSelect.selectOption(firstClassValue);
    }

    const loadRequest = page.waitForResponse(
        (response) => response.url().includes('/frontend/selection/controls') && response.request().method() === 'POST'
    );
    await page.getByTestId('load-builds-button').click();
    await loadRequest;

    const buildSelect = page.getByTestId('build-multiselect');
    const buildOptions = buildSelect.locator('option');
    await expect.poll(async () => await buildOptions.count(), { timeout: 10000 }).toBeGreaterThan(0);

    const buildValues = await buildOptions.evaluateAll((options) => options.slice(0, Math.min(3, options.length)).map((option) => option.value));
    if (buildValues.length > 0) {
        await buildSelect.selectOption(buildValues);
    }
}

async function applySelection(page) {
    const summary = page.getByTestId('item-summary');
    await page.getByTestId('apply-filter-button').click();
    await expect(summary).toBeVisible({ timeout: 30000 });
    return summary;
}

test('items are displayed alphabetically by name', async ({ page }) => {
    await loadBuilds(page);
    const summaryRoot = await applySelection(page);

    const rows = summaryRoot.locator('[data-filter-item]:visible');
    await expect.poll(async () => await rows.count(), { timeout: 10000 }).toBeGreaterThan(0);

    // Ensure there is no interactive sort button for Item
    await expect(summaryRoot.getByRole('button', { name: 'Item' })).toHaveCount(0);

    // Collect the first td of each row (item name) and verify alphabetical order (case-insensitive)
    const names = await rows.locator('td:nth-child(1)').allInnerTexts();
    const normalized = names.map(n => n.trim().toLowerCase());
    const sorted = [...normalized].sort((a, b) => a.localeCompare(b));
    expect(normalized).toEqual(sorted);
});
