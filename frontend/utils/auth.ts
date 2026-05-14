import { AlbJwtVerifier } from 'aws-jwt-verify'

export type UserAuthorisationResult = {
  email: string
  isAuthorised: boolean
  authReason: string
}

export type JwtPayloadVerifier = {
  verify: (token: string) => Promise<unknown>
}

export function createAlbJwtVerifier(): JwtPayloadVerifier {
  return AlbJwtVerifier.create({
    albArn: process.env.ALB_ARN!,
    issuer: process.env.OIDC_ISSUER!,
    clientId: process.env.OIDC_CLIENT_ID!,
  })
}

export async function parseAuthToken(
  verifier: JwtPayloadVerifier,
  token: string
): Promise<UserAuthorisationResult | null> {
  if (!token) {
    console.error('No auth token provided to parse')
    return null
  }

  try {
    const payload = (await verifier.verify(token)) as { email?: string }

    if (!payload.email) {
      console.error('No email found in JWT payload')
      return null
    }

    return { email: payload.email, isAuthorised: true, authReason: 'OIDC' }
  } catch (error) {
    console.error('Error verifying auth token:', error)
    return null
  }
}
