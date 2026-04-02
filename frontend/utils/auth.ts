import { AlbJwtVerifier } from 'aws-jwt-verify'

export type UserAuthorisationResult = {
  email: string
  isAuthorised: boolean
  authReason: string
}

const verifier =
  process.env.ENVIRONMENT !== 'local'
    ? AlbJwtVerifier.create({
        albArn: process.env.ALB_ARN!,
        issuer: process.env.OIDC_ISSUER!,
      })
    : null

export async function parseAuthToken(
  token: string
): Promise<UserAuthorisationResult | null> {
  if (!token) {
    console.error('No auth token provided to parse')
    return null
  }

  try {
    const payload = await verifier!.verify(token, {
      clientId: process.env.OIDC_CLIENT_ID!,
    })

    const email = payload.email as string | undefined
    if (!email) {
      console.error('No email found in JWT payload')
      return null
    }

    return { email, isAuthorised: true, authReason: 'OIDC' }
  } catch (error) {
    console.error('Error verifying auth token:', error)
    return null
  }
}
