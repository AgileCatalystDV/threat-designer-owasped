import { test, expect } from "@playwright/test";

/**
 * Sprint 8 — minimal UI smoke: no full stack / LLM required.
 * Playwright may start Vite via playwright.config.js webServer, or reuse an existing dev server.
 */
test.describe("UI smoke", () => {
  test("home loads (no-auth landing)", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Threat Designer/i);
    await expect(page.getByRole("button", { name: /submit threat model/i })).toBeVisible();
  });
});
