import { useState, useEffect, useCallback } from "react";

export function useLocalStorageSet(key: string, initialValue: Set<string> = new Set()) {
    // Check if we're in the browser environment
    const isBrowser = typeof window !== "undefined";

    // Initialize state lazily to read from localStorage only once
    const [storedSet, setStoredSet] = useState<Set<string>>(() => {
        if (!isBrowser) return initialValue;

        try {
            const item = window.localStorage.getItem(key);
            if (item) {
                // Parse the JSON array and convert it back to a Set
                return new Set(JSON.parse(item));
            }
        } catch (error) {
            console.warn(`Error reading localStorage key "${key}":`, error);
        }
        return initialValue;
    });

    // Update localStorage whenever the state changes
    useEffect(() => {
        if (!isBrowser) return;

        try {
            // Convert Set to Array before stringifying
            window.localStorage.setItem(key, JSON.stringify(Array.from(storedSet)));
        } catch (error) {
            console.warn(`Error setting localStorage key "${key}":`, error);
        }
    }, [key, storedSet, isBrowser]);

    const add = useCallback((value: string) => {
        setStoredSet(prev => {
            const next = new Set(prev);
            next.add(value);
            return next;
        });
    }, []);

    const remove = useCallback((value: string) => {
        setStoredSet(prev => {
            const next = new Set(prev);
            next.delete(value);
            return next;
        });
    }, []);

    const toggle = useCallback((value: string) => {
        setStoredSet(prev => {
            const next = new Set(prev);
            if (next.has(value)) {
                next.delete(value);
            } else {
                next.add(value);
            }
            return next;
        });
    }, []);

    const clear = useCallback(() => {
        setStoredSet(new Set());
    }, []);

    return {
        value: storedSet,
        setValue: setStoredSet,
        add,
        remove,
        toggle,
        clear
    };
}
