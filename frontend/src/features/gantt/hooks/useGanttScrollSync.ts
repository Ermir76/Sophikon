import { useRef, useCallback } from "react";

export function useGanttScrollSync() {
    const tableScrollRef = useRef<HTMLDivElement>(null);
    const chartBodyRef = useRef<HTMLDivElement>(null);
    const timelineHeaderRef = useRef<HTMLDivElement>(null);
    const topScrollRef = useRef<HTMLDivElement>(null);
    const isSyncing = useRef(false);

    // Sync: chart body scroll → table scrollTop + header scrollLeft
    const handleChartBodyScroll = useCallback(() => {
        if (isSyncing.current) return;
        isSyncing.current = true;

        const cb = chartBodyRef.current;
        if (cb) {
            if (tableScrollRef.current) {
                tableScrollRef.current.scrollTop = cb.scrollTop;
            }
            if (timelineHeaderRef.current) {
                timelineHeaderRef.current.scrollLeft = cb.scrollLeft;
            }
            if (topScrollRef.current) {
                topScrollRef.current.scrollLeft = cb.scrollLeft;
            }
        }

        requestAnimationFrame(() => {
            isSyncing.current = false;
        });
    }, []);

    // Sync: table scroll → chart body scrollTop
    const handleTableScroll = useCallback(() => {
        if (isSyncing.current) return;
        isSyncing.current = true;

        if (tableScrollRef.current && chartBodyRef.current) {
            chartBodyRef.current.scrollTop = tableScrollRef.current.scrollTop;
        }

        requestAnimationFrame(() => {
            isSyncing.current = false;
        });
    }, []);

    const handleTopScroll = useCallback(() => {
        if (isSyncing.current) return;
        isSyncing.current = true;

        if (topScrollRef.current && chartBodyRef.current) {
            chartBodyRef.current.scrollLeft = topScrollRef.current.scrollLeft;
            if (timelineHeaderRef.current) {
                timelineHeaderRef.current.scrollLeft = topScrollRef.current.scrollLeft;
            }
        }

        requestAnimationFrame(() => {
            isSyncing.current = false;
        });
    }, []);

    return {
        tableScrollRef,
        chartBodyRef,
        timelineHeaderRef,
        topScrollRef,
        handleChartBodyScroll,
        handleTableScroll,
        handleTopScroll,
    };
}
