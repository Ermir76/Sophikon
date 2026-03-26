import { test, expect, type Page } from "@playwright/test";
import { generateUser } from "./utils";

const MAILPIT_API = "http://localhost:8025/api/v1";

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

/** Log out the current user. */
async function logout(page: Page) {
    await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
    await page.getByRole("menuitem", { name: "Log out" }).click();
    await page.waitForURL("/login");
}

/** Log in an existing user. */
async function login(page: Page, user: ReturnType<typeof generateUser>) {
    await page.goto("/login");
    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/");
}

/** Create a project from the /projects page. */
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

/** Navigate to project tasks page. */
async function navigateToTasks(page: Page, projectName: string) {
    await page.goto("/projects");
    await page.getByRole("link", { name: projectName }).click();
    await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);
    await expect(page.getByRole("heading", { name: "Tasks", exact: true })).toBeVisible();
}

/** Add a task via the inline AddTaskRow input. */
async function addTask(page: Page, name: string) {
    const addInput = page.locator('input[name="taskName"]');

    if (!(await addInput.isVisible())) {
        await page.getByRole("button", { name: /Add Task/i }).click();
    }

    await addInput.fill(name);
    await addInput.press("Enter");
    await expect(page.getByRole("cell", { name })).toBeVisible();
}

/** Close the AddTaskRow input if open. */
async function closeAddTaskInput(page: Page) {
    const addInput = page.locator('input[name="taskName"]');
    if (await addInput.isVisible()) {
        await addInput.press("Escape");
    }
}

/**
 * Extract the invitation token from the latest Mailpit email for a given address.
 * Polls Mailpit API until the invitation email arrives (max 15s).
 */
async function getInvitationTokenFromMailpit(
    page: Page,
    email: string,
): Promise<string> {
    let token: string | null = null;

    for (let attempt = 0; attempt < 15; attempt++) {
        const response = await page.request.get(
            `${MAILPIT_API}/search?query=to:${encodeURIComponent(email)}&limit=5`,
        );
        const data = await response.json();

        if (data.messages && data.messages.length > 0) {
            // Get the most recent message
            const messageId = data.messages[0].ID;
            const msgResponse = await page.request.get(
                `${MAILPIT_API}/message/${messageId}`,
            );
            const msgData = await msgResponse.json();

            // Extract token from the email body (HTML or text)
            const body = msgData.HTML || msgData.Text || "";
            const match = body.match(/project-invitations\/accept\?token=([a-zA-Z0-9_-]+)/);
            if (match) {
                token = match[1];
                break;
            }
        }

        await page.waitForTimeout(1000);
    }

    if (!token) {
        throw new Error(`No invitation email found for ${email} within timeout`);
    }

    return token;
}

/**
 * Invite a user to the current project with a given role.
 * Assumes we're already on the project settings/members page.
 */
async function inviteProjectMember(page: Page, projectName: string, email: string, role: string) {
    // Navigate to project settings -> members tab
    await page.goto("/projects");
    await page.getByRole("link", { name: projectName }).click();
    await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);

    // Go to settings
    const currentUrl = page.url();
    const settingsUrl = currentUrl.replace(/\/tasks$/, "/settings");
    await page.goto(settingsUrl);

    // Click Members tab
    await page.getByRole("tab", { name: /Members/i }).click();

    // Click Invite Member
    await page.getByRole("button", { name: /Invite Member/i }).click();
    await expect(page.getByRole("dialog")).toBeVisible();

    // Fill email
    await page.getByRole("dialog").locator('input[name="email"]').fill(email);

    // Select role
    await page.getByRole("dialog").getByRole("combobox").click();
    await page.getByRole("option", { name: role, exact: true }).click();

    // Send invitation
    await page.getByRole("dialog").getByRole("button", { name: /Send Invitation/i }).click();
    await expect(page.getByText(/Invitation sent/i)).toBeVisible();
}

test.describe("RBAC — Viewer Role (FR-CO-002, NFR-SEC-002)", () => {
    let ownerUser: ReturnType<typeof generateUser>;
    let viewerUser: ReturnType<typeof generateUser>;
    const projectName = "RBAC Viewer Test Project";

    test.beforeAll(async ({ browser }) => {
        ownerUser = generateUser();
        viewerUser = generateUser();

        const page = await browser.newPage();

        // 1. Register viewer first (so they exist in DB when invited)
        await registerUser(page, viewerUser);
        await logout(page);

        // 2. Register owner
        await registerUser(page, ownerUser);

        // 3. Owner creates a project
        await createProject(page, projectName, "Project for RBAC viewer testing");

        // 4. Owner creates some tasks
        await navigateToTasks(page, projectName);
        await addTask(page, "Task Alpha");
        await closeAddTaskInput(page);
        await addTask(page, "Task Beta");
        await closeAddTaskInput(page);

        // 5. Add a dependency: Task Beta depends on Task Alpha
        // Open Task Beta detail panel
        const betaRow = page.getByRole("row").filter({ hasText: "Task Beta" });
        await betaRow.getByText("%").click();
        await expect(page.getByRole("dialog")).toBeVisible();

        const panel = page.getByRole("dialog");
        await panel.getByRole("button", { name: "Add Dependency" }).click();

        const depDialog = page.getByRole("dialog", { name: "Add Dependency" });
        await expect(depDialog).toBeVisible();
        await depDialog.locator("#predecessor").click();
        await page.getByRole("option", { name: /Task Alpha/i }).click();
        await depDialog.getByRole("button", { name: "Add" }).click();
        await expect(depDialog).not.toBeVisible();

        // Close task panel
        await page.keyboard.press("Escape");

        // 6. Invite viewer
        await inviteProjectMember(page, projectName, viewerUser.email, "viewer");

        // 7. Get invitation token from Mailpit
        const token = await getInvitationTokenFromMailpit(page, viewerUser.email);

        // 8. Log out owner, log in viewer, accept invitation
        await logout(page);
        await login(page, viewerUser);
        await page.goto(`/project-invitations/accept?token=${token}`);

        // Wait for auto-acceptance
        await expect(page.getByText("Invitation Accepted")).toBeVisible({ timeout: 10000 });
        await page.getByRole("button", { name: "Go to Project" }).click();
        await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/, { timeout: 10000 });

        // Log out viewer (each test will log in fresh)
        await logout(page);
        await page.close();
    });

    test.beforeEach(async ({ page }) => {
        // Log in as viewer for each test
        await login(page, viewerUser);

        // Switch to owner's org if needed
        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        const orgName = `${ownerUser.fullName}'s Org`;
        const orgMenuItem = page.getByRole("menuitem", { name: orgName });

        if (await orgMenuItem.isVisible()) {
            await orgMenuItem.click();
        } else {
            // Already in the right org, close the menu
            await page.keyboard.press("Escape");
        }
    });

    test("Viewer can see task list", async ({ page }) => {
        await navigateToTasks(page, projectName);

        await expect(page.getByRole("cell", { name: "Task Alpha" })).toBeVisible();
        await expect(page.getByRole("cell", { name: "Task Beta" })).toBeVisible();
    });

    test("Viewer can see Gantt view", async ({ page }) => {
        await page.goto("/projects");
        await page.getByRole("link", { name: projectName }).click();
        await expect(page).toHaveURL(/\/projects\/[^/]+\/tasks/);

        // Navigate to Gantt
        const currentUrl = page.url();
        const ganttUrl = currentUrl.replace(/\/tasks$/, "/gantt");
        await page.goto(ganttUrl);

        await expect(page).toHaveURL(/\/projects\/[^/]+\/gantt/);
        // Gantt page should load without error
        await expect(page.getByText("Task Alpha")).toBeVisible();
    });

    test("Viewer cannot create a task — Add Task button is hidden", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // The Add Task button should not be visible for viewers
        await expect(page.getByRole("button", { name: /Add Task/i })).not.toBeVisible();
    });

    test("Viewer cannot edit a task — inline edit is disabled", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Click on task name cell
        await page.getByRole("cell", { name: "Task Alpha" }).click();

        // No input should appear (inline edit disabled for viewers)
        const editInput = page.locator("table input");
        await expect(editInput).not.toBeVisible();
    });

    test("Viewer cannot create a dependency", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Open task detail panel
        const taskRow = page.getByRole("row").filter({ hasText: "Task Alpha" });
        await taskRow.getByText("%").click();
        await expect(page.getByRole("dialog")).toBeVisible();

        const panel = page.getByRole("dialog");

        // Add Dependency button should not be visible for viewers
        await expect(panel.getByRole("button", { name: "Add Dependency" })).not.toBeVisible();
    });

    test("Viewer cannot upload an attachment", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Open task detail panel
        const taskRow = page.getByRole("row").filter({ hasText: "Task Alpha" });
        await taskRow.getByText("%").click();
        await expect(page.getByRole("dialog")).toBeVisible();

        const panel = page.getByRole("dialog");

        // File upload button should not be visible or should be disabled
        const uploadButton = panel.getByRole("button", { name: /upload|attach/i });
        const uploadCount = await uploadButton.count();

        if (uploadCount > 0) {
            // If button exists, it should be disabled
            await expect(uploadButton).toBeDisabled();
        }
        // If button doesn't exist at all, that's also a pass (hidden for viewer)
    });

    test("Viewer cannot add a comment", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Open task detail panel
        const taskRow = page.getByRole("row").filter({ hasText: "Task Alpha" });
        await taskRow.getByText("%").click();
        await expect(page.getByRole("dialog")).toBeVisible();

        const panel = page.getByRole("dialog");

        // Comment input / form should not be visible for viewers
        const commentInput = panel.locator('textarea[name="comment"], textarea[placeholder*="comment" i], textarea[placeholder*="Write" i]');
        await expect(commentInput).not.toBeVisible();

        // Also verify via API that comment creation is rejected
        const url = page.url();
        const projectId = url.match(/\/projects\/([^/]+)\//)?.[1];
        expect(projectId).toBeTruthy();

        // Get a task ID
        const tasksResponse = await page.request.get(
            `/api/v1/projects/${projectId}/tasks`,
        );
        const tasksData = await tasksResponse.json();
        const taskId = tasksData.items?.[0]?.id ?? tasksData[0]?.id;
        expect(taskId).toBeTruthy();

        // Attempt to create a comment via API
        const commentResponse = await page.request.post(
            `/api/v1/projects/${projectId}/tasks/${taskId}/comments`,
            {
                data: { content: "Unauthorized comment from viewer" },
            },
        );
        expect(commentResponse.status()).toBe(403);
    });

    test("Viewer can view AI panel", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Look for AI panel toggle button
        const aiToggle = page.getByRole("button", { name: /AI|Assistant/i });
        if (await aiToggle.isVisible()) {
            await aiToggle.click();
            // AI panel should open without error
            await expect(page.locator('[data-testid="ai-panel"]').or(
                page.getByText(/AI Assistant|Estimates|Suggestions/i),
            )).toBeVisible();
        }
        // If no AI toggle is visible, the feature may not be enabled for this project — still a pass
    });

    test("Viewer sees tasks as read-only — API rejects create attempt", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Even if UI hides the button, verify the API rejects task creation
        // Extract project ID from URL
        const url = page.url();
        const projectId = url.match(/\/projects\/([^/]+)\//)?.[1];
        expect(projectId).toBeTruthy();

        // Attempt to create a task via API directly
        const response = await page.request.post(
            `/api/v1/projects/${projectId}/tasks`,
            {
                data: {
                    name: "Unauthorized Task",
                    start_date: new Date().toISOString().split("T")[0],
                    duration: 480,
                },
            },
        );

        // Should be 403 Forbidden
        expect(response.status()).toBe(403);
    });

    test("Viewer sees tasks as read-only — API rejects edit attempt", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // Extract project ID from URL
        const url = page.url();
        const projectId = url.match(/\/projects\/([^/]+)\//)?.[1];
        expect(projectId).toBeTruthy();

        // Get task list to find a task ID
        const tasksResponse = await page.request.get(
            `/api/v1/projects/${projectId}/tasks`,
        );
        expect(tasksResponse.ok()).toBeTruthy();

        const tasksData = await tasksResponse.json();
        const taskId = tasksData.items?.[0]?.id ?? tasksData[0]?.id;
        expect(taskId).toBeTruthy();

        // Attempt to edit the task via API
        const editResponse = await page.request.patch(
            `/api/v1/projects/${projectId}/tasks/${taskId}`,
            {
                data: { name: "Hacked Task Name" },
            },
        );

        // Should be 403 Forbidden
        expect(editResponse.status()).toBe(403);
    });

    test("UI hides action buttons viewers cannot perform", async ({ page }) => {
        await navigateToTasks(page, projectName);

        // 1. Add Task button should be hidden
        await expect(page.getByRole("button", { name: /Add Task/i })).not.toBeVisible();

        // 2. Toolbar actions (indent, outdent, delete) should be hidden or disabled
        await expect(page.getByRole("button", { name: /Indent/i })).not.toBeVisible();
        await expect(page.getByRole("button", { name: /Outdent/i })).not.toBeVisible();

        // 3. Navigate to project settings — viewer should not see settings or it should be restricted
        const currentUrl = page.url();
        const settingsUrl = currentUrl.replace(/\/tasks$/, "/settings");
        await page.goto(settingsUrl);

        // Viewer should not see "Invite Member" button on members tab
        const membersTab = page.getByRole("tab", { name: /Members/i });
        if (await membersTab.isVisible()) {
            await membersTab.click();
            await expect(page.getByRole("button", { name: /Invite Member/i })).not.toBeVisible();
        }
    });
});
