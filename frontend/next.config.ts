import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return {
      // Proxy all /api/* calls to the backend EXCEPT /api/auth/* (handled by NextAuth)
      // and /api/register (handled locally).
      beforeFiles: [],
      afterFiles: [
        {
          source: "/api/:path((?!auth/|register(?:/|$)).*)",
          destination: `${process.env.BACKEND_URL ?? "http://backend:8000"}/:path*`,
        },
      ],
      fallback: [],
    };
  },
};

export default nextConfig;
