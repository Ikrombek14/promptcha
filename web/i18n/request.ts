import { getRequestConfig } from "next-intl/server";
import { hasLocale } from "next-intl";
import { routing } from "./routing";

// Asosiy matnlar `messages/{locale}.json`; admin panel matnlari alohida `messages/admin/{locale}.json`
// (parallel ish uchun ajratilgan) — bu yerda birlashtiriladi.
export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested)
    ? requested
    : routing.defaultLocale;
  const base = (await import(`../messages/${locale}.json`)).default;
  const admin = (await import(`../messages/admin/${locale}.json`)).default;
  return { locale, messages: { ...base, ...admin } };
});
