// @ts-nocheck
import { test, expect } from '@playwright/test';

const TEST_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const TEST_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${TEST_PORT}`;

async function resolveTargetSection(page) {
    const usedSection = page.getByTestId('variant-summary-used');
    const usedVisibleCount = await usedSection.locator('[data-testid="variant-summary-used-item"]:visible').count();
    if (usedVisibleCount > 0) {
        return {
            section: usedSection,
            sectionId: 'variant-summary-used',
            visibleCount: usedVisibleCount,
        };
    }
    const salvageSection = page.getByTestId('variant-summary-salvage');
    const salvageVisibleCount = await salvageSection
        .locator('[data-testid="variant-summary-salvage-item"]:visible')
        .count();
    return {
        section: salvageSection,
        sectionId: 'variant-summary-salvage',
        visibleCount: salvageVisibleCount,
    };
}

function firstFragment(text) {
    const trimmed = (text ?? '').trim();
    if (!trimmed) {
        return '';
    }
    const parts = trimmed.split(/\s+/);
    if (!parts.length) {
        return trimmed.slice(0, 4);
    }
    if (parts[0].length >= 4) {
        return parts[0].slice(0, 4);
    }
    return trimmed.slice(0, Math.min(6, trimmed.length));
}

test.describe('Realtime item filtering', () => {
    test('filters by search term and slot, showing empty state when nothing matches', async ({ page }) => {
        await page.goto(`${TEST_BASE_URL}/`);

        const summaryRoot = page.getByTestId('variant-summary');
        await expect(summaryRoot).toBeVisible();

        const { section, sectionId, visibleCount } = await resolveTargetSection(page);
        test.skip(visibleCount === 0, 'No items available in summary to validate filtering.');

        const itemCard = section.locator(`[data-testid="${sectionId}-item"]:visible`).first();
        await expect(itemCard).toBeVisible();

        const itemName = (await itemCard.locator(`[data-testid="${sectionId}-item-name"]`).textContent())?.trim() ?? '';
        const itemSlot = (await itemCard.locator(`[data-testid="${sectionId}-item-slot"]`).textContent())?.trim() ?? '';

        expect(itemName.length).toBeGreaterThan(0);
        const searchTerm = firstFragment(itemName) || itemName.slice(0, Math.min(6, itemName.length));

        const searchInput = page.getByTestId('item-filter-search');
        await searchInput.fill(searchTerm);
        await page.waitForTimeout(200);

        const filteredCount = await section.locator(`[data-testid="${sectionId}-item"]:visible`).count();
        expect(filteredCount).toBeGreaterThan(0);
        expect(filteredCount).toBeLessThanOrEqual(visibleCount);
        await expect(section.getByTestId(`${sectionId}-count`)).toHaveText(String(filteredCount));

        const slotSelect = page.getByTestId('item-slot-filter');
        if (itemSlot) {
            const hasOption = await slotSelect.locator(`option[value="${itemSlot}"]`).count();
            if (hasOption > 0) {
                await slotSelect.selectOption(itemSlot);
                await page.waitForTimeout(150);
                const slotFilteredCount = await section.locator(`[data-testid="${sectionId}-item"]:visible`).count();
                expect(slotFilteredCount).toBeGreaterThan(0);
                await expect(itemCard).toBeVisible();
            }
        }

        await searchInput.fill('zzzxxyy');
        await page.waitForTimeout(250);
        const emptyState = section.getByTestId(`${sectionId}-empty`);
        await expect(emptyState).toBeVisible();
        await expect(section.locator(`[data-testid="${sectionId}-item"]:visible`)).toHaveCount(0);

        const clearButton = page.getByTestId('item-filter-clear');
        await clearButton.click();
        await page.waitForTimeout(200);
        const restoredCount = await section.locator(`[data-testid="${sectionId}-item"]:visible`).count();
        expect(restoredCount).toBeGreaterThan(0);
    });
});
