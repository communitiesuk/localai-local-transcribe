import { describe, it, expect } from 'vitest'
import { dataCollection } from '@/sentry.data-collection'

// These assertions exist because every value below is a statement about what leaves the service.
// Sentry v11 defaults all of them to collecting, so a key quietly dropped from the baseline is not
// a config tidy-up - it starts sending transcript-adjacent PII. Loosening anything here should mean
// deliberately editing this test too.

// Mirrors sentry.data-collection.ts: the v10-equivalent deny list from Sentry's migration guide,
// plus the ALB's x-amzn-oidc-* identity headers.
const SENSITIVE_FIELDS = [
  'forwarded',
  '-ip',
  'remote-',
  'via',
  '-user',
  'x-amzn-oidc',
]

describe('Sentry dataCollection baseline', () => {
  it('does not collect user info, cookies or database query data', () => {
    expect(dataCollection.userInfo).toBe(false)
    expect(dataCollection.cookies).toBe(false)
    expect(dataCollection.databaseQueryData).toBe(false)
    expect(dataCollection.queues).toBe(false)
  })

  it('collects no HTTP bodies at all', () => {
    expect(dataCollection.httpBodies).toEqual([])
  })

  it('denies PII-bearing headers in both directions', () => {
    expect(dataCollection.httpHeaders.request.deny).toEqual(SENSITIVE_FIELDS)
    expect(dataCollection.httpHeaders.response.deny).toEqual(SENSITIVE_FIELDS)
  })

  it('denies PII-bearing URL query params', () => {
    expect(dataCollection.urlQueryParams.deny).toEqual(SENSITIVE_FIELDS)
  })

  it('records no GenAI or MCP inputs and outputs', () => {
    expect(dataCollection.genAI).toEqual({ inputs: false, outputs: false })
    expect(dataCollection.mcp).toEqual({ inputs: false, outputs: false })
  })

  it('attaches no GraphQL documents or variables', () => {
    expect(dataCollection.graphQL).toEqual({
      document: false,
      variables: false,
    })
  })

  it('captures no local variable values from stack frames', () => {
    expect(dataCollection.stackFrameVariables).toBe(false)
  })

  it('keeps the v10 stack trace context width', () => {
    expect(dataCollection.frameContextLines).toBe(7)
  })

  // Guards the failure mode the comment in sentry.data-collection.ts warns about: a key removed
  // from the object silently inherits the permissive v11 default, and nothing else would catch it.
  it('pins every option Sentry would otherwise default to collecting', () => {
    expect(Object.keys(dataCollection).sort()).toEqual([
      'cookies',
      'databaseQueryData',
      'frameContextLines',
      'genAI',
      'graphQL',
      'httpBodies',
      'httpHeaders',
      'mcp',
      'queues',
      'stackFrameVariables',
      'urlQueryParams',
      'userInfo',
    ])
  })
})
