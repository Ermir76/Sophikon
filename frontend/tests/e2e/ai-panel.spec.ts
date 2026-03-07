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

async function createProject(page: Page, name: string, description: string) {
  await page.goto("/projects");
  await page.getByRole("button", { name: "New Project" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();

  await page.getByRole("dialog").locator('input[name="name"]').fill(name);
  await page
    .getByRole("dialog")
    .locator('textarea[name="description"]')
    .fill(description);

  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Start Date" })
    .click();
  await page
    .getByRole("gridcell", { name: /^Today/ })
    .getByRole("button")
    .click();

  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Create Project" })
    .click();
  await expect(page.getByText("Project created")).toBeVisible();
}

async function addTask(page: Page, name: string) {
  const addInput = page.locator('input[name="taskName"]');

  if (!(await addInput.isVisible())) {
    await page.getByRole("button", { name: /Add Task/i }).click();
  }

  await addInput.fill(name);
  await addInput.press("Enter");
  await expect(page.getByRole("cell", { name })).toBeVisible();
}

test.describe("AI Panel Smoke", () => {
  test("works across project subpages with chat, estimate, and suggestions", async ({
    page,
  }) => {
    const user = generateUser();
    await registerUser(page, user);

    const projectName = "AI Smoke Project";
    await createProject(page, projectName, "Smoke check for the AI panel");

    await page.goto("/projects");
    await page.getByRole("link", { name: projectName }).click();
    await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);
    await expect(
      page.getByRole("heading", { name: "Tasks", exact: true }),
    ).toBeVisible();

    await addTask(page, "QA regression pass");
    await addTask(page, "Production release");

    await page.getByRole("button", { name: "AI Assistant" }).click();
    await expect(page.getByText("Project-aware guidance")).toBeVisible();

    await page
      .getByPlaceholder("Ask the assistant about this project...")
      .fill("What is the project status?");
    await page.getByRole("button", { name: "Send", exact: true }).click();
    await expect(page.getByText(/currently has|I reviewed/)).toBeVisible();

    await page.getByRole("tab", { name: "Estimate" }).click();
    await page.getByLabel("QA regression pass").check();
    await page.getByRole("button", { name: "Run Estimate" }).click();
    await expect(page.getByText(/Estimated from task context/)).toBeVisible();
    await page.getByRole("button", { name: /Apply/ }).click();
    await expect(
      page.getByText("Task duration updated from AI estimate"),
    ).toBeVisible();

    await page.getByRole("tab", { name: "Suggestions" }).click();
    await expect(
      page.getByText(
        /Possible missing dependency|Task is overdue|No high-risk issues detected/,
      ),
    ).toBeVisible();

    const suggestionApplyButton = page
      .locator('button:has-text("Apply")')
      .last();
    await suggestionApplyButton.click();
    await expect(page.getByText("Suggestion applied")).toBeVisible();

    await page.getByRole("link", { name: "Overview" }).click();
    await expect(page).toHaveURL(/\/projects\/[^/]+$/);
    await expect(page.getByText("Project-aware guidance")).toBeVisible();

    await page.getByRole("link", { name: "Gantt" }).click();
    await expect(page).toHaveURL(/\/projects\/[^/]+\/gantt/);
    await expect(page.getByText("Project-aware guidance")).toBeVisible();

    await page.getByRole("link", { name: "Resources" }).click();
    await expect(page).toHaveURL(/\/projects\/[^/]+\/resources/);
    await expect(page.getByText("Project-aware guidance")).toBeVisible();
  });
});
