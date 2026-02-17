import { randomUUID } from "crypto";

// Helper to generate unique user data
export const generateUser = () => {
    const uniqueId = randomUUID();
    return {
        email: `testuser_${uniqueId}@example.com`,
        password: "StrongPassword123!",
        fullName: `Test User ${uniqueId}`,
    };
};
