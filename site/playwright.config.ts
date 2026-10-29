import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests",
  fullyParallel: true,
  use: { baseURL: "http://localhost:4322" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
    { name: "mobile-safari", use: { ...devices["iPhone 15"] } },
    { name: "mobile-chrome", use: { ...devices["Pixel 7"] } },
  ],
  // Tests the production build, on its own port so it never collides with `npm run dev`
  webServer: { command: "npm run build && npm run preview -- --port 4322 --ignore-lock", port: 4322, reuseExistingServer: false, timeout: 180_000 },
});
