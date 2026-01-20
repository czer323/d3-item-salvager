import { defineConfig, devices } from '@playwright/test';
import path from 'path';

// Resolve repo root and the virtualenv 'Scripts' (Windows) / 'bin' (POSIX)
const repoRoot = path.resolve(__dirname, '../../');
const venvScripts = process.platform === 'win32' ? path.join(repoRoot, '.venv', 'Scripts') : path.join(repoRoot, '.venv', 'bin');

export default defineConfig({
    testDir: './',
    timeout: 30_000,
    expect: { timeout: 5_000 },
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 2 : undefined,
    reporter: [['list'], ['html', { outputFolder: 'playwright-report' }]],
    use: {
        baseURL: process.env.FRONTEND_BASE_URL || 'http://127.0.0.1:8000',
        headless: true,
        trace: 'on-first-retry'
    },

    webServer: {
        command: process.env.PW_WEBSERVER_CMD || 'uv run python -m d3_item_salvager api',
        url: process.env.FRONTEND_BASE_URL || 'http://127.0.0.1:8000',
        reuseExistingServer: true, // if the server is already running, Playwright will reuse it
        timeout: 180_000,
        // Prepend the project's venv Scripts/bin to PATH so `python` resolves to our venv interpreter
        env: { PATH: `${venvScripts}${path.delimiter}${process.env.PATH || ''}` },
        // The cwd should point to the repository root so the server command runs from the project
        cwd: process.env.PW_WEBSERVER_CWD || '../../'
    },
    projects: [
        {
            name: 'chromium',
            use: { ...devices['Desktop Chrome'] }
        }
    ]
});
