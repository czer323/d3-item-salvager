// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

test.describe('Selection UI - collapsed summary and edit affordance', () => {
    test('collapsed summary is shown when build_ids are present', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/?build_ids=1`);

        const summary = page.locator('#selection-summary');
        await expect(summary).toBeVisible();

        const editBtn = page.getByTestId('selection-edit-button');
        await expect(editBtn).toBeVisible();

        // Ensure summary contains the selected build id
        await expect(summary).toContainText('1');
    });

    test('clicking Edit fetches and expands the full controls', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/?build_ids=1`);

        const editBtn = page.getByTestId('selection-edit-button');
        await expect(editBtn).toBeVisible();

        const fetchRequest = page.waitForResponse((resp) =>
            resp.url().includes('/frontend/selection/controls') && resp.request().method() === 'GET'
        );

        await editBtn.click();
        await fetchRequest;

        // The controls partial should be present after replacement
        const controls = page.getByTestId('selection-controls');
        await expect(controls).toBeVisible();
    });

    test('keyboard activation of Edit (Enter) expands the controls', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/?build_ids=1`);

        const editBtn = page.getByTestId('selection-edit-button');
        await expect(editBtn).toBeVisible();

        await editBtn.focus();

        const fetchRequest = page.waitForResponse((resp) =>
            resp.url().includes('/frontend/selection/controls') && resp.request().method() === 'GET'
        );

        await page.keyboard.press('Enter');
        await fetchRequest;

        const controls = page.getByTestId('selection-controls');
        await expect(controls).toBeVisible();
    });

    test('applying selection collapses the UI into the summary', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/`);

        // Ensure controls visible initially
        await expect(page.getByTestId('selection-controls')).toBeVisible();

        // Load builds first
        const loadRequest = page.waitForResponse((resp) =>
            resp.url().includes('/frontend/selection/controls') && resp.request().method() === 'POST'
        );
        await page.getByTestId('load-builds-button').click();
        await loadRequest;

        // Select at least one build option if available
        const buildOptions = page.locator('select[name="build_ids"] option');
        const count = await buildOptions.count();
        test.skip(count === 0, 'No build options available to test apply behavior');

        const firstVal = await buildOptions.first().getAttribute('value');
        if (firstVal) {
            await page.locator('select[name="build_ids"]').selectOption(firstVal);
        }

        // Click Apply and wait for the selection controls POST which triggers collapse
        const applyControlsRequest = page.waitForResponse((resp) =>
            resp.url().includes('/frontend/selection/controls') && resp.request().method() === 'POST'
        );
        // Wait for the items summary POST which should update the item table
        const itemsSummaryRequest = page.waitForResponse((resp) =>
            resp.url().includes('/frontend/items/summary') && resp.request().method() === 'POST'
        );

        await page.getByTestId('apply-filter-button').click();
        await applyControlsRequest;
        await itemsSummaryRequest;

        // Summary should be visible and controls hidden
        await expect(page.locator('#selection-summary')).toBeVisible();
        await expect(page.getByTestId('selection-controls')).toBeHidden();

        // Items summary should be visible and contain rows
        const itemSummary = page.getByTestId('item-summary');
        await expect(itemSummary).toBeVisible();
        const rows = itemSummary.locator('table tbody tr');
        const rowsCount = await rows.count();
        expect(rowsCount).toBeGreaterThan(0);

    });
});
