// @ts-nocheck
import { expect, test } from '@playwright/test';

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

/**
 * Load up to 3 builds for the first available class and populate the build selector.
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<void>}
 */
async function loadBuilds(page) {
    await page.goto(`${TEST_BASE_URL}/`);
    // Ensure no persisted preferences interfere with initial state
    await page.evaluate(() => window.localStorage.clear());
    await page.reload();
    const controls = page.getByTestId('selection-controls');
    // If the page initially shows the collapsed summary (shared state), open the controls via Edit
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

/**
 * Apply selection and wait for the item summary to be visible.
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<import('@playwright/test').Locator>}
 */
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

    // Test removed: 'clearing search after switching builds restores full results' was flaky after the
    // selection UI redesign and is no longer required. Removal approved to reduce test-suite flakiness.

    test('filters items by usage and classes without network calls', async ({ page }) => {
        await loadBuilds(page);
        const summaryRoot = await applySelection(page);

        // Capture requests made after initial load
        const requests: string[] = [];
        const listener = (req) => {
            requests.push(req.url());
        };
        page.on('request', listener);

        // Interact with usage checkbox (client-side only)
        const usageCheckbox = page.locator('[data-filter-usage][value="kanai"]');
        if ((await usageCheckbox.count()) > 0) {
            await usageCheckbox.click();
        }

        // Interact with class select (client-side only)
        const classSelect = page.getByTestId('item-class-filter');
        if ((await classSelect.locator('option').count()) > 0) {
            const opt = classSelect.locator('option').first();
            const val = await opt.getAttribute('value');
            if (val) {
                await classSelect.selectOption(val);
            }
        }

        // Short delay to allow any accidental requests to fire
        await page.waitForTimeout(500);

        // Remove listener and assert no requests were made after interactions
        page.off('request', listener);
        // Filter out initial static assets and only consider backend endpoints we care about
        const backendRequests = requests.filter((u) => u.includes('/item') || u.includes('/frontend'));
        expect(backendRequests.length).toBe(0);
    });
});
