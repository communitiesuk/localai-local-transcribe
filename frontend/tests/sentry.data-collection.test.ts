import { describe, it, expect } from 'vitest'
import { dataCollection } from '@/sentry.data-collection'

// Sentry v11 defaults every option below to collecting, so a key dropped from the baseline starts
// sending transcript-adjacent PII rather than just tidying config.

// Sentry matches deny terms as case-insensitive substrings - see shouldFilterDataKey in
// @sentry/core/utils/data-collection/filterKeyValueData.js - so these assert on header and param
// names rather than on the deny list itself, which would only compare the list to a copy of itself.
const isDenied = (name: string, deny: string[]) =>
  deny.some((term) => name.toLowerCase().includes(term.toLowerCase()))

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

  // x-amzn-oidc-data is the ALB's signed JWT of user claims, including email address. Its siblings
  // (-identity, -accesstoken) are also caught by Sentry's always-on SENSITIVE_KEY_SNIPPETS, but
  // -data is not, so the baseline has to deny it itself.
  it.each([
    ['x-amzn-oidc-data', true],
    ['x-amzn-oidc-identity', true],
    ['x-forwarded-for', true],
    ['x-real-ip', true],
    ['remote-addr', true],
    ['via', true],
    ['x-user-email', true],
    // Not PII, and useful for debugging - these must still reach Sentry.
    ['content-type', false],
    ['accept-language', false],
  ])('denies request and response header %s: %s', (header, expected) => {
    expect(isDenied(header, dataCollection.httpHeaders.request.deny)).toBe(
      expected
    )
    expect(isDenied(header, dataCollection.httpHeaders.response.deny)).toBe(
      expected
    )
  })

  it.each([
    ['remote-addr', true],
    ['client-ip', true],
    ['page', false],
  ])('denies URL query param %s: %s', (param, expected) => {
    expect(isDenied(param, dataCollection.urlQueryParams.deny)).toBe(expected)
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
