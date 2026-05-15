import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
  "data-testid"?: string;
}

export function PageHeader({
  title,
  description,
  actions,
  className,
  "data-testid": testId,
}: PageHeaderProps) {
  return (
    <div
      data-testid={testId ?? "page-header"}
      className={cn(
        "flex items-start justify-between gap-4 py-4 px-6",
        className,
      )}
    >
      <div className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold text-ink-1">{title}</h1>
        {description && <p className="text-sm text-ink-3">{description}</p>}
      </div>
      {actions && (
        <div className="flex items-center gap-2 shrink-0">{actions}</div>
      )}
    </div>
  );
}
