import { test, expect } from "@playwright/test";
import { generateUser } from "./utils";

test.describe("Authentication Flow", () => {
    let user: ReturnType<typeof generateUser>;

    test.beforeEach(async ({ page }) => {
        // Generate a fresh unique user for each test if needed,
        // though for sequential flow we might keep it simple.
        user = generateUser();
    });

    // Helper to open user menu safely by targeting the footer specifically
    const openUserMenu = async (page: any) => {
        // NavUser is rendered in SidebarFooter, while OrgSwitcher is in SidebarHeader.
        // Scoping to [data-sidebar="footer"] removes ambiguity with OrgSwitcher.
        // We use .first() to handle potential mobile/desktop duplication within the footer itself.
        await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
    };

    test("Register -> Dashboard -> Logout", async ({ page }) => {
        // 1. Register
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password); // Verified: camelCase in RegisterPage.tsx
        await page.click('button[type="submit"]');

        // 2. Expect Dashboard (AT ROOT /)
        await expect(page).toHaveURL("/");

        // Verify we are logged in by checking the User Menu in the footer
        const userMenuButton = page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first();
        await expect(userMenuButton).toBeVisible();
        await expect(userMenuButton).toContainText(user.fullName);

        // 3. Logout
        await openUserMenu(page);
        await page.getByRole('menuitem', { name: 'Log out' }).click();

        // 4. WAIT FOR REDIRECT
        await page.waitForURL("/login");
        await expect(page).toHaveURL("/login");

        // 5. Verify protected route access redirects to login (CRITICAL TEST)
        await page.goto("/");
        await expect(page).toHaveURL("/login");
    });

    test("Register with Existing Email -> Shows Error", async ({ page }) => {
        // 1. Register first time
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Logout
        await openUserMenu(page);
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // 3. Try to register AGAIN with same email
        await page.goto("/register");
        await page.fill('input[name="full_name"]', "Imposter");
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', "NewPass123!");
        await page.fill('input[name="confirmPassword"]', "NewPass123!");
        await page.click('button[type="submit"]');

        // 4. Expect Error
        // The error is rendered in an Alert component
        const alert = page.getByRole("alert");
        await expect(alert).toBeVisible();
        await expect(alert).toContainText("Email already registered"); // Verified text from typical backend response
        await expect(page).toHaveURL("/register");
    });

    test("Login with Correct Password -> Lands on Dashboard", async ({ page }) => {
        // 1. Register first
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Logout
        await openUserMenu(page);
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // 3. Login
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.click('button[type="submit"]');

        // 4. Expect Dashboard
        await expect(page).toHaveURL("/");
        const userMenuButton = page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first();
        await expect(userMenuButton).toBeVisible();
        await expect(userMenuButton).toContainText(user.fullName);
    });

    test("Session Persists on Reload", async ({ page }) => {
        // 1. Register/Login
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Reload Page
        await page.reload();

        // 3. Still on Dashboard?
        await expect(page).toHaveURL("/");
        const userMenuButton = page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first();
        await expect(userMenuButton).toBeVisible();
    });

    test("Login with Wrong Password -> Shows Error", async ({ page }) => {
        // 1. Register FIRST so the user explicitly exists
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Logout
        await openUserMenu(page);
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // 3. Try Login with WRONG password
        await page.goto("/login");
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', "WrongPass");
        await page.click('button[type="submit"]');

        // Make sure we see an error
        const alert = page.getByRole("alert");
        await expect(alert).toBeVisible();
        await expect(page).toHaveURL("/login");
    });
});
