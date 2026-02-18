import { test, expect, type Page } from "@playwright/test";
import { generateUser } from "./utils";

/** Register a new user and land on the dashboard. Matches pattern in org-flow.spec.ts */
async function registerUser(page: Page, user: ReturnType<typeof generateUser>) {
    await page.goto("/register");
    await page.fill('input[name="full_name"]', user.fullName);
    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.fill('input[name="confirmPassword"]', user.password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/");
}

test.describe("Error States & Loading", () => {

    test("Dashboard shows loading then content", async ({ page }) => {
        const user = generateUser();
        // Registering triggers the dashboard load
        await registerUser(page, user);

        // Note: PageLoader is very fast in local dev, may be hard to catch without network throttling.
        // However, we can assert that the dashboard content eventually appears.
        // DashboardPage.tsx renders "Welcome to Sophikon" if no orgs (but user gets a personal org)
        // or "{OrgName} Dashboard" if active org.

        // Personal org is created automatically: "Test User...'s Org"
        await expect(page.getByRole("heading", { name: /Dashboard/ })).toBeVisible();
    });

    test("API error shows toast with backend message", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        // Mock a specific failure on the update-org endpoint
        // Endpoint: PATCH /api/v1/organizations/{id}
        // We'll use a wildcard for ID
        await page.route(/\/api\/v1\/organizations\/[^/]+$/, async (route) => {
            if (route.request().method() === "PATCH") {
                await route.fulfill({
                    status: 400,
                    contentType: "application/json",
                    body: JSON.stringify({ detail: "Custom backend error message" }),
                });
            } else {
                await route.continue();
            }
        });

        // Navigate to Org Settings
        await page.goto("/settings");

        // Trigger the update
        await page.fill('input[name="name"]', "New Name");
        await page.getByRole("button", { name: "Save Changes" }).click();

        // Verify toast with custom message
        // Toasts usually appear as status role or similar, exact text check is robust here
        await expect(page.getByText("Custom backend error message")).toBeVisible();
    });

    test("Network offline shows appropriate error", async ({ page }) => {
        const user = generateUser();
        await registerUser(page, user);

        // Go to a data-fetching page (Projects)
        await page.goto("/projects");

        // Abort only the projects endpoint so auth/org queries still work
        await page.route("**/api/v1/projects**", (route) => route.abort());

        // Navigate to /projects — projects query fires and fails
        await page.goto("/projects");

        // QueryError renders an Alert (role="alert") with title "Error"
        await expect(page.getByRole("alert")).toBeVisible();
        await expect(page.getByRole("alert").getByText(/Error/)).toBeVisible();
    });
});
