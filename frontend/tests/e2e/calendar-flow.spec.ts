import { expect, test, type Page } from "@playwright/test";

import { generateUser } from "./utils";

async function registerUser(page: Page, user: ReturnType<typeof generateUser>) {
  await page.goto("/register");
  await page.fill('input[name="full_name"]', user.fullName);
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.fill('input[name="confirmPassword"]', user.password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL("/");
}

async function createProject(page: Page, name: string) {
  await page.goto("/projects");
  await page.getByRole("button", { name: "New Project" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();

  await dialog.locator('input[name="name"]').fill(name);
  await dialog.locator('textarea[name="description"]').fill("Calendar E2E project");
  await dialog.getByRole("button", { name: "Start Date" }).click();
  await page.getByRole("gridcell", { name: /^Today/ }).getByRole("button").click();
  await dialog.getByRole("button", { name: "Create Project" }).click();
  await expect(page.getByText("Project created")).toBeVisible();
}

async function getProjectId(page: Page, projectName: string): Promise<string> {
  const link = page.getByRole("link", { name: projectName }).first();
  await expect(link).toBeVisible();
  const href = await link.getAttribute("href");
  if (!href) {
    throw new Error("Project link href missing");
  }
  const match = href.match(/\/projects\/([^/]+)\//);
  if (!match) {
    throw new Error(`Could not parse project ID from href: ${href}`);
  }
  return match[1];
}

test.describe("Calendar Flow", () => {
  test("create calendar, set default calendar, and add exception", async ({ page }) => {
    const user = generateUser();
    const projectName = `Calendar Project ${Date.now()}`;
    const calendarName = "Operations Calendar";

    await registerUser(page, user);
    await createProject(page, projectName);
    const projectId = await getProjectId(page, projectName);

    await page.goto(`/projects/${projectId}/calendar`);
    await expect(page.getByRole("heading", { name: "Calendar" })).toBeVisible();

    await page.getByRole("button", { name: "New Calendar" }).click();
    const createDialog = page.getByRole("dialog");
    await createDialog.locator("#calendar-name").fill(calendarName);
    await createDialog.getByRole("button", { name: "Save" }).click();

    await expect(page.getByText("Calendar created")).toBeVisible();
    await expect(page.getAllByText(calendarName).first()).toBeVisible();

    await page.locator("#default-calendar").click();
    await page.getByRole("option", { name: calendarName }).click();
    await expect(page.getByText("Default calendar updated")).toBeVisible();

    await page.getByRole("button", { name: /Add exception/i }).click();
    const exceptionDialog = page.getByRole("dialog");
    await exceptionDialog.locator("#exception-name").fill("Founders Day");
    await exceptionDialog.locator("#exception-start-date").fill("2026-04-01");
    await exceptionDialog.locator("#exception-end-date").fill("2026-04-01");
    await exceptionDialog.getByRole("button", { name: "Save" }).click();

    await expect(page.getByText("Exception created")).toBeVisible();
    await expect(page.getByText("Founders Day")).toBeVisible();
  });
});
