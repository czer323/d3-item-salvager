// @ts-nocheck
import { defineConfig, devices } from '@playwright/test';

const DEFAULT_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const DEFAULT_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${DEFAULT_PORT}`;

export default defineConfig({
  testDir: './',
  // NOTE: setting `testMatch` replaces Playwright's defaults. This config intentionally
  // restricts test discovery to TypeScript files only: '*.ts', '*.spec.ts', and '*.test.ts'.
  // (No .js/.jsx/.tsx/.mjs/.cjs test files were found in the repo.)
  testMatch: ['**/test_*.ts', '**/*.spec.ts', '**/*.test.ts'],
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  retries: process.env.CI ? 2 : 0,
  fullyParallel: false,
  use: {
    baseURL: DEFAULT_BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    locale: 'en-US',
    timezoneId: 'UTC',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  reporter: [
    ['list'],
    [
      'html',
      {
        outputFolder: '../../playwright-report',
        open: 'never',
      },
    ],
  ],
  grepInvert: process.env.CI ? [/@local-only/] : undefined,
});
