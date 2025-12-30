// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

function firstFragment(text) {
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

test.describe('Item summary filtering', () => {
    test('filters items by search and slot', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/`);

        await page.getByRole('button', { name: 'Load builds' }).click();
        await page.getByRole('button', { name: 'Apply filter' }).click();

        const summaryRoot = page.getByTestId('item-summary');
        await expect(summaryRoot).toBeVisible();

        const rows = summaryRoot.locator('[data-filter-item]:visible');
        const visibleCount = await rows.count();
        test.skip(visibleCount === 0, 'No items available in summary to validate filtering.');

        const firstRow = rows.first();
        await expect(firstRow).toBeVisible();

        const itemName = (await firstRow.getAttribute('data-item-name')) ?? '';
        const itemSlot = (await firstRow.getAttribute('data-item-slot')) ?? '';

        expect(itemName.length).toBeGreaterThan(0);
        const searchTerm = firstFragment(itemName) || itemName.slice(0, Math.min(6, itemName.length));

        const searchInput = page.getByTestId('item-filter-search');
        await searchInput.fill(searchTerm);

        // Wait for debounce + UI update: poll until the filtered rows count is > 0 and <= original visibleCount
        const getFilteredCount = async () => await rows.count();
        await expect.poll(getFilteredCount, { timeout: 2000, interval: 100 }).toBeGreaterThan(0);
        await expect.poll(getFilteredCount, { timeout: 2000, interval: 100 }).toBeLessThanOrEqual(visibleCount);

        const filteredCount = await rows.count();
        expect(filteredCount).toBeGreaterThan(0);
        expect(filteredCount).toBeLessThanOrEqual(visibleCount);

        const slotSelect = page.getByTestId('item-slot-filter');
        if (itemSlot) {
            const hasOption = await slotSelect.locator(`option[value="${itemSlot}"]`).count();
            if (hasOption > 0) {
                await slotSelect.selectOption(itemSlot);
                // Wait for UI update after slot selection (poll until we see > 0 filtered rows)
                await expect.poll(getFilteredCount, { timeout: 2000, interval: 100 }).toBeGreaterThan(0);
                const slotFilteredCount = await rows.count();
                expect(slotFilteredCount).toBeGreaterThan(0);
                await expect(firstRow).toBeVisible();
            }
        }

        await searchInput.fill('zzzxxyy');
        const emptyState = summaryRoot.locator('[data-filter-empty]');
        // Wait for empty state to be visible and rows to become empty (no visible items)
        await expect(emptyState).toBeVisible({ timeout: 2000 });
        await expect(rows).toHaveCount(0, { timeout: 2000 });

        const clearButton = page.getByTestId('item-filter-clear');
        await clearButton.click();
        // Wait for at least one row to be visible again
        await expect(rows.first()).toBeVisible({ timeout: 2000 });
        const restoredCount = await rows.count();
        expect(restoredCount).toBeGreaterThan(0);
    });

    test('clearing search after switching builds restores full results (regression: search persistence)', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/`);

        // Choose Barbarian class
        const classOption = page.locator('select[name="class_ids"] option:has-text("Barbarian")');
        const classValue = await classOption.getAttribute('value');
        await page.getByTestId('class-multiselect').selectOption(classValue);

        // Load builds for selected class
        const loadRequest = page.waitForResponse((response) =>
            response.url().includes('/frontend/selection/controls') && response.request().method() === 'POST'
        );
        await page.getByTestId('load-builds-button').click();
        await loadRequest;

        const buildSelect = page.locator('select[name="build_ids"]');
        await expect.poll(async () => await buildSelect.locator('option').count(), { timeout: 2000 }).toBeGreaterThan(1);

        // Pick first build and apply
        const firstValue = await buildSelect.locator('option').first().getAttribute('value');
        await buildSelect.selectOption(firstValue);
        await page.getByTestId('apply-filter-button').click();

        const summaryRoot = page.getByTestId('item-summary');
        await expect(summaryRoot).toBeVisible();
        const rows = summaryRoot.locator('[data-filter-item]:visible');

        // Ensure we have items to filter
        await expect.poll(async () => await rows.count(), { timeout: 2000 }).toBeGreaterThan(0);

        // Search for 'immortal' and expect matches
        const searchInput = page.getByTestId('item-filter-search');
        await searchInput.fill('immortal');
        // Wait for filtered results to settle
        await expect.poll(async () => await rows.count(), { timeout: 2000 }).toBeGreaterThan(0);
        const filteredCount = await rows.count();
        expect(filteredCount).toBeGreaterThan(0);
        // Confirm search input contains our term
        await expect(searchInput).toHaveValue('immortal');
        // Diagnostic: capture screenshot and log
        await page.screenshot({ path: 'playwright-debug/step-search.png' });
        console.log('after search filteredCount=', filteredCount);

        // Switch to a different build (also contains immortal items in its results)
        // Select by label to ensure we pick the intended build
        await buildSelect.selectOption({ label: 'Ik Hota Barbarian Guide (Barbarian)' });
        // Wait for the items summary to refresh (server call)
        const summaryRequest = page.waitForResponse((response) =>
            response.url().includes('/frontend/items/summary') && response.request().method() === 'POST'
        );
        await page.getByTestId('apply-filter-button').click();
        await summaryRequest;

        // Wait for rows to update for the new build
        await expect.poll(async () => await rows.count(), { timeout: 2000 }).toBeGreaterThan(0);
        const postSwitchCount = await rows.count();
        console.log('after switch postSwitchCount=', postSwitchCount);
        // Confirm the search input still contains our term after switching builds
        const searchValAfterSwitch = await searchInput.inputValue();
        console.log('search value after switch=', searchValAfterSwitch);
        await expect(searchInput).toHaveValue('immortal');
        // Diagnostic: capture screenshot after switch
        await page.screenshot({ path: 'playwright-debug/step-after-switch.png' });

        // Clear the search via Clear button and wait for server-side summary refresh
        const clearButton = page.getByTestId('item-filter-clear');
        const summaryReload = page.waitForResponse((response) =>
            response.url().includes('/frontend/items/summary') && response.request().method() === 'POST'
        );
        await Promise.all([clearButton.click(), summaryReload]);

        // EXPECTATION (correct behavior): clearing the search should restore more results than the filtered set
        await expect.poll(async () => await rows.count(), { timeout: 3000 }).toBeGreaterThan(postSwitchCount);
        const finalCount = await rows.count();
        console.log('after clear finalCount=', finalCount);
        // Diagnostic: capture screenshot and confirm the search field was cleared
        await page.screenshot({ path: 'playwright-debug/step-after-clear.png' });
        await expect(searchInput).toHaveValue('');

        // --- NEW: emulate a user manually clearing the input (without clicking clear button)
        // This reproduces the manual scenario where the field is edited directly.
        // Restore a known non-empty search, then clear via input and ensure a server reload occurs.
        await searchInput.fill('immortal');
        await expect(searchInput).toHaveValue('immortal');
        // Now clear the field via normal typing (fill empty). Wait for server refresh triggered by input debounce.
        const manualReload = page.waitForResponse((response) =>
            response.url().includes('/frontend/items/summary') && response.request().method() === 'POST'
        );
        await searchInput.fill('');
        await manualReload;
        // After manual clear we expect the rows to increase back to the post-clear count
        await expect.poll(async () => await rows.count(), { timeout: 3000 }).toBeGreaterThan(postSwitchCount);
        const postManualClear = await rows.count();
        console.log('after manual clear finalCount=', postManualClear);
        await expect(searchInput).toHaveValue('');
    });
});
