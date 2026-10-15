"use client";

// Tarix va Kutubxona uchun umumiy roʻyxat. `mode` faqat manba va matnlarni almashtiradi.

import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";
import { History, Library } from "lucide-react";
import {
  type Page,
  type SavedPrompt,
  listHistory,
  listLibrary,
  removePrompt,
  setSaved,
} from "@/lib/pages-api";
import { useUser } from "@/lib/auth";
import { PromptCard } from "@/components/pages/prompt-card";
import {
  EmptyState,
  ErrorState,
  ListSkeleton,
  Pagination,
  SignInState,
} from "@/components/pages/states";
import { useLoad } from "@/components/pages/use-list";

const LIMIT = 20;

export type ListMode = "history" | "library";

export function PromptList({ mode }: { mode: ListMode }) {
  const t = useTranslations("pages.common");
  const tm = useTranslations(`pages.${mode}`);
  const user = useUser();
  const [page, setPage] = useState(1);

  const enabled = Boolean(user);
  const loader = useCallback((): Promise<Page<SavedPrompt> | null> => {
    if (!enabled) return Promise.resolve(null);
    return mode === "history"
      ? listHistory(page, LIMIT)
      : listLibrary(page, LIMIT);
  }, [enabled, mode, page]);

  const { loading, data, error, reload, setData } = useLoad(loader);

  const patch = useCallback(
    (id: string, next: SavedPrompt | null) => {
      setData((prev) => {
        if (!prev) return prev;
        // Kutubxonada saqlanmagan element roʻyxatda qolmaydi; oʻchirilgani ham olib tashlanadi
        const drop =
          next === null || (mode === "library" && next.is_saved === false);
        if (drop) {
          return {
            ...prev,
            items: prev.items.filter((i) => i.id !== id),
            total: Math.max(0, prev.total - 1),
          };
        }
        return {
          ...prev,
          items: prev.items.map((i) => (i.id === id ? next : i)),
        };
      });
    },
    [mode, setData],
  );

  const onToggleSave = useCallback(
    async (item: SavedPrompt) => {
      const updated = await setSaved(item.id, !item.is_saved);
      patch(item.id, updated);
    },
    [patch],
  );

  const onDelete = useCallback(
    async (item: SavedPrompt) => {
      await removePrompt(item.id);
      patch(item.id, null);
    },
    [patch],
  );

  const body = () => {
    if (user === undefined) return <ListSkeleton />;
    if (user === null) return <SignInState next={`/${mode}`} />;
    if (error)
      return error.status === 401 ? (
        <SignInState next={`/${mode}`} />
      ) : (
        <ErrorState message={error.message} onRetry={reload} />
      );
    if (loading || !data) return <ListSkeleton />;
    if (!data.items.length)
      return (
        <div className="flex flex-col gap-4">
          <EmptyState
            icon={
              mode === "history" ? (
                <History size={26} aria-hidden />
              ) : (
                <Library size={26} aria-hidden />
              )
            }
            title={tm("emptyTitle")}
            body={tm("emptyBody")}
          />
          {/* Oxirgi sahifadagi element oʻchirilsa — orqaga qaytish uchun */}
          {page > 1 && (
            <Pagination
              page={page}
              limit={data.limit || LIMIT}
              total={data.total}
              onPage={setPage}
            />
          )}
        </div>
      );
    return (
      <div className="flex flex-col gap-4">
        <ul className="flex list-none flex-col gap-3 p-0">
          {data.items.map((item) => (
            <PromptCard
              key={item.id}
              item={item}
              mode={mode}
              onToggleSave={onToggleSave}
              onDelete={onDelete}
            />
          ))}
        </ul>
        <Pagination
          page={data.page || page}
          limit={data.limit || LIMIT}
          total={data.total}
          onPage={setPage}
        />
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-8 md:px-8">
      <div className="mx-auto flex w-full max-w-[880px] flex-col gap-6">
        <header className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <div className="flex flex-col gap-1">
            <h1 className="text-headline-md font-extrabold tracking-tight text-text">
              {tm("title")}
            </h1>
            <p className="text-body-md text-muted">{tm("subtitle")}</p>
          </div>
          {data && data.total > 0 && (
            <span className="font-mono text-code-sm text-subtle">
              {t("count", { total: data.total })}
            </span>
          )}
        </header>
        {body()}
      </div>
    </div>
  );
}
