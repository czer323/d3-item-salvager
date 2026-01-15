// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

test.describe('Union items population when selection changes', () => {
    test('applying selection triggers /builds/items fetch and populates the item list', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/`);

        // Load builds first
        const loadRequest = page.waitForResponse((resp) =>
            resp.url().includes('/frontend/selection/controls') && resp.request().method() === 'POST'
        );
        await page.getByTestId('load-builds-button').click();
        await loadRequest;

        // Choose a build if available
        const buildOptions = page.locator('select[name="build_ids"] option');
        const count = await buildOptions.count();
        test.skip(count === 0, 'No build options available to test apply behavior');

        const firstVal = await buildOptions.first().getAttribute('value');
        if (firstVal) {
            await page.locator('select[name="build_ids"]').selectOption(firstVal);
        }

        // Wait for the /builds/items GET request which should happen due to client-side fetch
        const buildsItemsRequest = page.waitForResponse((resp) =>
            resp.url().includes('/builds/items') && resp.request().method() === 'GET'
        );

        await page.getByTestId('apply-filter-button').click();
        await buildsItemsRequest;

        // The client should render the items into #item-list
        const itemList = page.locator('#item-list');
        await expect(itemList).toBeVisible();
        const items = itemList.locator('.virtual-item, .p-2');
        const itemsCount = await items.count();
        expect(itemsCount).toBeGreaterThan(0);
    });
});
