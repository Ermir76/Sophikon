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
  await dialog.locator('textarea[name="description"]').fill("Attachment E2E project");
  await dialog.getByRole("button", { name: "Start Date" }).click();
  await page.getByRole("gridcell", { name: /^Today/ }).getByRole("button").click();
  await dialog.getByRole("button", { name: "Create Project" }).click();
  await expect(page.getByText("Project created")).toBeVisible();
}

async function navigateToTasks(page: Page, projectName: string) {
  await page.goto("/projects");
  await page.getByRole("link", { name: projectName }).click();
  await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);
  await expect(page.getByRole("heading", { name: "Tasks", exact: true })).toBeVisible();
}

async function addTask(page: Page, taskName: string) {
  const addInput = page.locator('input[name="taskName"]');
  if (!(await addInput.isVisible())) {
    await page.getByRole("button", { name: /Add Task/i }).click();
  }
  await addInput.fill(taskName);
  await addInput.press("Enter");
  await expect(page.getByRole("cell", { name: taskName })).toBeVisible();
}

async function openTaskDetailPanel(page: Page, taskName: string) {
  const row = page.getByRole("row").filter({ hasText: taskName });
  await row.getByText("%").click();
  await expect(page.getByRole("dialog")).toBeVisible();
}

test.describe("Attachment Flow", () => {
  test("upload, list, download-link, and delete task attachment", async ({ page }) => {
    const user = generateUser();
    const projectName = `Attachment Project ${Date.now()}`;
    const taskName = "Attachment Task";
    const fileName = "scope.txt";

    await registerUser(page, user);
    await createProject(page, projectName);
    await navigateToTasks(page, projectName);
    await addTask(page, taskName);
    await openTaskDetailPanel(page, taskName);

    const panel = page.getByRole("dialog");
    const fileInput = panel.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: fileName,
      mimeType: "text/plain",
      buffer: Buffer.from("attachment coverage"),
    });

    await expect(page.getByText("Attachment uploaded")).toBeVisible();
    await expect(panel.getByText(fileName)).toBeVisible();

    const downloadLink = panel.getByRole("link", { name: `Download ${fileName}` });
    await expect(downloadLink).toHaveAttribute("href", /\/attachments\/.+\/download$/);

    await panel.getByRole("button", { name: `Delete ${fileName}` }).click();
    await expect(page.getByText("Attachment deleted")).toBeVisible();
    await expect(panel.getByText(fileName)).not.toBeVisible();
  });
});
