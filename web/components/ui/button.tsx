import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius)] font-medium text-label-md transition-[color,background-color,opacity] duration-300 disabled:pointer-events-none disabled:opacity-50 select-none",
  {
    variants: {
      variant: {
        primary: "bg-accent text-on-accent hover:bg-[#1e40af] dark:hover:bg-[#2563eb]",
        secondary: "bg-surface text-text border border-border hover:bg-surface-2",
        ghost: "bg-transparent text-muted hover:text-text hover:bg-surface-2",
      },
      size: {
        md: "h-10 px-4",
        lg: "h-11 px-6",
        sm: "h-9 px-3",
        icon: "h-8 w-8 rounded-[var(--radius-sm)]",
      },
    },
    defaultVariants: { variant: "secondary", size: "md" },
  },
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, type = "button", ...props }: ButtonProps) {
  return (
    <button type={type} className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}
