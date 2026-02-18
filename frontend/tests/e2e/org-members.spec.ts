import { test, expect } from "@playwright/test";
import { generateUser } from "./utils";

test.describe("Organization Members Flow", () => {
    let owner: ReturnType<typeof generateUser>;
    let member: ReturnType<typeof generateUser>;

    test.beforeAll(() => {
        owner = generateUser();
        member = generateUser();
    });

    test("Owner can invite new member", async ({ page }) => {
        // 1. Register Member FIRST (so they exist in DB)
        await page.goto("/register");
        await page.fill('input[name="full_name"]', member.fullName);
        await page.fill('input[name="email"]', member.email);
        await page.fill('input[name="password"]', member.password);
        await page.fill('input[name="confirmPassword"]', member.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // Logout Member
        await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // 2. Register Owner
        await page.goto("/register");
        await page.fill('input[name="full_name"]', owner.fullName);
        await page.fill('input[name="email"]', owner.email);
        await page.fill('input[name="password"]', owner.password);
        await page.fill('input[name="confirmPassword"]', owner.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 3. Go to Members Page
        await page.goto("/members");

        // 4. Invite Member
        await page.getByRole("button", { name: "Invite Member" }).click();
        await page.fill('input[name="email"]', member.email);
        // Default role is usually 'member', let's stick with that
        await page.getByRole("button", { name: "Send Invitation" }).click();

        // 5. Verify Success
        // Toast message
        await expect(page.getByText("Invitation sent")).toBeVisible();

        // Member in table
        await expect(page.getByRole("cell", { name: member.email })).toBeVisible();
        await expect(page.getByRole("cell", { name: "member", exact: true })).toBeVisible();
    });

    test("Owner can change member role", async ({ page }) => {
        // Reuse state from previous test if possible, but for isolation let's assume we are logged in as owner
        // Since playright workers are isolated, we need to redo setup or use storage state.
        // For simplicity/reliability in this specific task, I'll repeat the setup or assume sequential execution if configured.
        // But better to be explicit.

        // Fast-track setup: Register Owner & Invite Member (or just use the previous flow?)
        // Let's make this test dependent on the previous state? No, bad practice.
        // I will do a quick setup.

        // Ideally we'd use a Setup fixture, but I'll write it inline for now.
        const owner2 = generateUser();
        const member2 = generateUser();

        // Register Member2
        await page.goto("/register");
        await page.fill('input[name="full_name"]', member2.fullName);
        await page.fill('input[name="email"]', member2.email);
        await page.fill('input[name="password"]', member2.password);
        await page.fill('input[name="confirmPassword"]', member2.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");
        await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // Register Owner2
        await page.goto("/register");
        await page.fill('input[name="full_name"]', owner2.fullName);
        await page.fill('input[name="email"]', owner2.email);
        await page.fill('input[name="password"]', owner2.password);
        await page.fill('input[name="confirmPassword"]', owner2.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // Invite Member2
        await page.goto("/members");
        await page.getByRole("button", { name: "Invite Member" }).click();
        await page.fill('input[name="email"]', member2.email);
        await page.getByRole("button", { name: "Send Invitation" }).click();
        await expect(page.getByRole("cell", { name: member2.email })).toBeVisible();

        // CHANGE ROLE
        // Find row with member email
        const row = page.getByRole("row", { name: member2.email });
        // Click actions menu (sr-only "Open menu")
        await row.getByRole("button", { name: "Open menu" }).click();
        // Hover/Click "Change Role"
        await page.getByText("Change Role").click(); // Submenu trigger
        // Select "Admin"
        await page.getByRole("menuitemradio", { name: "Admin" }).click();

        // Verify
        await expect(page.getByText("Role updated", { exact: true })).toBeVisible();
        await expect(row.getByRole("cell", { name: "admin" })).toBeVisible();
    });

    test("Owner can remove member", async ({ page }) => {
        // Setup Owner3 & Member3
        const owner3 = generateUser();
        const member3 = generateUser();

        // Register Member3
        await page.goto("/register");
        await page.fill('input[name="full_name"]', member3.fullName);
        await page.fill('input[name="email"]', member3.email);
        await page.fill('input[name="password"]', member3.password);
        await page.fill('input[name="confirmPassword"]', member3.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");
        await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // Register Owner3
        await page.goto("/register");
        await page.fill('input[name="full_name"]', owner3.fullName);
        await page.fill('input[name="email"]', owner3.email);
        await page.fill('input[name="password"]', owner3.password);
        await page.fill('input[name="confirmPassword"]', owner3.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // Invite Member3
        await page.goto("/members");
        await page.getByRole("button", { name: "Invite Member" }).click();
        await page.fill('input[name="email"]', member3.email);
        await page.getByRole("button", { name: "Send Invitation" }).click();
        await expect(page.getByRole("cell", { name: member3.email })).toBeVisible();

        // REMOVE MEMBER
        const row = page.getByRole("row", { name: member3.email });
        await row.getByRole("button", { name: "Open menu" }).click();
        await page.getByText("Remove Member").click();

        // Confirm Dialog
        await expect(page.getByRole("alertdialog")).toBeVisible();
        await page.getByRole("button", { name: "Remove Member" }).click();

        // Verify
        await expect(page.getByText("Member removed")).toBeVisible();
        await expect(page.getByRole("cell", { name: member3.email })).toBeHidden();
    });

    test("Non-admin cannot see invite/remove buttons", async ({ page }) => {
        // Setup Owner4 & Member4
        const owner4 = generateUser();
        const member4 = generateUser();

        // Register Member4
        await page.goto("/register");
        await page.fill('input[name="full_name"]', member4.fullName);
        await page.fill('input[name="email"]', member4.email);
        await page.fill('input[name="password"]', member4.password);
        await page.fill('input[name="confirmPassword"]', member4.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");
        await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // Register Owner4
        await page.goto("/register");
        await page.fill('input[name="full_name"]', owner4.fullName);
        await page.fill('input[name="email"]', owner4.email);
        await page.fill('input[name="password"]', owner4.password);
        await page.fill('input[name="confirmPassword"]', owner4.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // Invite Member4 as 'member' (default)
        await page.goto("/members");
        await page.getByRole("button", { name: "Invite Member" }).click();
        await page.fill('input[name="email"]', member4.email);
        await page.getByRole("button", { name: "Send Invitation" }).click();

        // Log out Owner4
        await page.locator('[data-sidebar="footer"] [data-sidebar="menu-button"]').first().click();
        await page.getByRole('menuitem', { name: 'Log out' }).click();
        await page.waitForURL("/login");

        // Log in Member4
        await page.goto("/login");
        await page.fill('input[name="email"]', member4.email);
        await page.fill('input[name="password"]', member4.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // SWITCH ORGANIZATION
        // Member4 needs to switch to Owner4's organization.
        // Open Org Switcher (in Header)
        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();

        // Find and select Owner4's Org (it should be listed in the dropdown)
        // Since we don't know the exact name (it's auto-generated, usually "Name's Org"),
        // we can try to guess it or just pick the second one if we assume the first is Personal.
        // Or we can retrieve Owner4's org name?
        // Actually, Owner4's name is `Test User {uuid}`. The org name defaults to `Test User {uuid}'s Org`.
        const orgName = `${owner4.fullName}'s Org`;
        await page.getByRole("menuitem", { name: orgName }).click();

        // Navigate to Members
        await page.goto("/members");

        // VERIFY RESTRICTIONS
        // 1. "Invite Member" button should NOT be visible
        await expect(page.getByRole("button", { name: "Invite Member" })).toBeHidden();

        // 2. Actions Menu
        const row = page.getByRole("row", { name: owner4.email }); // Owner should be visible
        // Click menu
        await row.getByRole("button", { name: "Open menu" }).click();

        // "Change Role" should be hidden or disabled? We conditionally render it.
        await expect(page.getByText("Change Role")).toBeHidden();

        // "Remove Member" should be hidden
        await expect(page.getByText("Remove Member")).toBeHidden();
    });
});
