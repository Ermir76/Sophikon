import { test, expect, type Page } from "@playwright/test";
import { generateUser } from "./utils";

/** Register a new user and land on the dashboard. Matches pattern in org-flow.spec.ts */
async function registerUser(page: Page, user: ReturnType<typeof generateUser>) {
    await page.goto("/register");
    // Fields from RegisterPage.tsx: full_name, email, password, confirmPassword
    await page.fill('input[name="full_name"]', user.fullName);
    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.fill('input[name="confirmPassword"]', user.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/");
}

/** Create a project using the dialog. Matches pattern in project-flow.spec.ts */
async function createProject(page: Page, name: string) {
    await page.goto("/projects");
    await page.getByRole("button", { name: "New Project" }).click(); // DialogTrigger in CreateProjectDialog
    await page.getByRole("dialog").locator('input[name="name"]').fill(name);

    // Date picker interaction
    await page.getByRole("dialog").getByRole("button", { name: "Start Date" }).click();
    await page.getByRole("gridcell", { name: /^Today/ }).getByRole("button").click();

    await page.getByRole("dialog").getByRole("button", { name: "Create Project" }).click();
    await expect(page.getByText("Project created")).toBeVisible();
}

test.describe("Navigation & Layout", () => {

    test("Sidebar switches between global and project mode", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        const projectName = "Sidebar Test Project";
        await createProject(page, projectName);

        // 1. Verify Global Nav Items (AppSidebar.tsx: globalNavItems)
        await page.goto("/");
        // Scope to sidebar content to avoid ambiguity with breadcrumbs
        const sidebar = page.locator('[data-sidebar="content"]');

        // Look for links with exact titles from AppSidebar.tsx
        await expect(sidebar.getByRole("link", { name: "Dashboard" })).toBeVisible();
        await expect(sidebar.getByRole("link", { name: "Projects", exact: true })).toBeVisible();
        await expect(sidebar.getByRole("link", { name: "Settings" })).toBeVisible(); // Admin/Owner sees this

        // 2. Enter Project Context
        await page.goto("/projects");
        await page.getByRole("link", { name: projectName }).click();

        // 3. Verify Project Nav Items (AppSidebar.tsx: projectNavItems)
        await expect(sidebar.getByRole("link", { name: "Back to Projects" })).toBeVisible();
        await expect(sidebar.getByRole("link", { name: "Overview" })).toBeVisible();
        await expect(sidebar.getByRole("link", { name: "Tasks" })).toBeVisible();

        // 4. Verify Global Items are Hidden in Project Mode
        await expect(sidebar.getByRole("link", { name: "Dashboard" })).not.toBeVisible();
        await expect(sidebar.getByRole("link", { name: "Members" })).not.toBeVisible();
    });

    test("Org switcher shows all user's organizations", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        // 1. Create a second organization
        // Open Org Switcher (SidebarHeader -> OrgSwitcher)
        // Selector derived from OrgSwitcher.tsx: SidebarMenuButton inside SidebarHeader
        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        await page.getByRole("menuitem", { name: "Add Organization" }).click();

        const org2Name = "Second Org";
        await page.getByRole("dialog").locator('input[name="name"]').fill(org2Name);
        await page.getByRole("dialog").locator('input[name="slug"]').fill(`org2-${Date.now()}`);
        await page.getByRole("dialog").getByRole("button", { name: "Create" }).click();
        await expect(page.getByText("Organization created")).toBeVisible();

        // 2. Open Org Switcher again
        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();

        // 3. Verify both orgs are present as menu items
        // Personal org name format: "{fullName}'s Org"
        const personalOrgName = `${user.fullName}'s Org`;
        await expect(page.getByRole("menuitem", { name: personalOrgName })).toBeVisible();
        await expect(page.getByRole("menuitem", { name: org2Name })).toBeVisible();
    });

    test("Protected routes redirect to login", async ({ page }) => {
        // Do not register/login
        const protectedPaths = ["/", "/projects", "/settings"];

        for (const path of protectedPaths) {
            await page.goto(path);
            // ProtectedRoute.tsx redirects to /login
            await expect(page).toHaveURL("/login");
        }
    });

    test("404 page shows for unknown routes", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        // Navigate to nonexistent path
        await page.goto("/some/nonexistent/path");

        // Verify 404 content (NotFoundPage.tsx)
        await expect(page.getByRole("heading", { name: "404" })).toBeVisible();
        await expect(page.getByText("Page not found")).toBeVisible();

        // Click link back to dashboard
        await page.getByRole("link", { name: "Go to Dashboard" }).click();
        await expect(page).toHaveURL("/");
    });

    test("Responsive: sidebar collapses on mobile", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        // Set viewport to mobile (use-mobile.ts: MOBILE_BREAKPOINT = 768)
        await page.setViewportSize({ width: 375, height: 667 });

        // Sidebar should be hidden initially on mobile
        // Sidebar.tsx: data-mobile="true" sheet is used on mobile, triggers via button
        // When closed, the sheet content is not visible.
        // We verify the toggle button is visible.
        // Trigger accessibility name from SidebarTrigger: "Toggle Sidebar"
        const trigger = page.getByRole("button", { name: "Toggle Sidebar" });
        await expect(trigger).toBeVisible();

        // Open Sidebar
        await trigger.click();

        // Sidebar sheet should be visible
        // Sidebar.tsx: SheetContent has data-sidebar="sidebar" and data-mobile="true"
        const mobileSidebar = page.locator('[data-sidebar="sidebar"][data-mobile="true"]');
        await expect(mobileSidebar).toBeVisible();

        // Verify nav items are inside
        await expect(mobileSidebar.getByRole("link", { name: "Dashboard" })).toBeVisible();

        // Reset to desktop
        await page.setViewportSize({ width: 1280, height: 800 });

        // Mobile sheet should be hidden/gone
        await expect(mobileSidebar).not.toBeVisible();

        // Desktop sidebar should be visible
        // data-slot="sidebar" is the desktop implementation (hidden on mobile, block on md usually)
        await expect(page.locator('[data-slot="sidebar"][data-state="expanded"]')).toBeVisible();
    });
});
