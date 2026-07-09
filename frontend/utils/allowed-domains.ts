export default function isAllowedDomain(
  email: string,
  allowedDomains: string[]
): boolean {
  const domain = email.split('@')[1]?.toLowerCase()

  if (!domain) {
    return false
  }

  return allowedDomains.some((allowed) => allowed.toLowerCase() === domain)
}
