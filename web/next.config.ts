import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

// Dev'da /api/* soʻrovlari FastAPI'ga yoʻnaltiriladi (prod'da buni Nginx qiladi).
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
  // HSTS Nginx'da (faqat HTTPS orqasida maʼnoli)
];

const nextConfig: NextConfig = {
  // Next dev web/CLAUDE.md va AGENTS.md yaratmasin — loyihaning CLAUDE.md'si ildizda
  agentRules: false,
  // SSE oqimi proxy orqali buferlanmasin (gzip butun javobni kutadi). Prod'da Nginx siqadi.
  compress: false,
  poweredByHeader: false,
  async headers() {
    return [{ source: "/(.*)", headers: SECURITY_HEADERS }];
  },
  async rewrites() {
    // Faqat dev: prod'da /api/ ni Nginx toʻgʻridan-toʻgʻri FastAPI'ga yoʻnaltiradi
    if (process.env.NODE_ENV === "production") return [];
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
};

export default withNextIntl(nextConfig);
