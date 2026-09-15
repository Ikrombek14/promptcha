import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

// Next.js 16: middleware.ts → proxy.ts. Faqat locale yoʻnaltirish, boshqa mantiq yoʻq.
export default createMiddleware(routing);

export const config = {
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
