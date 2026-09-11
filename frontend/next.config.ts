import type { NextConfig } from 'next';
const isStaticExport = process.env.STATIC_EXPORT === '1';
const config: NextConfig = {
  outputFileTracingRoot: process.cwd(),
  distDir: process.env.NODE_ENV === 'development' ? '.next-dev' : '.next',
  poweredByHeader: false,
  devIndicators: false,
  ...(isStaticExport ? { output: 'export' as const, trailingSlash: true } : {}),
  ...(!isStaticExport ? { async rewrites() {
    return [{ source: '/api/:path*', destination: `${process.env.API_ORIGIN || 'http://127.0.0.1:8000'}/api/:path*` }];
  }} : {}),
};
export default config;
