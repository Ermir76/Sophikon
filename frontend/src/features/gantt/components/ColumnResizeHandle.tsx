import { useRef, useCallback } from "react";

interface ColumnResizeHandleProps {
  columnId: string;
  currentWidth: number;
  minWidth: number;
  onResize: (id: string, width: number) => void;
}

export function ColumnResizeHandle({ columnId, currentWidth, minWidth, onResize }: ColumnResizeHandleProps) {
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      startXRef.current = e.clientX;
      startWidthRef.current = currentWidth;

      const handleMouseMove = (e: MouseEvent) => {
        const newWidth = Math.max(minWidth, startWidthRef.current + (e.clientX - startXRef.current));
        onResize(columnId, Math.round(newWidth));
      };

      const handleMouseUp = () => {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };

      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    },
    [columnId, currentWidth, minWidth, onResize],
  );

  return (
    <div
      className="absolute right-0 top-0 h-full w-1 cursor-col-resize opacity-0 hover:opacity-100 hover:bg-primary/50 active:bg-primary active:opacity-100"
      onMouseDown={handleMouseDown}
    />
  );
}
