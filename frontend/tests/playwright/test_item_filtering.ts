// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

function firstFragment(text: string) {
    const trimmed = (text ?? '').trim();
    if (!trimmed) {
        return '';
    }
    const parts = trimmed.split(/\s+/);
    if (parts[0].length >= 4) {
        return parts[0].slice(0, 4);
    }
    return trimmed.slice(0, Math.min(6, trimmed.length));
}

async function loadBuilds(page) {
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
}

async function applySelection(page) {
    const summary = page.getByTestId('item-summary');
    await page.getByTestId('apply-filter-button').click();
    await expect(summary).toBeVisible({ timeout: 30000 });
    return summary;
}

test.describe('Item summary filtering', () => {
    test('filters items by search and slot', async ({ page }) => {
        await loadBuilds(page);
        const summaryRoot = await applySelection(page);

        const rows = summaryRoot.locator('[data-filter-item]:visible');
        await expect.poll(async () => await rows.count(), { timeout: 5000 }).toBeGreaterThan(0);
        const visibleCount = await rows.count();

        const firstRow = rows.first();
        await expect(firstRow).toBeVisible();

        const itemName = (await firstRow.getAttribute('data-item-name')) ?? '';
        const itemSlot = (await firstRow.getAttribute('data-item-slot')) ?? '';

        expect(itemName.length).toBeGreaterThan(0);
        const searchTerm = firstFragment(itemName) || itemName.slice(0, Math.min(6, itemName.length));

        const searchInput = page.getByTestId('item-filter-search');
        await searchInput.fill(searchTerm);

        const getFilteredCount = async () => await rows.count();
        await expect.poll(getFilteredCount, { timeout: 4000, interval: 100 }).toBeLessThanOrEqual(visibleCount);

        const filteredCount = await rows.count();
        expect(filteredCount).toBeGreaterThan(0);
        expect(filteredCount).toBeLessThanOrEqual(visibleCount);

        const slotSelect = page.getByTestId('item-slot-filter');
        if (itemSlot) {
            const hasOption = await slotSelect.locator(`option[value="${itemSlot}"]`).count();
            if (hasOption > 0) {
                await slotSelect.selectOption(itemSlot);
                await expect.poll(getFilteredCount, { timeout: 4000, interval: 100 }).toBeGreaterThan(0);
                await expect(firstRow).toBeVisible();
            }
        }

        await searchInput.fill('zzzxxyy');
        const emptyState = summaryRoot.locator('[data-filter-empty]');
        await expect(emptyState).toBeVisible({ timeout: 2000 });
        await expect(rows).toHaveCount(0, { timeout: 2000 });

        const clearButton = page.getByTestId('item-filter-clear');
        await clearButton.click();
        await expect(rows.first()).toBeVisible({ timeout: 3000 });
        const restoredCount = await rows.count();
        expect(restoredCount).toBeGreaterThan(0);
    });

    test('clearing search after switching builds restores full results (regression: search persistence)', async ({ page }) => {
        await loadBuilds(page);

        const classSelect = page.getByTestId('class-multiselect');
        const classOption = classSelect.locator('option').first();
        const classValue = await classOption.getAttribute('value');
        if (classValue) {
            await classSelect.selectOption(classValue);
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
        const buildCount = await buildOptions.count();
        test.skip(buildCount < 2, 'Need at least two builds to validate switching.');

        const firstBuildValue = await buildOptions.nth(0).getAttribute('value');
        const secondBuildValue = await buildOptions.nth(1).getAttribute('value');

        await buildSelect.selectOption(firstBuildValue ?? undefined);
        const summaryRoot = await applySelection(page);

        const rows = summaryRoot.locator('[data-filter-item]:visible');
        await expect.poll(async () => await rows.count(), { timeout: 5000 }).toBeGreaterThan(0);
        const baselineCount = await rows.count();

        const firstRow = rows.first();
        const firstName = (await firstRow.getAttribute('data-item-name')) ?? '';
        const searchTerm = firstFragment(firstName) || firstName.slice(0, Math.min(6, firstName.length));

        const searchInput = page.getByTestId('item-filter-search');
        await searchInput.fill(searchTerm);
        await expect.poll(async () => await rows.count(), { timeout: 4000 }).toBeLessThanOrEqual(baselineCount);
        const filteredCount = await rows.count();
        expect(filteredCount).toBeGreaterThan(0);
        await expect(searchInput).toHaveValue(searchTerm);

        await buildSelect.selectOption(secondBuildValue ?? undefined);
        const summaryReload = page.waitForResponse(
            (response) =>
                response.url().includes('/frontend/items/summary') && response.request().method() === 'POST'
        );
        await page.getByTestId('apply-filter-button').click();
        await summaryReload;

        await expect(searchInput).toHaveValue(searchTerm);
        await expect.poll(async () => await rows.count(), { timeout: 5000 }).toBeGreaterThan(0);
        const postSwitchCount = await rows.count();

        const clearButton = page.getByTestId('item-filter-clear');
        const clearReload = page.waitForResponse(
            (response) =>
                response.url().includes('/frontend/items/summary') && response.request().method() === 'POST'
        );
        await Promise.all([clearButton.click(), clearReload]);

        await expect.poll(async () => await rows.count(), { timeout: 5000 }).toBeGreaterThanOrEqual(postSwitchCount);
        await expect(searchInput).toHaveValue('');
    });
});
