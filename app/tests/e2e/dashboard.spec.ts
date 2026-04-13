import { expect, test } from "@playwright/test";

test("dashboard renders charts and stat cards", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });

  await page.goto("/");
  await expect(
    page.getByText(
      "Static reproduction of the macroeconomic free-cash-flow yield.",
    ),
  ).toBeVisible();
  await expect(page.getByText("Latest FCF Yield")).toBeVisible();

  for (const id of [
    "chart-fcf-yield",
    "chart-valuation",
    "chart-twin-axis",
    "chart-net-inv-k",
    "chart-k-v",
  ]) {
    const chart = page.getByTestId(id);
    await expect(chart).toBeVisible();
    await expect(chart.locator("path").first()).toBeVisible();
  }

  expect(errors).toEqual([]);
});

test("hovering the primary chart shows a tooltip", async ({ page }) => {
  await page.goto("/");
  const chart = page.getByTestId("chart-fcf-yield-main");
  await chart.hover();
  await expect(chart.getByText("FCF yield")).toBeVisible();
});

test("changing the brush sliders updates the overview selection", async ({
  page,
}) => {
  await page.goto("/");
  const brush = page.getByTestId("chart-fcf-yield");
  const sliders = brush.locator('input[type="range"]');
  await sliders.nth(0).fill("2");
  await sliders.nth(1).fill("5");
  await expect(
    brush.locator('rect[fill="rgba(17, 100, 102, 0.12)"]'),
  ).toBeVisible();
});
