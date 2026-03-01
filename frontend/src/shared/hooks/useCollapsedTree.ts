import { useMemo, useLayoutEffect, useRef } from "react";
import { useLocalStorageSet } from "@/shared/hooks/useLocalStorageSet";

/**
 * Manages collapsed node state for any tree structure with localStorage persistence.
 *
 * Handles a key edge case: when a node's parent changes (e.g. indent/outdent),
 * any collapsed ancestors in the new parent chain are automatically expanded
 * so the node stays visible. Uses useLayoutEffect to prevent visual flicker.
 *
 * @param storageKey - localStorage key for persisting collapsed state
 * @param data - flat array of tree nodes
 * @param getParentId - function to extract the parent ID from a node
 */
export function useCollapsedTree<T extends { id: string }>(
    storageKey: string,
    data: T[],
    getParentId: (node: T) => string | undefined | null,
) {
    const { value: collapsedIds, toggle: toggleCollapse, remove: removeCollapsed } = useLocalStorageSet(storageKey);

    // Snapshot of each node's parent so we can detect hierarchy changes.
    const prevParentsRef = useRef<Map<string, string | undefined | null>>(
        new Map(data.map(t => [t.id, getParentId(t)]))
    );

    // When data changes (after indent/outdent/reorder), detect nodes whose
    // parent changed and expand any collapsed ancestors so they stay visible.
    // Runs before paint to prevent flicker.
    useLayoutEffect(() => {
        const dataMap = new Map<string, T>(data.map(t => [t.id, t]));

        for (const node of data) {
            if (!prevParentsRef.current.has(node.id)) continue;

            const prevParent = prevParentsRef.current.get(node.id);
            const currentParent = getParentId(node);

            if (currentParent && currentParent !== prevParent) {
                let ancestor: string | undefined | null = currentParent;
                while (ancestor) {
                    if (collapsedIds.has(ancestor)) {
                        removeCollapsed(ancestor);
                    }
                    const parentNode = dataMap.get(ancestor);
                    ancestor = parentNode ? getParentId(parentNode) : undefined;
                }
            }
        }

        prevParentsRef.current = new Map(data.map(t => [t.id, getParentId(t)]));
    }, [data, collapsedIds, removeCollapsed, getParentId]);

    // Filter out nodes whose ancestors are collapsed.
    const visibleData = useMemo(() => {
        if (collapsedIds.size === 0) return data;

        const dataMap = new Map<string, T>(data.map(t => [t.id, t]));

        return data.filter(node => {
            let current = getParentId(node);
            while (current) {
                if (collapsedIds.has(current)) {
                    return false;
                }
                const parentNode = dataMap.get(current);
                current = parentNode ? getParentId(parentNode) : undefined;
            }
            return true;
        });
    }, [data, collapsedIds, getParentId]);

    return { visibleData, collapsedIds, toggleCollapse };
}
