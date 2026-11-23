import { describe, it, expect } from 'vitest'
import { dataCollection } from '@/sentry.data-collection'

// Sentry v11 defaults these options to true, so keep everything pinned here to avoid leaking PII.

// Sentry matches deny keys as case-insensitive substrings, so test with actual header/param
// names rather than asserting against the raw deny array directly.
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

  // x-amzn-oidc-data holds ALB user claims (including email). Sentry's built-in filter
  // catches -identity and -accesstoken automatically, but misses -data.
  it.each([
    ['x-amzn-oidc-data', true],
    ['x-amzn-oidc-identity', true],
    ['x-forwarded-for', true],
    ['x-real-ip', true],
    ['remote-addr', true],
    ['via', true],
    ['x-user-email', true],
    // Non-PII debugging headers we still want in Sentry
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

  // Catch any removed keys before they silently fall back to Sentry v11 defaults.
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
