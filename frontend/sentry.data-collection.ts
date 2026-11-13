// Sentry v11 replaced the v10 `sendDefaultPii` option with the more granular `dataCollection`,
// and made its defaults *more permissive*: leaving it unset starts collecting user IP addresses,
// request/response bodies, cookies, database query data and GenAI inputs/outputs.
//
// This service handles meeting recordings and transcripts, so we pin the baseline explicitly to
// Sentry's documented v10-equivalent posture rather than inheriting the v11 defaults. Widening
// anything here changes what leaves the service, so it needs a deliberate decision.
// https://github.com/getsentry/sentry-javascript/blob/develop/MIGRATION.md#senddefaultpii-is-replaced-by-datacollection

// Sentry's default denylist for header/query-param values that commonly carry PII.
const SENSITIVE_FIELDS = ['forwarded', '-ip', 'remote-', 'via', '-user']

// Not annotated with Sentry's `DataCollection` type: it is exported from `@sentry/core`, which we
// only have transitively. `Sentry.init()` checks this object against that type at each call site.
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
  databaseQueryData: false,
  queues: false,
  graphQL: { document: false, variables: false },

  // v11 lowered the default from 7 to 5; keep the wider stack trace context we had on v10.
  frameContextLines: 7,
}
