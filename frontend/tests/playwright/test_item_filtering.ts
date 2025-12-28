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
});
