import { expect, test } from '@playwright/test';

test.describe('Item filtering and salvage badge', () => {
    test('shows DB-only item with Salvage badge and spelling message when no match', async ({ page }) => {
        await page.goto('/');

        const search = page.locator('input[placeholder="Search items..."]');
        await expect(search).toBeVisible();

        // Typo that should match a DB item (Golden Gorget of Leoric -> Gorget of Leorik)
        await search.fill('Gorget of Leorik');
        // Allow debounce + client-side processing
        await page.waitForTimeout(200);

        // The canonical name should appear in the results and the 'Salvage' badge should be present
        const table = page.locator('table');
        await expect(table).toContainText('Golden Gorget of Leoric');
        await expect(table).toContainText('Salvage');

        // Now use a query with zero matches
        await search.fill('this-is-not-an-item-xyz');
        await page.waitForTimeout(200);

        await expect(page.locator('td:text("No items found — check spelling.")')).toBeVisible();
    });
});
