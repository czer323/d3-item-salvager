import { expect, test } from '@playwright/test';

test.describe('Item filtering and salvage badge', () => {
    test('shows DB-only item with Salvage badge and spelling message when no match', async ({ page }) => {
        await page.goto('/');

        // Load the items table (submit the form even with no builds selected)
        await page.click('form button[type="submit"]');

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

    test('exact match from selected build appears at top', async ({ page }) => {
        await page.goto('/');

        // Choose the first available non-empty build option
        const optionValue = await page.evaluate(() => {
            const select = document.querySelector('#build-select') as HTMLSelectElement | null;
            if (!select) return '';
            const options = Array.from(select.options).filter(o => o.value && o.value.trim() !== '');
            return options.length ? options[0].value : '';
        });
        if (!optionValue) {
            test.skip();
            return;
        }

        await page.selectOption('#build-select', optionValue);
        await page.click('form button[type="submit"]');
        // Wait for results to load
        await page.locator('#results-area table').waitFor({ timeout: 5000 });

        // Grab first item name from table
        const firstName = await page.locator('table tbody tr').first().locator('td .d3planner-name').innerText();
        expect(firstName.length).toBeGreaterThan(0);

        // Search for exact name
        const search = page.locator('input[placeholder="Search items..."]');
        await search.fill(firstName);
        await page.waitForTimeout(200);

        // Assert top row contains the exact name
        const topRowName = await page.locator('table tbody tr').first().locator('td .d3planner-name').innerText();
        expect(topRowName).toBe(firstName);
    });

    test('fuzzy misspelling still finds build item (not Salvage)', async ({ page }) => {
        await page.goto('/');

        // Select a build to ensure in-build items are present
        const optionValue = await page.evaluate(() => {
            const select = document.querySelector('#build-select') as HTMLSelectElement | null;
            if (!select) return '';
            const options = Array.from(select.options).filter(o => o.value && o.value.trim() !== '');
            return options.length ? options[0].value : '';
        });
        if (!optionValue) {
            test.skip();
            return;
        }

        await page.selectOption('#build-select', optionValue);
        await page.click('form button[type="submit"]');
        await page.locator('#results-area table').waitFor({ timeout: 5000 });

        const firstRow = page.locator('table tbody tr').first();
        const name = await firstRow.locator('td .d3planner-name').innerText();

        // Create a simple misspelling by removing one character from the name
        const misspelled = name.length > 2 ? name.slice(0, Math.floor(name.length / 2)) + name.slice(Math.floor(name.length / 2) + 1) : name;

        const search = page.locator('input[placeholder="Search items..."]');
        await search.fill(misspelled);
        await page.waitForTimeout(200);

        // Expect the original name to appear in results
        const table = page.locator('table');
        await expect(table).toContainText(name);

        // Ensure the found row does not include 'Salvage' badge (it's an in-build match)
        const foundRow = page.locator(`table tbody tr:has(td .d3planner-name:text("${name}"))`);
        await expect(foundRow).not.toContainText('Salvage');
    });
});
