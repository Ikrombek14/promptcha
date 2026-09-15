import * as React from "react";
import { cn } from "@/lib/utils";

export function Textarea({ className, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "w-full resize-none rounded-[var(--radius)] border border-border bg-surface p-3 text-body-md text-text placeholder:text-muted",
        "focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent",
        "disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-[var(--radius)] border border-border bg-surface px-3 text-body-md text-text placeholder:text-muted",
        "focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent",
        className,
      )}
      {...props}
    />
  );
}
