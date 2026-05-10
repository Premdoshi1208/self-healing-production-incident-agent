const { test, expect } = require("@playwright/test");


test("dashboard loads core command-center controls", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: /Self-Healing Incident Agent/i })
  ).toBeVisible();

  await expect(
    page.getByRole("button", { name: /Run Workflow/i })
  ).toBeVisible();

  await expect(
    page.getByRole("heading", { name: /Prometheus Alert Simulator/i })
  ).toBeVisible();

  await expect(
    page.getByRole("heading", { name: /Demo Auth Service Controls/i })
  ).toBeVisible();
});


test("agent trace drawer exposes deploy gate when run data exists", async ({ page }) => {
  await page.goto("/");

  const traceButtons = page.getByText("Open trace");

  try {
    await traceButtons.first().waitFor({ state: "visible", timeout: 5000 });
  } catch (error) {
    test.skip(true, "No saved workflow runs available to open.");
  }

  await traceButtons.first().click();

  const deployGateTab = page.getByRole("button", {
    name: "Deploy Gate",
    exact: true
  });

  await expect(deployGateTab).toBeVisible();

  await deployGateTab.click();

  await expect(page.getByText(/Staging Allowed/i)).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Human Approval Workflow" })
  ).toBeVisible();
});
