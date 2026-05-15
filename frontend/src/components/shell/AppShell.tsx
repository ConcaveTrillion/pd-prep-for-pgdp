import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface AppShellProps {
  header: ReactNode;
  footer: ReactNode;
  children: ReactNode;
  className?: string;
  "data-testid"?: string;
}

export function AppShell({
  header,
  footer,
  children,
  className,
  "data-testid": testId,
}: AppShellProps) {
  return (
    <div
      data-testid={testId ?? "app-shell"}
      className={cn("grid min-h-screen", className)}
      style={{
        gridTemplateRows: "56px 1fr 32px",
        gridTemplateAreas: '"header" "main" "footer"',
      }}
    >
      <header style={{ gridArea: "header" }}>{header}</header>
      <main style={{ gridArea: "main" }} className="overflow-auto">
        {children}
      </main>
      <footer style={{ gridArea: "footer" }}>{footer}</footer>
    </div>
  );
}
