"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/callout";

// Workbench holati localStorage'dan tiklanadi — shuning uchun faqat brauzerda chiziladi
// (SSR bilan hydration farqi boʻlmasin).
const Workbench = dynamic(() => import("@/components/workbench").then((m) => m.Workbench), {
  ssr: false,
  loading: () => (
    <div className="mx-auto max-w-[1312px] px-4 py-8 md:px-8" aria-busy>
      <Skeleton className="mb-8 h-10" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-[720px]" />
        <Skeleton className="h-[720px]" />
      </div>
    </div>
  ),
});

export function WorkbenchLoader() {
  return <Workbench />;
}
