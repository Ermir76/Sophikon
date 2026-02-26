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

    await page.getByRole("dialog").getByRole("button", { name: "Start Date" }).click();
    await page.getByRole("gridcell", { name: /^Today/ }).getByRole("button").click();

    await page.getByRole("dialog").getByRole("button", { name: "Create Project" }).click();
    await expect(page.getByText("Project created")).toBeVisible();
}

/** Navigate to a project's tasks page. */
async function navigateToTasks(page: Page, projectName: string) {
    // Make sure we're on projects page
    await page.goto("/projects");
    await page.getByRole("link", { name: projectName }).click();

    // Project link goes directly to /projects/:id/tasks
    await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);
    // Wait for tasks page content to be ready
    await expect(page.getByRole("heading", { name: "Tasks", exact: true })).toBeVisible();
}

/** Add a task via the AddTaskRow inline input. */
async function addTask(page: Page, name: string) {
    const addInput = page.locator('input[name="taskName"]');

    // If the input is not visible, click the "Add Task" button to open it
    if (!(await addInput.isVisible())) {
        await page.getByRole("button", { name: /Add Task/i }).click();
    }

    await addInput.fill(name);
    await addInput.press("Enter");
    await expect(page.getByRole("cell", { name })).toBeVisible();
}

/** Close the AddTaskRow input if it's open (press Escape). */
async function closeAddTaskInput(page: Page) {
    const addInput = page.locator('input[name="taskName"]');
    if (await addInput.isVisible()) {
        await addInput.press("Escape");
    }
}

/**
 * Open the task detail panel by clicking a non-inline-editable cell in the row.
 * Name and Duration cells have stopPropagation (inline edit), so we click the
 * start_date or percent_complete cell instead to trigger the row onClick → panel.
 */
async function openTaskDetailPanel(page: Page, taskName: string) {
    const taskRow = page.getByRole("row").filter({ hasText: taskName });
    // Click the "0%" text in the percent_complete column — it's plain text, no stopPropagation
    await taskRow.getByText("%").click();
    await expect(page.getByRole("dialog")).toBeVisible();
}

test.describe("Task Flow", () => {
    test("Create task from empty state", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 1";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Verify empty state
        await expect(page.getByText("No tasks")).toBeVisible();

        // Click Add Task in empty state → switches to table with AddTaskRow input
        await page.getByRole("button", { name: /Add Task/i }).click();

        // Type name and hit Enter
        const taskName = "My First Task";
        await page.locator('input[name="taskName"]').fill(taskName);
        await page.locator('input[name="taskName"]').press("Enter");

        // Verify task appears in table
        await expect(page.getByRole("cell", { name: taskName })).toBeVisible();
    });

    test("Create task from add row with existing tasks", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 2";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Add first task
        await addTask(page, "Task A");

        // Close the input (stays open for rapid entry after submit), then reopen
        await closeAddTaskInput(page);

        // Add second task
        await addTask(page, "Task B");
    });

    test("Inline edit task name", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 3";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Add task
        await addTask(page, "Old Name");
        await closeAddTaskInput(page);

        // Click the task name cell to trigger inline edit (TaskInlineEdit div click → isEditing)
        await page.getByRole("cell", { name: "Old Name" }).click();

        // TaskInlineEdit renders an <Input> inside the cell (auto-focused via useEffect).
        // After closeAddTaskInput, this is the only input in the table.
        const editInput = page.locator("table input");
        await editInput.fill("New Name");
        await editInput.press("Enter");

        // Verify updated
        await expect(page.getByRole("cell", { name: "New Name" })).toBeVisible();
        await expect(page.getByRole("cell", { name: "Old Name" })).not.toBeVisible();
    });

    test("Open task detail panel and edit", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 4";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Add task
        await addTask(page, "Panel Task");
        await closeAddTaskInput(page);

        // Click a non-name cell to trigger row onClick → opens detail panel
        // (clicking the name cell would open inline edit due to stopPropagation)
        await openTaskDetailPanel(page, "Panel Task");

        const panel = page.getByRole("dialog");

        // The panel title contains an Input for the task name (no label, first input in panel)
        const nameInput = panel.locator("input").first();
        await expect(nameInput).toHaveValue("Panel Task");

        // Edit task name in panel
        await nameInput.fill("Updated Panel Task");

        // Blur to trigger save
        await nameInput.press("Tab");

        // Close panel
        await page.keyboard.press("Escape");
        await expect(panel).not.toBeVisible();

        // Confirm task name change in table
        await expect(page.getByRole("cell", { name: "Updated Panel Task" })).toBeVisible();
    });

    test("Indent and outdent task", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 5";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Add Parent
        await addTask(page, "Parent Task");
        await closeAddTaskInput(page);

        // Add Child
        await addTask(page, "Child Task");
        await closeAddTaskInput(page);

        // Select Child using checkbox (checkbox has stopPropagation, won't trigger row click)
        const childRow = page.getByRole("row", { name: /Child Task/i });
        await childRow.getByRole("checkbox").check();

        // Indent
        await page.getByRole("button", { name: /Indent/i }).click();

        // WBS code should change from "2" to "1.1"
        await expect(childRow.getByText("1.1")).toBeVisible();

        // Outdent
        await page.getByRole("button", { name: /Outdent/i }).click();

        // WBS back to "2"
        await expect(childRow.getByText("2", { exact: true })).toBeVisible();
    });

    test("Add and delete dependency", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 6";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Add Predecessor
        await addTask(page, "Task 1");
        await closeAddTaskInput(page);

        // Add Successor
        await addTask(page, "Task 2");
        await closeAddTaskInput(page);

        // Open successor's detail panel (click non-name cell)
        await openTaskDetailPanel(page, "Task 2");

        const panel = page.getByRole("dialog");

        // Add dependency
        await panel.getByRole("button", { name: "Add Dependency" }).click();

        // AddDependencyDialog opens with title "Add Dependency"
        const depDialog = page.getByRole("dialog", { name: "Add Dependency" });
        await expect(depDialog).toBeVisible();

        // Select predecessor task from the Select
        await depDialog.locator("#predecessor").click();
        await page.getByRole("option", { name: /Task 1/i }).click();

        // Confirm (button text is "Add")
        await depDialog.getByRole("button", { name: "Add" }).click();
        await expect(depDialog).not.toBeVisible();

        // Verify dependency appears in the panel list
        // Rendered as separate spans: task name + dependency type badge
        await expect(panel.getByText("Task 1")).toBeVisible();
        await expect(panel.getByText("FS")).toBeVisible();

        // Delete dependency using the trash icon button in the dependency item
        const depItem = panel.locator(".rounded-md.border").filter({ hasText: "Task 1" });
        await depItem.getByRole("button").click();

        // Verify removed — the dep item should no longer exist
        await expect(depItem).not.toBeVisible();
    });

    test("Error state on mock network failure", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Task Project 7";
        await createProject(page, projectName, "Desc");
        await navigateToTasks(page, projectName);

        // Intercept tasks endpoint to fail on POST
        await page.route("**/api/v1/projects/*/tasks", (route) => {
            if (route.request().method() === "POST") {
                route.abort("failed");
            } else {
                route.continue();
            }
        });

        // Add task to trigger POST
        await page.getByRole("button", { name: /Add Task/i }).click();
        await page.locator('input[name="taskName"]').fill("Fail Task");
        await page.locator('input[name="taskName"]').press("Enter");

        // Verify error toast (from AddTaskRow onError: toast.error("Failed to create task"))
        await expect(page.getByText(/Failed to create task/i)).toBeVisible();
    });
});
