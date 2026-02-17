import { test, expect, type Page } from "@playwright/test";
import { generateUser } from "./utils";

/** Register a new user and land on the dashboard. */
async function registerUser(page: Page, user: ReturnType<typeof generateUser>) {
    await page.goto("/register");
    await page.fill('input[name="full_name"]', user.fullName);
    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.fill('input[name="confirmPassword"]', user.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/");
}

/** Create a project from the /projects page via the dialog. */
async function createProject(page: Page, name: string, description: string) {
    await page.goto("/projects");
    await page.getByRole("button", { name: "New Project" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();

    await page.getByRole("dialog").locator('input[name="name"]').fill(name);
    await page.getByRole("dialog").locator('textarea[name="description"]').fill(description);

    // Pick today's date — button is labelled by FormLabel "Start Date"
    await page.getByRole("dialog").getByRole("button", { name: "Start Date" }).click();
    // react-day-picker labels today's cell as "Today, {weekday}, {full date}"
    await page.getByRole("gridcell", { name: /^Today/ }).getByRole("button").click();

    await page.getByRole("dialog").getByRole("button", { name: "Create Project" }).click();
    await expect(page.getByText("Project created")).toBeVisible();
}

test.describe("Project Flow", () => {
    test("Create project -> appears in projects list", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Alpha Project";
        await createProject(page, projectName, "Test description");

        // Verify the project card link (not the toast which also contains the name)
        await expect(page.getByRole("link", { name: projectName })).toBeVisible();
    });

    test("Open project -> navigates to project layout", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Beta Project";
        await createProject(page, projectName, "Beta description");

        // Click project name link in the card
        await page.getByRole("link", { name: projectName }).click();

        // Expect URL to match /projects/{id}/tasks
        await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);

        // Sidebar should show project nav
        await expect(page.getByText("Back to Projects")).toBeVisible();
    });

    test("Update project details -> changes reflected", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const originalName = "Original Name";
        await createProject(page, originalName, "Original description");

        // Open card menu and go to settings
        await page.getByRole("button", { name: "Open menu" }).click();
        await page.getByRole("menuitem", { name: "Settings" }).click();
        await expect(page).toHaveURL(/\/projects\/[^/]+\/settings/);

        // Wait for form to load
        const nameInput = page.locator('input[name="name"]');
        await expect(nameInput).toHaveValue(originalName);

        // Update name
        const updatedName = "Updated Name";
        await nameInput.fill(updatedName);
        await page.getByRole("button", { name: "Save Changes" }).click();

        await expect(page.getByText("Project updated")).toBeVisible();

        // Verify in list
        await page.goto("/projects");
        await expect(page.getByText(updatedName)).toBeVisible();
    });

    test("Delete project -> removed from list", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Delete Me";
        await createProject(page, projectName, "To be deleted");

        // Go to settings via card menu
        await page.getByRole("button", { name: "Open menu" }).click();
        await page.getByRole("menuitem", { name: "Settings" }).click();
        await expect(page).toHaveURL(/\/projects\/[^/]+\/settings/);

        // Delete
        await page.getByRole("button", { name: "Delete Project" }).click();

        // Confirm in alert dialog
        await expect(page.getByRole("alertdialog")).toBeVisible();
        await page.getByRole("alertdialog").getByRole("button", { name: "Delete Project" }).click();

        await expect(page.getByText("Project deleted")).toBeVisible();
        await expect(page).toHaveURL("/projects");

        await expect(page.getByRole("link", { name: projectName })).not.toBeVisible();
    });

    test("Back to Projects link works from project context", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        await createProject(page, "Nav Test", "Desc");

        // Enter project
        await page.getByRole("link", { name: "Nav Test" }).click();
        await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);

        // Click Back to Projects in sidebar
        await page.getByText("Back to Projects").click();

        await expect(page).toHaveURL("/projects");

        // Sidebar should show global nav again
        await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
        await expect(page.getByText("Back to Projects")).not.toBeVisible();
    });
});
