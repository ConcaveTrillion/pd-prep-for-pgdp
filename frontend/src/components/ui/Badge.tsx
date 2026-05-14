/**
 * Badge — lightweight status indicator (M5 hi-fi adoption).
 *
 * No Radix primitive underlies this one — a badge is purely presentational.
 * The component encodes the status → colour map from the M5 hi-fi design file
 * so callers never scatter Tailwind colour classes for status semantics.
 *
 * Usage:
 *   <Badge status="running" />       → "Running" with blue dot
 *   <Badge status="complete" />      → "Done" with emerald dot
 *   <Badge status="error" />         → "Errored" with red dot
 *   <Badge status="queued" />        → "Queued" with slate dot
 *   <Badge status="awaiting_review" /> → "Review" with amber dot
 *
 * `children` overrides the default label when provided.
 */
import type { ReactNode } from "react";

export type BadgeStatus =
  | "running"
  | "complete"
  | "queued"
  | "scheduled"
  | "error"
  | "cancelled"
  | "awaiting_review";

interface StatusMeta {
  label: string;
  /** ring + text + background classes */
  cls: string;
  /** dot background class */
  dot: string;
}

const STATUS_META: Record<BadgeStatus, StatusMeta> = {
  running: {
    label: "Running",
    cls: "bg-blue-50 text-blue-700 ring-blue-600/20",
    dot: "bg-blue-500",
  },
  complete: {
    label: "Done",
    cls: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
    dot: "bg-emerald-500",
  },
  queued: {
    label: "Queued",
    cls: "bg-slate-50 text-slate-600 ring-slate-500/20",
    dot: "bg-slate-400",
  },
  scheduled: {
    label: "Scheduled",
    cls: "bg-amber-50 text-amber-700 ring-amber-600/20",
    dot: "bg-amber-400",
  },
  error: {
    label: "Errored",
    cls: "bg-red-50 text-red-700 ring-red-600/20",
    dot: "bg-red-500",
  },
  cancelled: {
    label: "Cancelled",
    cls: "bg-slate-100 text-slate-500 ring-slate-400/20",
    dot: "bg-slate-400",
  },
  awaiting_review: {
    label: "Review",
    cls: "bg-amber-50 text-amber-800 ring-amber-600/20",
    dot: "bg-amber-500",
  },
};

export interface BadgeProps {
  status: BadgeStatus;
  children?: ReactNode;
  className?: string;
}

export function Badge({ status, children, className = "" }: BadgeProps) {
  const meta = STATUS_META[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${meta.cls} ${className}`}
    >
      <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${meta.dot}`} />
      {children ?? meta.label}
    </span>
  );
}
