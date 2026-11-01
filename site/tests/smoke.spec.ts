import { test, expect } from "@playwright/test";

const routes = ["/", "/work", "/about", "/work/skywalker", "/work/vyra", "/work/monarch"];
const revealed = "[data-reveal], [data-split], [data-wipe]";

for (const path of routes) {
  test(`${path} loads cleanly`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    // Playwright's WebKit can't load its own native video-control icons; that's the test browser, not the site
    page.on("console", (m) => m.type() === "error" && !m.text().startsWith("Button failed to load") && errors.push(m.text()));
    await page.goto(path);
    await expect(page.locator("h1").first()).toBeAttached();
    // No sideways scrolling on any viewport
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);
    expect(errors).toEqual([]);
  });

  test(`${path} shows everything with reduced motion`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto(path);
    const hidden = await page.$$eval(revealed, (els) => els.filter((e) => getComputedStyle(e).opacity === "0" || getComputedStyle(e).visibility === "hidden").length);
    expect(hidden).toBe(0);
  });
}

test("work → project navigation", async ({ page }) => {
  await page.goto("/work");
  await page.getByRole("link", { name: "Geely Skywalker", exact: true }).click();
  await expect(page).toHaveURL(/\/work\/skywalker$/);
  await expect(page.locator("h1")).toContainText("Skywalker");
});

test("home hero video loops muted inline", async ({ page }) => {
  await page.goto("/");
  const v = page.locator("video");
  await expect(v).toHaveJSProperty("muted", true);
  await expect(v).toHaveJSProperty("loop", true);
  await expect(v).toHaveAttribute("playsinline", "");
  await expect(page.getByRole("link", { name: "Work" })).toBeVisible();
});

test("monarch weather toggle switches mode", async ({ page }) => {
  await page.goto("/work/monarch");
  const hot = page.getByRole("button", { name: "Hot" });
  await hot.scrollIntoViewIfNeeded();
  await hot.click();
  await expect(hot).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("img", { name: /hot weather/i })).toBeVisible();
});

test("cockpit evolution carousel steps and loops", async ({ page, isMobile }) => {
  await page.goto("/work/skywalker");
  const carousel = page.locator("[data-carousel]").first();
  const index = carousel.locator("[data-index]");
  await carousel.scrollIntoViewIfNeeded();
  if (isMobile) {
    // touch: the scroller itself swipes; arrow-key equivalent via scrollBy
    await carousel.locator("[data-slides]").evaluate((el) => el.scrollBy({ left: el.clientWidth }));
    await expect(index).toHaveText("2");
    return;
  }
  await carousel.getByRole("button", { name: "Next image" }).click();
  await expect(index).toHaveText("2");
  await carousel.getByRole("button", { name: "Previous image" }).click();
  await carousel.getByRole("button", { name: "Previous image" }).click();
  await expect(index).toHaveText("9"); // wraps from the first to the last image
});

test("project hero text never overlaps the image", async ({ page, isMobile }) => {
  test.skip(isMobile, "phones stack the text under the image");
  for (const slug of ["skywalker", "vyra", "monarch"]) {
    for (const width of [768, 1024, 1440, 1920]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`/work/${slug}`);
      const gap = await page.evaluate(() => {
        const img = document.querySelector("main section .slice")!.getBoundingClientRect();
        const text = [...document.querySelectorAll("main section:first-child h1, main section:first-child p")];
        return img.left - Math.max(...text.map((t) => t.getBoundingClientRect().right));
      });
      expect(gap, `${slug} @ ${width}px`).toBeGreaterThan(0);
    }
  }
});
