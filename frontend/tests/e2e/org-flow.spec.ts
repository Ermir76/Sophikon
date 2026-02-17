import { test, expect, type Page } from "@playwright/test";
import { generateUser } from "./utils";

/** Open the OrgSwitcher dropdown and click "Add Organization" to open the create dialog. */
async function openCreateOrgDialog(page: Page) {
    await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
    await page.getByRole("menuitem").filter({ hasText: "Add Organization" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
}

/** Fill and submit the create-org dialog. */
async function createOrg(page: Page, name: string, slug: string) {
    await openCreateOrgDialog(page);
    await page.getByRole("dialog").locator('input[name="name"]').fill(name);
    await page.getByRole("dialog").locator('input[name="slug"]').fill(slug);
    await page.getByRole("dialog").getByRole("button", { name: "Create" }).click();
    await expect(page.getByText("Organization created")).toBeVisible();
}

test.describe("Organization Flow", () => {
    test("Create organization -> appears in org switcher", async ({ page }) => {
        const user = generateUser();

        // 1. Register & Login
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Verify Org Switcher exists (Personal Org)
        await expect(page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]')).toBeVisible();

        // 3. Create org via dialog
        const newOrgName = "Acme Corp";
        const newOrgSlug = `acme-${Date.now()}`;
        await createOrg(page, newOrgName, newOrgSlug);

        // 4. Verify Org Switcher
        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        await expect(page.getByRole("menuitem").filter({ hasText: newOrgName })).toBeVisible();
    });

    test("Switch between organizations -> sidebar updates", async ({ page }) => {
        const user = generateUser();

        // 1. Register
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Create Second Org via dialog
        const org2Name = "Org Beta";
        const org2Slug = `beta-${Date.now()}`;
        await createOrg(page, org2Name, org2Slug);

        // Current active org should be Org Beta
        await expect(page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]')).toHaveText(new RegExp(org2Name));

        // 3. Switch back to Personal Org
        const personalOrgName = `${user.fullName}'s Org`;

        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        await page.getByRole("menuitem").filter({ hasText: personalOrgName }).click();

        // 4. Verify Sidebar Updates
        await expect(page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]')).toHaveText(new RegExp(personalOrgName));

        // 5. Switch back to Org Beta
        await expect(page.getByRole("menuitem").filter({ hasText: personalOrgName })).toBeHidden();
        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        await page.getByRole("menuitem").filter({ hasText: org2Name }).click();
        await expect(page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]')).toHaveText(new RegExp(org2Name));
    });

    test("Update org name -> reflected in switcher", async ({ page }) => {
        const user = generateUser();

        // 1. Register
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // Use Personal Org
        const personalOrgName = `${user.fullName}'s Org`;

        // 2. Go to Settings
        await page.goto("/organizations/settings");

        // 3. Wait for form to load with current org data, then update name
        const nameInput = page.locator('input[name="name"]');
        await expect(nameInput).toHaveValue(personalOrgName);

        const updatedName = "Updated Name Org";
        await nameInput.fill(updatedName);
        await page.click('button[type="submit"]');

        // 4. Verify Toast
        await expect(page.getByText("Organization updated", { exact: true })).toBeVisible();

        // 5. Verify Switcher
        await expect(page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]')).toHaveText(new RegExp(updatedName));

        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        await expect(page.getByRole("menuitem").filter({ hasText: updatedName })).toBeVisible();
    });

    test("Delete org -> removed from switcher, redirected", async ({ page }) => {
        const user = generateUser();

        // 1. Register
        await page.goto("/register");
        await page.fill('input[name="full_name"]', user.fullName);
        await page.fill('input[name="email"]', user.email);
        await page.fill('input[name="password"]', user.password);
        await page.fill('input[name="confirmPassword"]', user.password);
        await page.click('button[type="submit"]');
        await expect(page).toHaveURL("/");

        // 2. Create Org to Delete (Cannot delete personal org)
        const orgToDelete = "Delete Me Corp";
        await createOrg(page, orgToDelete, `delete-${Date.now()}`);

        // 3. Go to Settings and wait for page to load
        await page.goto("/organizations/settings");
        await expect(page.locator('input[name="name"]')).toHaveValue(orgToDelete);

        // 4. Delete
        await page.getByRole("button", { name: "Delete Organization" }).click();

        // 5. Confirm in dialog
        await expect(page.getByRole("alertdialog")).toBeVisible();
        await page.getByRole("alertdialog").getByRole("button", { name: "Delete Organization" }).click();

        // 6. Verify Redirect & Toast
        await expect(page.getByText("Organization deleted", { exact: true })).toBeVisible();
        await expect(page).toHaveURL("/");

        // 7. Verify Gone from Switcher
        const personalOrgName = `${user.fullName}'s Org`;
        await expect(page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]')).toHaveText(new RegExp(personalOrgName));

        await page.locator('[data-sidebar="header"] [data-sidebar="menu-button"]').click();
        await expect(page.getByRole("menuitem").filter({ hasText: orgToDelete })).toBeHidden();
        await expect(page.getByRole("menuitem").filter({ hasText: personalOrgName })).toBeVisible();
    });
});
