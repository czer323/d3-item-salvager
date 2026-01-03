/// <reference types="node" />
// Note: to enable TypeScript Node types for this config, install dev dependency
// `@types/node` in the `frontend` package (e.g. `cd frontend && npm i -D @types/node`).
import fs from 'fs';
import path from 'path';
import { defineConfig, devices } from '@playwright/test';
import type { PlaywrightTestConfig } from '@playwright/test';

// If `@types/node` is not installed in the frontend package, declare Node globals
// used by this config so TypeScript doesn't complain in the editor/CI.
declare const __dirname: string;
declare const process: { env: Record<string, string | undefined>; platform?: string | undefined };

const DEFAULT_PORT = process.env.FRONTEND_PLAYWRIGHT_PORT ?? '8001';
const DEFAULT_BASE_URL = process.env.FRONTEND_BASE_URL ?? `http://127.0.0.1:${DEFAULT_PORT}`;

// Resolve artifact directories relative to the frontend root (this file is in frontend/tests/playwright)
const FRONTEND_ROOT = path.resolve(__dirname, '../../');
const outputDir = process.env.PLAYWRIGHT_OUTPUT_DIR ?? path.join(FRONTEND_ROOT, 'test-results');
const htmlReportDir = process.env.PLAYWRIGHT_HTML_REPORT_DIR ?? path.join(FRONTEND_ROOT, 'playwright-report');

// Prefer virtualenv Python in repo (cross-platform path), but allow override from env
const VENV_PY = process.platform === 'win32'
  ? path.join(FRONTEND_ROOT, '..', '.venv', 'Scripts', 'python.exe')
  : path.join(FRONTEND_ROOT, '..', '.venv', 'bin', 'python');

const quoteForShell = (p: string): string => {
  if (!p) return '';
  if (process.platform === 'win32') {
    // Wrap in double quotes and escape internal double quotes for cmd.exe / PowerShell.
    return `"${p.replace(/"/g, '\\"')}"`;
  }
  // POSIX-style: wrap in single quotes and escape existing single quotes.
  return "'" + p.replace(/'/g, "'\\''") + "'";
};

const projectRoot = path.resolve(FRONTEND_ROOT, '..');
const startServersScript = path.join(FRONTEND_ROOT, 'scripts', 'start_servers.py');
const preferredPython = process.env.PYTHON ?? VENV_PY;
const pythonPath = preferredPython && fs.existsSync(preferredPython) ? preferredPython : undefined;
const startServersCommand = process.env.PLAYWRIGHT_USE_UV === '0'
  ? `${pythonPath ?? 'python'} ${quoteForShell(startServersScript)}`
  : `uv run --project ${quoteForShell(projectRoot)} python ${quoteForShell(startServersScript)}`;

const webServerEnv: Record<string, string> = {
  FRONTEND_PLAYWRIGHT_PORT: DEFAULT_PORT,
  BACKEND_PORT: process.env.BACKEND_PORT ?? '8000',
  ...(pythonPath ? { PYTHON: pythonPath } : {}),
};


const config: PlaywrightTestConfig = {
  // Tests live in this directory (TypeScript tests); keep explicit testMatch to TypeScript files
  testDir: './',

  // NOTE: setting `testMatch` replaces Playwright's defaults. This config intentionally
  // restricts test discovery to TypeScript files only: '*.ts', '*.spec.ts', and '*.test.ts'.
  // (No .js/.jsx/.tsx/.mjs/.cjs test files were found in the repo.)
  testMatch: ['**/test_*.ts', '**/*.spec.ts', '**/*.test.ts'],

  // Playwright output directory for artifacts (traces, attachments)
  outputDir,

  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  retries: process.env.CI ? 2 : 0,
  fullyParallel: true, // enables full-file parallelism for faster runs; set to false if tests require ordering

  forbidOnly: !!process.env.CI,
  workers: process.env.CI ? 1 : undefined,

  use: {
    baseURL: DEFAULT_BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
    locale: 'en-US',
    timezoneId: 'UTC',
  },

  // Start backend/frontend automatically for local runs using the helper script.
  webServer: {
    // Runs the Python helper that starts both backend and frontend and waits for readiness.
    command: startServersCommand,
    url: DEFAULT_BASE_URL,
    timeout: 120_000,
    // Force Playwright to run the helper script every time so DB init and
    // reference data load occur before tests (prevents "no such table" errors).
    reuseExistingServer: false,
    env: webServerEnv,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to enable cross-browser tests:
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  reporter: [
    ['list'],
    ['html', { outputFolder: htmlReportDir, open: 'never' }]
  ],

  grepInvert: process.env.CI ? [/@local-only/] : undefined,
};

export default defineConfig(config);
