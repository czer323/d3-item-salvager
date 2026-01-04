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
});
