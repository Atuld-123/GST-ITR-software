const nextConfig = {
  output: "standalone",
  async rewrites() {
    const configuredApiOrigin = process.env.TAXSPHERE_API_INTERNAL_URL || "http://127.0.0.1:8000";
    const apiOrigin = configuredApiOrigin.includes("://") ? configuredApiOrigin : `https://${configuredApiOrigin}`;
    return [{ source: "/api/:path*", destination: `${apiOrigin}/api/:path*` }];
  },
};

export default nextConfig;
