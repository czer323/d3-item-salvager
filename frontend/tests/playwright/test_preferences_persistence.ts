// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

function waitForSelectionRefresh(page) {
    return page.waitForResponse(
        (response) =>
            response.url().includes('/frontend/selection/controls') &&
            response.request().method() === 'POST'
    );
}

test.describe('Preferences persistence', () => {
    test('saves selections, restores on reload, and supports import/export', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/`);
        await expect(page.getByTestId('selection-controls')).toBeVisible();

        const loadRequest = waitForSelectionRefresh(page);
        await page.getByTestId('load-builds-button').click();
        await loadRequest;

        const classSelect = page.getByTestId('class-multiselect');
        const buildSelect = page.getByTestId('build-multiselect');
        const buildOptions = buildSelect.locator('option');
        const buildCount = await buildOptions.count();
        test.skip(buildCount === 0, 'Build options are required to verify preferences.');

        const classOption = classSelect.locator('option').first();
        const selectedClassValue = await classOption.getAttribute('value');
        if (selectedClassValue) {
            await classSelect.selectOption(selectedClassValue);
        }

        const selectedBuildValues = await buildOptions.evaluateAll((options) =>
            options.slice(0, Math.min(2, options.length)).map((option) => option.value)
        );
        await buildSelect.selectOption(selectedBuildValues);

        await page.getByTestId('preferences-open-button').click();
        const modal = page.getByTestId('preferences-modal');
        await expect(modal).toBeVisible();

        await page.getByTestId('preferences-save-button').click();
        await expect(page.getByTestId('preferences-toast')).toContainText('Preferences saved');

        await page.getByTestId('preferences-export-button').click();
        const editor = page.getByTestId('preferences-json-editor');
        const exportedJson = await editor.inputValue();
        expect(exportedJson.length).toBeGreaterThan(0);

        await page.getByTestId('preferences-close-button').click();

        await page.reload();
        await expect(page.getByTestId('selection-controls')).toBeVisible();
        const reloadRequest = waitForSelectionRefresh(page);
        await page.getByTestId('load-builds-button').click();
        await reloadRequest;

        const restoredClasses = await page
            .locator('select[name="class_ids"] option:checked')
            .evaluateAll((options) => options.map((option) => option.value));
        if (selectedClassValue) {
            expect(restoredClasses).toContain(selectedClassValue);
        }

        const restoredBuilds = await page
            .locator('select[name="build_ids"] option:checked')
            .evaluateAll((options) => options.map((option) => option.value));
        expect(restoredBuilds).toEqual(selectedBuildValues);

        const storageKey = await page.evaluate(() => window.d3Preferences?.storageKey ?? '');
        if (storageKey) {
            await page.evaluate((key) => window.localStorage.removeItem(key), storageKey);
        }

        await page.reload();
        await expect(page.getByTestId('selection-controls')).toBeVisible();
        const secondLoad = waitForSelectionRefresh(page);
        await page.getByTestId('load-builds-button').click();
        await secondLoad;

        await page.getByTestId('preferences-open-button').click();
        await expect(page.getByTestId('preferences-modal')).toBeVisible();
        const importEditor = page.getByTestId('preferences-json-editor');
        await importEditor.fill(exportedJson);

        await page.getByTestId('preferences-import-button').click();
        await expect(page.getByTestId('preferences-toast')).toContainText('Preferences imported');

        const importedBuilds = await page
            .locator('select[name="build_ids"] option:checked')
            .evaluateAll((options) => options.map((option) => option.value));
        expect(importedBuilds).toEqual(selectedBuildValues);

        await page.getByTestId('preferences-close-button').click();
    });
});
