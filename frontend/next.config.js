import { withSentryConfig } from '@sentry/nextjs'

const isDev = process.env.NODE_ENV === 'development'
const isLocal = process.env.NEXT_PUBLIC_ENVIRONMENT === 'local'

const reportUri = process.env.SENTRY_SECURITY_REPORT_URI
const reportOrigin = reportUri ? new URL(reportUri).origin : ''
const reportGroup = 'csp-endpoint'

const cspHeader = `
    default-src 'self';
    script-src 'self' 'unsafe-inline'${isDev ? " 'unsafe-eval'" : ''};
    style-src 'self' 'unsafe-inline';
    img-src 'self' blob: data:;
    font-src 'self';
    object-src 'none';
    base-uri 'self';
    form-action 'self';
    frame-ancestors 'none';
    ${isLocal ? '' : 'upgrade-insecure-requests;'}
    connect-src 'self' ${reportOrigin};
    ${reportUri ? `report-uri ${reportUri}; report-to ${reportGroup};` : ''}
`

const headers = [
  {
    key: 'Content-Security-Policy-Report-Only',
    value: cspHeader.replace(/\n/g, ''),
  },
]

if (reportUri) {
  headers.push({
    key: 'Reporting-Endpoints',
    value: `${reportGroup}="${reportUri}"`,
  })
}

let nextConfig = {
  output: 'standalone',
  async headers() {
    return [
      {
        // By default: cache nothing in shared caches (e.g. CloudFront) and require (etag) revalidation
        // The exception is static assets, which can be cached more aggressively (Next defaults to `public,
        // max-age=31536000, immutable`)
        source: '/:path((?!_next/static/).*)',
        headers: [{ key: 'Cache-Control', value: 'private, no-cache' }],
      },
      {
        source: '/(.*)',
        headers: headers,
      },
    ]
  },
  sassOptions: {
    includePaths: ['./node_modules'],
    quietDeps: true,
  },
}

const sentryConfig = {
  // For all available options, see:
  // https://github.com/getsentry/sentry-webpack-plugin#options
  webpack: {
    treeShaking: {
      removeDebugLogging: true,
    },
  },
  org: 'communitiesuk',
  project: 'localai-local-transcribe',

  // Only print logs for uploading source maps in CI
  silent: !process.env.CI,

  // For all available options, see:
  // https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/

  // Upload a larger set of source maps for prettier stack traces (increases build time)
  widenClientFileUpload: true,

  // Automatically annotate React components to show their full name in breadcrumbs and session replay
  reactComponentAnnotation: {
    enabled: true,
  },

  // Route browser requests to Sentry through a Next.js rewrite to circumvent ad-blockers.
  tunnelRoute: '/monitoring',

  // Hides source maps from generated client bundles
  hideSourceMaps: true,

  // Physically deletes source maps from build output after upload completes
  sourcemaps: {
    deleteSourcemapsAfterUpload: true,
  },

  // Automatically tree-shake Sentry logger statements to reduce bundle size
  disableLogger: true,

  // Enables automatic instrumentation of Vercel Cron Monitors.
  automaticVercelMonitors: true,
}
nextConfig = withSentryConfig(nextConfig, sentryConfig)

export default nextConfig
