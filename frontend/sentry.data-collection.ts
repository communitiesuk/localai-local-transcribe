// Sentry v11 replaced the v10 `sendDefaultPii` option with the more granular `dataCollection`,
// and made its defaults *more permissive*: leaving it unset starts collecting user IP addresses,
// request/response bodies, cookies, database query data and GenAI inputs/outputs.
//
// This service handles meeting recordings and transcripts, so we pin the baseline explicitly to
// Sentry's documented v10-equivalent posture rather than inheriting the v11 defaults. Widening
// anything here changes what leaves the service, so it needs a deliberate decision.
// https://github.com/getsentry/sentry-javascript/blob/develop/MIGRATION.md#senddefaultpii-is-replaced-by-datacollection

import type * as Sentry from '@sentry/nextjs'

// Sentry's default denylist for header/query-param values that commonly carry PII.
const SENTRY_DEFAULT_SENSITIVE_FIELDS = [
  'forwarded',
  '-ip',
  'remote-',
  'via',
  '-user',
]

// The ALB's identity headers (x-amzn-oidc-data, x-amzn-oidc-identity) carry user claims.

const SENSITIVE_FIELDS = [...SENTRY_DEFAULT_SENSITIVE_FIELDS, 'x-amzn-oidc']

// Derived from `init`'s own signature rather than imported: the `DataCollection` type is exported
// from `@sentry/core`, which we only have transitively. Type-only import, so nothing is added to
// the bundle.
type DataCollection = NonNullable<
  NonNullable<Parameters<typeof Sentry.init>[0]>['dataCollection']
>

// `satisfies`, not a plain object: passing this to `Sentry.init()` as a variable means TypeScript
// does no excess property check at the call site, so without this a key misspelled here - or
// renamed by a future Sentry version - would compile clean, be ignored at runtime, and silently
// inherit the permissive v11 default. The unit tests cannot catch that either, since they pin the
// same hand-written key names. `satisfies` rather than an annotation so the literal types survive
// for those tests.
export const dataCollection = {
  userInfo: false,
  cookies: false,
  httpHeaders: {
    request: { deny: SENSITIVE_FIELDS },
    response: { deny: SENSITIVE_FIELDS },
  },
  httpBodies: [],
  urlQueryParams: { deny: SENSITIVE_FIELDS },
  genAI: { inputs: false, outputs: false },

  // MCP content is gated by this, not by `genAI`, even though it lands on `gen_ai.*` attributes.
  // Unset it falls back to the `genAI` values above, so this is already closed - pinned anyway so
  // the fallback stops being load-bearing if Sentry changes it.
  mcp: { inputs: false, outputs: false },

  databaseQueryData: false,
  queues: false,
  graphQL: { document: false, variables: false },

  // Inert today: `localVariablesIntegration()` is a default integration, but its `setup()` returns
  // early unless `includeLocalVariables` is set, and we do not set it. Pinned so that turning
  // `includeLocalVariables` on to debug something cannot also start shipping local variable values
  // - which here would mean transcript fragments held in locals - as a side effect.
  stackFrameVariables: false,

  // v11 lowered the default from 7 to 5; keep the wider stack trace context we had on v10.
  frameContextLines: 7,
} satisfies Required<DataCollection>
